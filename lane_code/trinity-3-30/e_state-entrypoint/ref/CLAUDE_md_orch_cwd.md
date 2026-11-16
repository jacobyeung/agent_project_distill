@/home/jjyeung/agent_project_distill/CLAUDE.md

This directory exists so that the harness's per-command git status has no repository to scan.
The repository is /home/jjyeung/agent_project_distill; every path that instructions write relative to the repo root resolves there.
Never cd into a Git work tree (the repository, /data2/jjyeung or /data2/jjyeung/agent_project_data), since the scan follows the shell's directory; use absolute paths, git -C, or a (cd DIR && ...) subshell.
This orchestrator runs on trinity-3-30. trinity-2-18 and trinity-2-28 are unreachable, so nothing on their /scratch can be read. Take state from this session's own context, the newest ORCH_STATE_SNAPSHOT_*.md in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/, the records under /data2/jjyeung/agent_project_data/distill_design/, and /data3/jjyeung/orch_n13_20261026/io_governor/.
Write orchestrator state snapshots to /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/, never only to node-local /scratch, so a node failure loses no state.
