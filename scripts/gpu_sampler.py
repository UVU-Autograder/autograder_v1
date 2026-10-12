"""GPU and vLLM sampling shared by the load tests (standard library only).

    sampler = Sampler("http://127.0.0.1:8001/metrics")
    before = read_vllm_metrics(sampler.metrics_url)
    sampler.start(); ...run a load level...; sampler.stop()
    row = sampler.summary(before, read_vllm_metrics(sampler.metrics_url), wall_seconds)

Twice a second it reads vLLM's Prometheus /metrics (running / waiting requests,
KV cache use) and ``nvidia-smi`` (utilisation, power, temperature, SM clock,
throttle reasons). Throttle reasons are decoded from nvidia-smi's bitmask so a
row says *why* the clock dropped (power cap, thermal) instead of a hex number.
Either source may be missing (no GPU on a laptop, metrics off); its columns are
then None.
"""

from __future__ import annotations

import shutil
import statistics
import subprocess
import threading
import urllib.error
import urllib.request

NVIDIA_FIELDS = "utilization.gpu,power.draw,temperature.gpu,clocks.sm,clocks_throttle_reasons.active"
# nvidia-smi clocks_throttle_reasons bits; 0x1 (GPU idle) is normal and ignored.
THROTTLE_BITS = {
    0x2: "app_clock_setting",
    0x4: "sw_power_cap",
    0x8: "hw_slowdown",
    0x20: "sw_thermal",
    0x40: "hw_thermal",
    0x80: "hw_power_brake",
}


def read_vllm_metrics(url: str | None) -> dict[str, float]:
    """vllm:* series from /metrics, summed across labels. Empty when unreadable."""
    if not url:
        return {}
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            text = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return {}
    totals: dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("vllm:"):
            name, _, value = line.rpartition(" ")
            key = name.split("{")[0]
            try:
                totals[key] = totals.get(key, 0.0) + float(value)
            except ValueError:
                pass
    return totals


def decode_throttle(mask: int) -> set[str]:
    return {name for bit, name in THROTTLE_BITS.items() if mask & bit}


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))]


class Sampler(threading.Thread):
    """Polls vLLM's /metrics and nvidia-smi twice a second until stop()."""

    def __init__(self, metrics_url: str | None):
        super().__init__(daemon=True)
        self.metrics_url = metrics_url
        self.nvidia_smi = shutil.which("nvidia-smi")
        self.stop_event = threading.Event()
        self.running: list[float] = []
        self.waiting: list[float] = []
        self.kv_cache: list[float] = []
        self.gpu_util: list[float] = []
        self.gpu_power: list[float] = []
        self.gpu_temp: list[float] = []
        self.sm_clock: list[float] = []
        self.throttle: set[str] = set()

    def sample_gpu(self) -> None:
        if not self.nvidia_smi:
            return
        try:
            out = subprocess.run(
                [self.nvidia_smi, f"--query-gpu={NVIDIA_FIELDS}", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3,
            ).stdout.splitlines()[0]
            util, power, temp, clock, mask = (x.strip() for x in out.split(","))
            self.gpu_util.append(float(util))
            self.gpu_power.append(float(power))
            self.gpu_temp.append(float(temp))
            self.sm_clock.append(float(clock))
            self.throttle |= decode_throttle(int(mask, 16))
        except (OSError, ValueError, IndexError, subprocess.SubprocessError):
            pass

    def run(self) -> None:
        while not self.stop_event.is_set():
            sample = read_vllm_metrics(self.metrics_url)
            if sample:
                self.running.append(sample.get("vllm:num_requests_running", 0))
                self.waiting.append(sample.get("vllm:num_requests_waiting", 0))
                kv = sample.get("vllm:kv_cache_usage_perc", sample.get("vllm:gpu_cache_usage_perc"))
                if kv is not None:
                    self.kv_cache.append(kv)
            self.sample_gpu()
            self.stop_event.wait(0.5)

    def stop(self) -> None:
        self.stop_event.set()
        self.join()

    def summary(self, before: dict[str, float], after: dict[str, float], wall: float, requests: int) -> dict:
        """Queue, token and GPU columns for one load level."""

        def delta(name: str) -> float:
            return after.get(name, 0.0) - before.get(name, 0.0)

        return {
            "generated_tokens_per_second": round(delta("vllm:generation_tokens_total") / wall, 1) if after and wall else None,
            "prompt_tokens_per_request": round(delta("vllm:prompt_tokens_total") / requests) if after and requests else None,
            "vllm_max_running": max(self.running, default=None),
            "vllm_max_waiting": max(self.waiting, default=None),
            "vllm_preemptions": round(delta("vllm:num_preemptions_total")) if after else None,
            "kv_cache_max_pct": round(100 * max(self.kv_cache), 1) if self.kv_cache else None,
            "gpu_util_avg": round(statistics.mean(self.gpu_util), 1) if self.gpu_util else None,
            "gpu_util_max": max(self.gpu_util, default=None),
            "gpu_power_max_w": max(self.gpu_power, default=None),
            "gpu_temp_max_c": max(self.gpu_temp, default=None),
            "sm_clock_min_mhz": min(self.sm_clock, default=None),
            "throttle_reasons": sorted(self.throttle),
        }


def _show(value, fmt: str = "{}") -> str:
    return "-" if value is None else fmt.format(value)


QUEUE_GPU_HEADER = f"{'gen tok/s':>9} {'run/wait':>9} {'preempt':>7} {'KV %':>5} {'GPU avg/max %':>13} {'W max':>6} {'°C':>4} {'MHz min':>7}  throttle"


def queue_gpu_cells(row: dict) -> str:
    """The shared right-hand columns of a load-test row (see QUEUE_GPU_HEADER)."""
    run_wait = (f"{_show(row['vllm_max_running'], '{:.0f}')}/{_show(row['vllm_max_waiting'], '{:.0f}')}"
                if row["vllm_max_running"] is not None else "-")
    gpu = (f"{_show(row['gpu_util_avg'])}/{_show(row['gpu_util_max'], '{:.0f}')}"
           if row["gpu_util_avg"] is not None else "-")
    return (f"{_show(row['generated_tokens_per_second']):>9} {run_wait:>9} {_show(row['vllm_preemptions']):>7} "
            f"{_show(row['kv_cache_max_pct']):>5} {gpu:>13} {_show(row['gpu_power_max_w'], '{:.0f}'):>6} "
            f"{_show(row['gpu_temp_max_c'], '{:.0f}'):>4} {_show(row['sm_clock_min_mhz'], '{:.0f}'):>7}  "
            f"{','.join(row['throttle_reasons']) or '-'}")
