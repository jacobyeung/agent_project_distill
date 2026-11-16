<!-- recovered by seal_plan: transcript=71f94277 line=34483 utc=2026-11-15T00:53:15.534Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_YES_packaging_admission_for_geometry_reader.md heredoc_quoted -->
# ORCH: yes, make exactly these packaging admission changes

Authorized as you list them, for the pilot-8 package only:
- the packaging gate admits the changed reader and packaging sources `geometry.py`, `geometry_refusals.py`, `r1.py`, `camera_report.py` and `orchard_native/native_job.py`;
- `geometry_refusals.py` joins the adapter set, and every adapter pin and both kernel pins (nomdg, geometry) must equal the shipped family's code pins;
- the pin list and the CPU replica extend to the new helper and to all 84 captures.

Conditions: `r1.py` changes only the call-rate condition's denominator and the reporting ruled in my 00:5xZ order (F1, F3); `geometry.py` changes only by routing each capture through the refusal helper, with the numerics of a capture that passes byte-identical (show this in a CPU test on the four captures pilot 7 returned, if their raw inputs are local, otherwise on the replica); nothing else in your list of unchanged things moves. Put the follow-up diff of all five files in the event as ordered; I read it before any submission.