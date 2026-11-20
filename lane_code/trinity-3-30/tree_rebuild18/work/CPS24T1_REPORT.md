FAIL step 3: the refused-endpoint transport case is untested; all copier shutdown assertions pass.
The source and copied kit retain seal c992c930; b/ matches reference seal 240f8c17; every checked digest matches.
EXIT, TERM and USR1 return 0, 143 and 138; TERM and USR1 with a fake worker preserve its return codes 7 and 0.
Each case produces matching live logs, both .steps inputs, metrics, run/attempt JSON and marker listings.
Each case writes gcs_m100.json with “export not uploaded: sessions unusable (directory missing)”; no .done falsely claims upload.
Each case writes ckstop.json and a verified checkpoint_100.tar plus n_ck/<job>/complete.json.
pc.sh stops both copier groups, runs pc.py --final, then ep.py; z.py loads and screens evidence.
The trap never calls o.py. Decoded k/j.json calls it at line 438; its separate test produces verified o.tar and RESULT.json.
There is no dry-run/no-session CLI switch. Missing sessions trigger pc.py’s built-in error branch; --sessions only selects a file.
The synthetic 127.0.0.1:1 file has mode 0644: --sessions rejects its mode cleanly before transport; a valid file would be copied to sess.json.
Read-only host mounts and a read-only kit confine persistent writes to T; seccomp denies sockets and connect; no sess.json exists.
All tests inherit nice 10, four-CPU affinity, one-thread library settings and a 7 GiB address-space limit; T is below 500 MB.
RESULT.json contains the command ledger, exit codes, assertions, call-path description, setup failures, limitations and complete file inventory.
