# Rulings the kit's launch gates read
- B0 (base Qwen3.5-9B, control-only, `vla.control_only: true`): authorised by the user on 2026-11-11 ("yes vla base model run!") as the base comparison, once per benchmark. Launch with `VLL_RULING=user_20261111_base_yes`. No VLA training or evaluation starts on any GPU until the orchestrator writes that the spatial student is ready.
