# Host Verification and Fault Recovery Validation (Issue #25 Archive)

> [!NOTE]
> **Archive Notice:** This document archives the detailed synthetic drill evidence executed on the production Dell Precision 5860 Tower during GitHub Issue [#25](https://github.com/UVU-Autograder/autograder_v1/issues/25). For active deployment status, consult [`docs/guides/workstation.md`](../guides/workstation.md) and [`docs/releases/v1.0.0-pilot.md`](../releases/v1.0.0-pilot.md).

---

## Verified Host Environment
- **Host Workstation:** Dell Precision 5860 Tower (`CET-D24728`, static IP `10.115.20.200`)
- **OS / Kernel:** Ubuntu 24.04 LTS (`Linux 6.17.0-1032-oem x86_64`)
- **CPU / RAM:** Intel Core Ultra 7 265 (20 cores: 8 P-cores, 12 E-cores), 32GB DDR5 RAM
- **GPU / VRAM:** NVIDIA RTX PRO 4500 Blackwell (32,623 MiB / 32 GB VRAM)
- **Target Commit:** `f3eba87`

---

## 1. Kata microVM Isolation & Boundary Proofs
- **Kernel Separation:** Execution was confirmed running in an independent guest Linux kernel (`6.18.35-202` inside Kata vs. host `6.17.0-1032-oem`), isolated by hardware KVM acceleration (`accel=kvm`).
- **Resource Caps:** MicroVM hypervisor envelopes were verified in `/etc/kata-containers/runtime-rs/configuration.toml` (`default_vcpus = 2`, `default_memory = 2048` MB, `virtio-fs`), with Judge0 per-box `isolate` boundaries strictly capping memory to 256MB, CPU time to 30.0s, wall time to 20.0s, and thread count to 60.
- **MicroVM Process Boundaries:** All 6 `judge0-worker` containers operate under `runtime: kata-runtime`, with dedicated `containerd-shim-kata-v2`, `virtiofsd`, and `qemu-system-x86_64` process isolation per slot.

---

## 2. 200-Submission Batch Capacity & Concurrent Sandbox Execution
- **Batch Processing:** 200 synthetic submissions were processed through the official pipeline via [`validate_dispatch_host.py`](../../backend/scripts/validate_dispatch_host.py) against CS 1400 `m1-lab1` (`completed: 200`, total batch duration: `1454.13s`).
- **Concurrent Sandbox Throughput:** A concurrent sandbox submission was dispatched mid-batch; it completed cleanly in `20.03s` with score 10/10 while the official queue remained fully active.
- **Export Artifacts:** Official grades export (`grades.csv`, 200 rows) and student feedback bundles (`feedback.zip`, 200 items) were compiled in `0.0085s` packaging time and verified with zero dropped jobs.
- **Post-Run Teardown:** Cleaned up via `validate_dispatch_host.py cleanup`, confirming `physical_absence: true` with zero orphaned workspace directories or archive artifacts.

---

## 3. Fault & Interruption Recovery Mid-Batch
- **Celery Worker Crash Recovery:** Restarted `celery-worker` mid-batch; worker reconnected to Redis within 1s and resumed grading the active submission without ticket or slot leakage.
- **Dispatch Worker Restart:** Restarted `dispatch-worker` mid-batch; dispatcher cleanly re-evaluated in-flight tickets, published next tasks, and maintained 5s health sweeps (`healthy: true, publish_failures: 0`).
- **Judge0 Execution Worker Crash Recovery:** Restarted `judge0-worker` during active test execution; the interrupted job was safely trapped, reported as `cleanup_failure`, checkpointed, and the remaining batch proceeded without deadlocks or stalled queues.
- **Slot & Ticket Audit:** Audited `ExecutionTicket` table in PostgreSQL; confirmed zero orphaned tickets or deadlocks across all runs.

---

## 4. Zero-Retention Compliance
- **Submission Deletion:** Verified through [`validate_grading_package_host.py`](../../backend/scripts/validate_grading_package_host.py) and live Celery traces that every completed submission payload is immediately deleted via `DELETE /submissions/[TOKEN]` (subsequent queries return HTTP 404).
- **Cleanup Worker Reconciliation:** Executed [`validate_retention_host.py`](../../backend/scripts/validate_retention_host.py) across simulated 23h review expiry, 24h hard deletion, permission failure quarantine, and recovery. All 14 retention and cleanup assertions passed, leaving zero dangling files or orphaned workspaces.
