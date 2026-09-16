# Kata Containers Optimization Guide for Dev Machine

This guide provides strategies to optimize the Kata Containers isolation layer used by Judge0 on the Dell workstation to ensure low-latency grading and system stability.

## 1. Hypervisor Selection
For a grading workload characterized by short-lived, high-frequency executions, avoid standard QEMU.
- **Recommended**: `Firecracker` or `Cloud-Hypervisor`.
- **Benefit**: These are "microVM" monitors designed for serverless workloads, offering significantly faster boot times and lower memory overhead than general-purpose hypervisors.

## 2. Host-Level Tuning
### Memory Management
- **Hugepages**: Enable Hugepages on the host OS to reduce page table overhead.
  - Check status: `grep Huge /proc/meminfo`
  - Configure in `/etc/sysctl.conf`: `vm.nr_hugepages = [value]`
- **Swapiness**: Reduce `vm.swappiness` (e.g., to 10) to prevent the host from swapping out active VM memory to disk, which would cause massive latency spikes in grading.

### CPU Optimization
- **CPU Pinning**: The Dell Pro Max Tower T2 provides 20 cores (Intel Core Ultra 7 265, 40 threads). Use `cpuset` to pin cores for Kata VMs if needed, preventing them from competing with the FastAPI/Celery orchestration layer.

### Privileged Container Passthrough
Judge0 requires `privileged: true` to run its internal `isolate` sandbox. In Kata (especially `runtime-rs`), enable:
```toml
# /etc/kata-containers/configuration.toml
privileged_without_host_devices = true
```
This gives Judge0 namespace and cgroup permissions inside the microVM without failing on host `/dev` hardware device mapping.

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
- `virt-top`: If using libvirt, monitor the overhead of the VM monitors themselves.

## 6. Cleanup Verification
The zero-retention contract requires immediate deletion:
- Ensure `DELETE /submissions/{token}` is called immediately after result retrieval.
- Periodically check for "zombie" VMs that may have failed to terminate using `ps aux | grep vmm`.
