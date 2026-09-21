# Kata Containers Optimization Guide for Dev Machine

This guide provides strategies to optimize the Kata Containers isolation layer used by Judge0 on the Dell workstation to ensure low-latency grading and system stability.

## 1. Hypervisor Selection
**Stay on QEMU.** Kata's Docker integration is only tested against QEMU; Firecracker and
Cloud Hypervisor are documented for the CRI/Kubernetes path. There is a live upstream issue
for the Firecracker + Docker/`ctr` combination failing on rootfs mount, and this stack already
sits on two less-travelled paths (standalone Docker + `runtime-rs`).

Firecracker/Cloud-Hypervisor microVMs do boot faster and use less memory, which matters for
short-lived grading jobs — revisit once the QEMU path has run a full semester's load, and test
in isolation before switching the execution target.

## 1a. Config file location (read this first)

`runtime-rs` loads **`/etc/kata-containers/runtime-rs/configuration.toml`**, not
`/etc/kata-containers/configuration.toml` (that is the deprecated Go runtime's path). Anything
written to the wrong path is silently ignored — every tuning item below depends on getting
this right. Seed it from the shipped default and confirm:

```bash
sudo mkdir -p /etc/kata-containers/runtime-rs
sudo cp /opt/kata/share/defaults/kata-containers/runtime-rs/configuration-qemu-runtime-rs.toml \
  /etc/kata-containers/runtime-rs/configuration.toml
docker run --rm --runtime kata-runtime busybox true
sudo journalctl -u containerd --since "2 minutes ago" --no-pager | grep "load configuration from"
```

The last command must print your `/etc/...` path. If it prints `/opt/kata/share/defaults/...`,
nothing below will take effect.

### vCPU and memory

Kata defaults to `default_vcpus = 1` / `default_memory = 2048`, which makes Judge0's Rails boot
take ~33s. Set 2 vCPUs (matches `JUDGE0_MAX_CONCURRENT=2` on a 20-core host):

```bash
sudo sed -i 's/^default_vcpus = .*/default_vcpus = 2/' \
  /etc/kata-containers/runtime-rs/configuration.toml
docker run --rm --runtime kata-runtime busybox nproc   # must print 2
```

Leave `default_memory = 2048` until measured — observed usage is ~7MB for trivial code and
~35MB with pytest/Pillow/pygame imported, well under the 256MB per-submission cap.

## 2. Host-Level Tuning
### Memory Management
- **Hugepages**: Enable Hugepages on the host OS to reduce page table overhead.
  - Check status: `grep Huge /proc/meminfo`
  - Configure in `/etc/sysctl.conf`: `vm.nr_hugepages = [value]`
- **Swapiness**: Reduce `vm.swappiness` (e.g., to 10) to prevent the host from swapping out active VM memory to disk, which would cause massive latency spikes in grading.

### CPU Optimization
- **CPU Pinning**: The Dell Pro Max Tower T2 provides 20 cores (Intel Core Ultra 7 265, 40 threads). Use `cpuset` to pin cores for Kata VMs if needed, preventing them from competing with the FastAPI/Celery orchestration layer.

### Privileged Container Passthrough (do NOT use `--privileged`)

Judge0 upstream ships `privileged: true` to run its internal `isolate` sandbox. **Under Kata,
that fails outright**: Kata enumerates every host `/dev` entry to hot-plug into the guest and
dies with `get host path failed / No such file or directory (os error 2)` (a workstation with
NVMe plus ~20 snap loop devices reliably trips this).

`privileged_without_host_devices = true` does **not** fix this on standalone Docker. It is a
containerd-CRI / CRI-O runtime option, not a field in Kata's config schema — verified on this
host by dumping the parsed `Runtime` struct from the shim, which has no such field. Written to
`configuration.toml` it is silently discarded. There is no equivalent for standalone Docker
Engine; enforcing it would require a CRI control plane (containerd CRI plugin or k3s).

**What actually works** — `docker-compose.kata.yml` sets `privileged: false` plus a bounded
capability set:

```yaml
privileged: false
cap_add: [SYS_ADMIN, SYS_RESOURCE, SYS_CHROOT, SETUID, SETGID,
          DAC_OVERRIDE, MKNOD, CHOWN, FOWNER, KILL]
```

Verified end to end: submissions return `Accepted` on both language 71 and custom 711, with
pytest/Pillow/pygame imports working. This is strictly better than privileged — no host device
enumeration, bounded capabilities, and the VM boundary intact.

## 3. Guest OS & Image Optimization
- **Minimal Rootfs**: Use a stripped-down guest image (e.g., based on Alpine or a custom minimal Linux) to keep the base memory footprint below 128MB.
- **Pre-baked Runtimes**: Ensure all Python versions and dependencies are pre-installed in the image. Any runtime installation during grading will violate the performance targets.

## 4. Resource Guardrails
- **Execution Slot Cap**: Strictly adhere to the cap of `2-4` concurrent jobs. 
- **Memory Limit**: Ensure Judge0 is configured with a hard limit of `256MB` per container to prevent a single malicious or buggy student submission from crashing the host via OOM (Out of Memory).

## 5. Monitoring & Validation
Use these tools to verify optimization:
- `htop`: Monitor for CPU spikes and RAM exhaustion during batch runs.
- `docker stats`: Verify that containers are staying within their memory limits.
- `ps aux | grep qemu-system`: inspect the Kata VMM processes directly. (`virt-top` does **not**
  apply here — it reads libvirt, and this stack runs QEMU straight through containerd/Kata with
  no libvirt layer.)

## 6. Cleanup Verification
The zero-retention contract requires immediate deletion:
- Ensure `DELETE /submissions/{token}` is called immediately after result retrieval.
- Periodically check for "zombie" VMs that may have failed to terminate using `ps aux | grep qemu-system`.
