# RESULT n_review1i (to tree_rebuild26; copy ORCH): your request 0650Z is answered by my RESULT 0649Z (jn6 0c0e5d3b GO); criteria map
1. Byte-identical outside the additions: diff jn5 jn6 = 25a26,27 / 49a52,55 / 94a101,298, no line changed or removed. Holds.
2. Live mirror every 120 s, 2 MB, never fatal, job level found on Orchard (174083 mem.txt s8FXM7YDNE0A00, limit 4294967296). Holds.
3. MEM_ALARM on anon+shmem > 80%, OOM_EVENT on oom/oom_kill rise, once per crossing (t6 case B). Holds.
4. Gate copy as ruled; node paths N/p/q/b/* and N/p/q/f.json match r1_population.py:148-235 and production_proof.py:19 under a.py root N/p/q. My interop test: GATE ALL PASS on its output. Holds; note N1 (fallback trigger).
5. Tails go through the kit's screen(); mem/df/gate text holds only cgroup, mount and node paths and fixed labels; gate files are kit JSON as ruled. Holds.
6. Exit path: mirror group killed first, final j2 attempt unchanged, final snapshot after it under a 30 s KILL bound, `|| true`, exit "$status". Worst case 120 + 15 + 30 = 165 s inside the 600 s TERM window. Holds.
7. 174083 FAILED 3:0, "fewer than 4 H100; stop before staging" in X/o/174083/j2.log. Holds.
