#!/bin/bash
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; E=$O/orch_n30/events/k1_ops3
date -u +%FT%TZ
ls $O | grep INBOX_TO_DISTILL_ORCH_2026111[5-9]T | sort | tail -3
ls $E | grep -E '_ORCH_' ; ls /scratch/jjyeung/orch_n30/k1_ops3/inbox
tail -n 2 /data3/jjyeung/orch_n13_20261026/io_governor/REGISTER.md | cut -c1-200
head -3 /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | tail -1
