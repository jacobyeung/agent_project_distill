# SPLIT static-cell tool faults

The correction packages are ready for an authorized launcher. The census contains 44 harness defects, eight planner failures and no infrastructure-only cases. Only the 44 harness questions are selected. The eight planner failures retain their answers.

**Question.** How can SPLIT correct tool failures in the Flash and Pro static-scene cells while preserving the planner comparison?

**Answer.** Classify each recorded failure from its tool call, response, trace and source receipt. Freeze the eligible question IDs before launch. Apply the same repairs to both planners, retain their source settings, and merge only the selected questions' first native answers into a complete cell.

| Cell | Harness | Planner | Infrastructure | Correction round | Retained answers |
|---|---:|---:|---:|---|---:|
| Flash ReVSI | 2 | 4 | 0 | r3074 | 997 |
| Flash VSIBench | 8 | 1 | 0 | r3075 | 492 |
| Pro VSIBench | 14 | 0 | 0 | r3076 | 486 |
| Pro ReVSI | 20 | 3 | 0 | r3077 | 979 |
| Flash VSTIBench | 0 | 0 | 0 | None | Entire cell |
| Pro VSTIBench | 0 | 0 | 0 | None | Entire cell |

The Flash packages are in `/dev/shm/jjyeung/split_fault_topup_1112/bundle_v6`; the Pro packages are in `bundle_v7` under the same root. Their delivery-seal SHA-256 values are `b87f54f57fd385c60e09530857bbc5c0b1d1bc45f4b4a9df37d383864795aa3b` and `544fcfd0ff78a1ed132b70519f705c7e622ece1937578b3ff4c1dca84749ec54`. Each delivery pins all package files, contracts, input maps, service code and launch tools.

**Repairs and their scope.**

- The frame helper preserves successful parsing. A rejected reply can supply explicit frame filenames or trigger a schema-constrained retry on the same images. Point coordinates never become frame indices.
- The SAM3 service serializes the native Triton NMS call. It retains the native inputs, outputs, candidate policy and thresholds.
- The executor gives registered closest-point work a separate 600-second bound. The planner's own Python retains its 60-second budget. The numerical geometry implementation is unchanged.
- The runtime initializes native thread-pool metadata before the sandbox, preserves each library's current thread count, and binds the declared temporary directory. The sandbox restrictions are unchanged.
- The runner uses its package-local frame registry. The registry retains the identity of the immutable input package and authenticates every frame's bytes.

The contracts preserve the source models, prompts, thinking policy, generation budgets, tool roster and reconstruction inputs. Selection uses fault evidence, never correctness. The merger verifies every source hash and copies each of the 2,954 retained answer receipts byte-for-byte.

**Evidence.** The lane's durable evidence directory is `/home/jjyeung/agent_project/agent/scratch/devin_lanes/split_fault_topup_1112/out/`.
