# Exact continuation from the LEG-S1 step-544 slot

Status: **build-only; continuation not ready or authorized**. Date: 2026-11-14.

## Question and answer

Can the unchanged production kit resume the original optimizer state at step 545 and retain its 1,000-step schedule?

The local source and metadata proofs say **yes for argument and identity binding**, not for an executed production restore. The native selector chooses `u`, dispatch passes arm `0` and `resume_pin=latest`, and the recipe already ends at 1,000. The installed wrapper, `job.sh` and all 95 kit members stay unchanged.

The actual real-slot CPU equality result, numerical loss baseline, verified early-loss observer/optimization-stop procedure and new execution orders remain missing.

## Evidence and scope

- The sealed local proof has **36 passing CPU tests**, **three syntax checks** and **54 bound files**. Tests exercise the actual native selector and argument functions with tiny synthetic payloads and a stub trainer. They perform no model restore, forward pass or optimizer update.
- The wrapper's published A record agrees with its archive-size/digest record and the native complete marker. A holds step **544** for job **169097** and is **112,988,477,440 B**. Its archive digest is **22249bc7a3cb34117631e21db0132e9a4dc13f1ef85df4676c26ef1826c2c671**. Its native complete-marker digest is **0450e3a3c0265131175d4751329eba9f4605a5f391450a0c98b4e6fdefddc31c**.
- The effective training identity is **84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb**. It preserves global step 1,000, world four, seed 17, offset zero, fixed-zero sampling and the existing wall/save rules.
- The expected resume inventory contains nine checkpoint payloads and 28 hash-pinned run-input paths. It is not an archive-header listing or a fresh staged-filesystem inventory.
- The authenticated original metrics prefix has **544 complete rows**, **86,552,359 B**, and SHA256 **607fc9f232a967bb28097829ad9a84914f62507a37b6cae7e983a43f41c3449f**. No full prefix or numerical ending window was captured on Trinity.

## CPU equality and baseline integration

Canary's CPU and baseline packets pass cp2's local integration review. Both bind the original slot, effective configuration, attempt and complete metrics prefix. Their actual execution remains unauthorized.

The CPU wrapper calls the unchanged confirmed checker's **entry script**, with canonical kit, slot, bundle and disjoint output roots. It requires **general, zero GPUs, 16 CPUs and 800G**. The maximum wall is **five hours**; the initial private-space requirement is **554,291,183,104 B**. Fresh paths, capacity and shared-resource placement still need approval and verification.

The wrapper accepts only a matching real CPU PASS from the current CPU allocation, with all four native rank records and no optimizer update. It never submits a GPU job or substitutes the CPU-reserialized checkpoint for original A.

After that PASS, the baseline child authenticates one stable-descriptor read of every original metric row. It retains normalized rows **525–544**, not a raw copy, and uses the unchanged loss policy. Its limits are **512 MiB and 60 seconds**. The combined parent requires remaining capture/publication time and refuses partial returns.

