# Orchard state-copy memory scope

## Question and answer

Does a finite limit on the helper's own cgroup establish the memory headroom available to a state copy?

No. Every enforcing ancestor can constrain the allocation. A step-local group can have the same limit as an ancestor but much lower usage. Sampling that child alone misses shared pressure and overstates headroom. A full-copy claim also needs authenticated evidence that the watched group contains the trainer.

## Evidence

Allocation 169097's small-copy manifest records two finite limits:

| Scope | Limit, B | Usage, B | Headroom, B |
|---|---:|---:|---:|
| Selected `.../s8FXM7AR3HQC00/step_5/user` | 858,993,459,200 | 18,747,392 | 858,974,711,808 |
| Enforcing ancestor `.../s8FXM7AR3HQC00` | 858,993,459,200 | 767,968,198,656 | 91,025,260,544 |

The ancestor's **89.403%** usage exceeds the copier's **85%** threshold. The 16 five-second samples cover only the step-local group. The manifest reports allocation identity `UNAVAILABLE`; it does not authenticate trainer membership. The selected child's headroom is therefore not conservative across the ancestry.

The authorized counter snapshot at 00:30:14Z reads only the named ancestor, its immediate children and the specified memory files. It records **716.934 / 800 GiB** used, **668.312 GiB** of file memory, **667.699 GiB** of inactive file memory and **27.914 GiB** of anonymous memory. Dirty and writeback bytes are zero. The ancestor has `high=0`, `max=1714`, `oom=0` and `oom_kill=0`; all pressure averages are 0.00. The `max` counter is cumulative and does not date its events.

`anon + slab_unreclaimable` is **3.4898%** of the job limit. The broader proxy `anon + shmem + max(0, kernel - slab_reclaimable)` is **3.5110%**. Kernel already includes slab; adding both would double-count it. Shmem is part of file memory and must also be counted only once. These proxies do not guarantee immediate reclaimability.

The counter snapshot does not repair the copy's sampling scope. The final acceptance record has nine true checks and three false: allocation memory, trainer membership and unchanged step timing. The small archive is server-confirmed but **NOT_A_RESUMABLE_SLOT**.

## Durable evidence

`ORCHARD_STATE_COPY_MEMORY_169097_EVIDENCE_20261114T010734Z.tar.gz` in this directory contains fourteen credential-free members. It is **18,520 B**, SHA-256 **4dfd43e40893cf25d8c0bfda6b0f0d3d77bb46644c71bdd989eb47d5aee63498**. Its manifest pins every member.

Key records:
