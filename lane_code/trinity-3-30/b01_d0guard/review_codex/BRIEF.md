# Read-only refute review (gpt-6-astra high): guard_read.py and one production merge change

You are an independent reviewer. Read-only: no edits, no network, no ssh, no Git, no deletion. Report verified problems only; design no fixes. Python for experiments: /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B (write nothing; use -c or stdin only).

Context: the init rule /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_INIT_RULE_20261116.md (items 3, 5, 6) defines a guard read: a candidate export minus step 544, paired on the same items. The task brief is /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/qs/01_d0_native_guard_kit.md (section "What to build", item 2, and "Tests").

Review targets (both written by a Claude model; you are the cross-family reviewer):
A. /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/report/guard_read.py (tests in report/tests/, inputs in report/inputs/). Check: pairing per item; the bootstrap is over physical rooms, 10,000 draws, seed 20261115, percentile 95% intervals; the guards are the three camera types (150 items each), metre distance on the frozen list, call rates (camera 450 of 450; metre distance at least 95%); room and non-metre distance are printed only; a refusal or non-answer scores 0 and stays in the denominator; the unit comes from question text only, through the brief-02 parser; PASS/FAIL per guard; the first line says internal instrument. Find any input that yields a wrong PASS.
B. /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/G3_ADMISSION.patch and the resulting guard_kit/admission.py `merge`: it compares in-memory rows with the authenticated JSON journal by canonical-JSON digest instead of Python equality and then continues with the journal rows. Check that it never admits a row whose content differs from the journal, and that no item leaves the denominator.

Output: a verdict (GO, GO AFTER FIXES with numbered findings each with file:line and a reproducing input, or NO-GO), at most 40 lines, as your final message.
