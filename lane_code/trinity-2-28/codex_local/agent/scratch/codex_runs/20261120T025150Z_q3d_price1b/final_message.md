Posted the [BLOCKER event](/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/q3d_price/20261120T0256Z_BLOCKER_q3d_price1_stock_weight_budget.md).

- Stock Qwen-3D, backbone and G3T weights total **21.031 GB**, exceeding the 20 GB cap before dependencies.
- The default decoder consumes ScanNet mesh geometry; swapping depth and poses alone would leave sensor geometry in arm B.

Code is cloned and preregistration preserved. The kit and CPU dry run remain incomplete. No large downloads or GPU work ran.