W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E 'tr15|tr16'; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -sh $W 2>/dev/null | cut -f1
for l in tree_rebuild24m2d; do d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_$l | head -1); echo "== $l $d"; grep -c "Selected model is at capacity" $d/transcript.log; test -f $d/final_message.md && head -c 4000 $d/final_message.md || tail -c 800 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-300; echo; done
ls -lt $W/w24/out | head -15
test -e $W/work/dbb2.py || base64 -d > $W/work/dbb2.py <<EOB
aW1wb3J0IGhhc2hsaWIsIGpzb24sIG9zLCBzeXMKZnJvbSBtdWx0aXByb2Nlc3NpbmcgaW1wb3J0
IFBvb2wKVEFSR0VUID0gb3MuZW52aXJvbi5nZXQoJ0RCQl9UQVJHRVQnLCAnNGU4ZTZjMDRlNjk3
ZDhmMTJlY2Q5ZDcwNWUxOTdlOTRmNzNmNGE5ZGM1MDhiN2E5ZTliNGYzNjQ4NzMzNmY4NCcpCm4s
IG8gPSBzeXMuYXJndlsxXSwgc3lzLmFyZ3ZbMl0KCgpkZWYgZmlsZXMoKToKICAgIG91dCA9IFtd
CiAgICBmb3IgZCwgZHMsIGZzIGluIG9zLndhbGsobik6CiAgICAgICAgaWYgbm90IGQucmVwbGFj
ZShvcy5zZXAsICcvJykuZW5kc3dpdGgoJy9wL3Evc2VsZWN0aW9uJyk6CiAgICAgICAgICAgIGNv
bnRpbnVlCiAgICAgICAgZm9yIGYgaW4gc29ydGVkKGZzKToKICAgICAgICAgICAgcCA9IG9zLnBh
dGguam9pbihkLCBmKQogICAgICAgICAgICBpZiBvcy5wYXRoLmlzbGluayhwKSBvciBub3Qgb3Mu
cGF0aC5pc2ZpbGUocCk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICB3aXRo
IG9wZW4ocCwgJ3JiJykgYXMgaDoKICAgICAgICAgICAgICAgIGhlYWQgPSBoLnJlYWQoMTAwKQog
ICAgICAgICAgICAgICAgaWYgbm90IChmLmVuZHN3aXRoKCcuc3FsaXRlJykgb3IgaGVhZC5zdGFy
dHN3aXRoKGInU1FMaXRlIGZvcm1hdCAzXHgwMCcpKToKICAgICAgICAgICAgICAgICAgICBjb250
aW51ZQogICAgICAgICAgICAgICAgd2hvbGUgPSBoYXNobGliLnNoYTI1NihoZWFkKTsgYm9keSA9
IGhhc2hsaWIuc2hhMjU2KCkKICAgICAgICAgICAgICAgIGZvciBiIGluIGl0ZXIobGFtYmRhOiBo
LnJlYWQoMSA8PCAyMiksIGInJyk6CiAgICAgICAgICAgICAgICAgICAgd2hvbGUudXBkYXRlKGIp
OyBib2R5LnVwZGF0ZShiKQogICAgICAgICAgICBvdXQuYXBwZW5kKGRpY3QocGF0aD1vcy5wYXRo
LnJlbHBhdGgocCwgbiksIHNpemU9b3MucGF0aC5nZXRzaXplKHApLCBzaGEyNTY9d2hvbGUuaGV4
ZGlnZXN0KCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBoZWFkMTAwX2hleD1oZWFkLmhl
eCgpLCBib2R5X3NoYTI1Nj1ib2R5LmhleGRpZ2VzdCgpKSkKICAgIHJldHVybiBvdXQKCgpkZWYg
d3JpdGUodik6CiAgICB0ID0gb3MucGF0aC5qb2luKG8sICcuZGJfYnl0ZXMuanNvbi50bXAnKQog
ICAgd2l0aCBvcGVuKHQsICd3JykgYXMgaDoKICAgICAgICBqc29uLmR1bXAodiwgaCwgaW5kZW50
PTEpCiAgICBvcy5yZXBsYWNlKHQsIG9zLnBhdGguam9pbihvLCAnZGJfYnl0ZXMuanNvbicpKQoK
CmRlZiB0cmlhbChhcmdzKToKICAgIHAsIGhlYWQsIHZlciA9IGFyZ3MKICAgIGggPSBieXRlYXJy
YXkoaGVhZCk7IGhbOTY6MTAwXSA9IHZlci50b19ieXRlcyg0LCAnYmlnJykKICAgIHMgPSBoYXNo
bGliLnNoYTI1NihieXRlcyhoKSkKICAgIHdpdGggb3BlbihwLCAncmInKSBhcyBmOgogICAgICAg
IGYuc2VlaygxMDApCiAgICAgICAgZm9yIGIgaW4gaXRlcihsYW1iZGE6IGYucmVhZCgxIDw8IDIy
KSwgYicnKToKICAgICAgICAgICAgcy51cGRhdGUoYikKICAgIHJldHVybiB2ZXIgaWYgcy5oZXhk
aWdlc3QoKSA9PSBUQVJHRVQgZWxzZSBOb25lCgoKb3V0ID0gZmlsZXMoKQppZiBub3Qgb3V0Ogog
ICAgc3lzLmV4aXQoMSkKdiA9IGRpY3QodGFyZ2V0X3NoYTI1Nj1UQVJHRVQsIGZpbGVzPW91dCkK
d3JpdGUodikKcHJpbnQoJ2RiX2J5dGVzJywganNvbi5kdW1wcyhbKHhbJ3BhdGgnXSwgeFsnc2l6
ZSddLCB4WydzaGEyNTYnXVs6MTZdLCB4Wydib2R5X3NoYTI1NiddWzoxNl0pIGZvciB4IGluIG91
dF0pLCBmbHVzaD1UcnVlKQpmb3IgeCBpbiBvdXQ6CiAgICBoZWFkID0gYnl0ZXMuZnJvbWhleCh4
WydoZWFkMTAwX2hleCddKQogICAgeFsnZXF1YWxfdGFyZ2V0J10gPSB4WydzaGEyNTYnXSA9PSBU
QVJHRVQKICAgIG93biA9IGludC5mcm9tX2J5dGVzKGhlYWRbOTY6MTAwXSwgJ2JpZycpCiAgICB4
WydoZWFkZXJfOTZfOTlfdmVyc2lvbiddID0gb3duCiAgICBpZiB4WydlcXVhbF90YXJnZXQnXToK
ICAgICAgICB3cml0ZSh2KQogICAgICAgIGNvbnRpbnVlCiAgICB2ZXJzID0gW3cgZm9yIHcgaW4g
KDMwMDAwMDAgKyBtaSAqIDEwMDAgKyBwYSBmb3IgbWkgaW4gcmFuZ2UoNywgNjEpIGZvciBwYSBp
biByYW5nZSgwLCAyMSkpIGlmIHcgIT0gb3duXQogICAgcCA9IG9zLnBhdGguam9pbihuLCB4Wydw
YXRoJ10pCiAgICB3aXRoIFBvb2woOCkgYXMgcG9vbDoKICAgICAgICBoaXRzID0gW3IgZm9yIHIg
aW4gcG9vbC5pbWFwX3Vub3JkZXJlZCh0cmlhbCwgWyhwLCBoZWFkLCB3KSBmb3IgdyBpbiB2ZXJz
XSwgY2h1bmtzaXplPTQpIGlmIHIgaXMgbm90IE5vbmVdCiAgICB4WydoZWFkZXJfc2VhcmNoJ10g
PSBkaWN0KGJ5dGVzPSc5Ni05OSAoU1FMSVRFX1ZFUlNJT05fTlVNQkVSKSwgYWxsIG90aGVyIGJ5
dGVzIHVuY2hhbmdlZCcsIGNhbmRpZGF0ZXM9bGVuKHZlcnMpLAogICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICByYW5nZT0nMy43LjAuLjMuNjAuMjAnLCBmb3VuZD1bZGljdCh2ZXJzaW9uPXcs
IGhleD13LnRvX2J5dGVzKDQsICdiaWcnKS5oZXgoKSkgZm9yIHcgaW4gaGl0c10pCiAgICB3cml0
ZSh2KQogICAgcHJpbnQoJ2hlYWRlcl9zZWFyY2gnLCB4WydwYXRoJ10sICdmb3VuZCcsIGhpdHMs
IGZsdXNoPVRydWUpCg==
EOB
sha256sum $W/work/dbb2.py
cat > $W/prompts/build24m3.md <<'EOPY'
# Codex build 24m3 of lane tree_rebuild: tree 24l4r (removal lists by role protected_rooms) into the launch kits, bind the pointing K1 held-out list, census through the tree's post-condition, discovery kit records WOULD_REFUSE

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24` only, except `work/build24f/` and the rehearsal files of `work/build24k/` (names starting rehearsal, make_rehearsal, check_rehearsal, go_rehearsal, REHEARSAL, FIXTURE, dirs rehearsal_k*), which you only read. New disk space under 200 MB in all. Keep every existing package unchanged; move superseded files to `L/attic/`. Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24m2d.md`, `build24m2c.md`, `build24m1.md`, `build24k.md` and those they name (rules hold). Base: build 24m2d (`out/BUILD24M2D_REPORT.md`, `out/DELIVERY_24M2D.json`, its package) on top of 24m2c (`out/BUILD24M2_REPORT.md`, `out/MISSING_STAGED_PINS.md`, `out/SCENE_REBUILD_INPUTS.md`); read them first. Time limit: 110 minutes.

## Inputs
- Tree 24l4r (built and tested on trinity-2-28, Cursor review pending): `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24l4r_back/out/`: `tree_rebuild_b24l4r_92fe11f8.tar` (sha256 db64b3266674f0669759badbbbd3d8791f51a981f40872e412c6a2cbfdc21748; holds work/tree_r1), `HOST24L4R.patch` (against 96ff9a03), `TREE24L4R_SEAL.json` (92fe11f83f9e79234f00ed56521e8ad0b1dd48c80ffc593e9c0f6814610186b9), `UNCHANGED24L4R.json`, `BUILD24L4R_REPORT.md`, `PROTECTED_ROOMS_API.md` (read it in full: config entry shape, removal_order, Removals(stream=...), check_protected_rooms call contract, refusal names, what the kit must regenerate).
- Pointing list: `/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl` (sha256 d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1, 320 row keys, two K1 held-out rooms), evidence `AUDIT_POINTING_K1.json` 8d5c1a9a in the same folder. Expected production counts: pointing source 25,020; removed by the list 320; scene-excluded 6,584; admitted 18,116 before the target-shape filter; K1 held-out admitted 0 (ORCH 2235Z).

## Rulings (ORCH 2211Z, 2216Z, 2254Z, 2305Z, 2331Z)
- No stream of vehicle N trains a row in a K1 held-out room, R0, the withheld 80, BENCH v2, dev-S1 or official scenes.
- Lists bind by config with role protected_rooms; the safety is the tree's post-condition `student_pilot.r1_rooms.check_protected_rooms`, called by the kit's census step with the store in hand. Launch kits (q, n, n_go) refuse on any refusal of it. In kit qd ONLY (GO false, nothing trains) a census hit or a post-condition refusal is recorded as WOULD_REFUSE (code, counts, protected row keys per stream to live/) and the job continues into the preparation.

## Do
0. Scene-rebuild step (24m2c item 2b, stopped there only because the camera/routing population 4e8e6c04 had no bytes; ORCH 2331Z item 2): build it now exactly as build24m2c.md item 2b says (the kit step ONLY calls the tree's own `student_pilot.r2_scene_bindings.rebuild` on authenticated staged inputs and binds the two pins it returns; native verify unchanged; publishes receipt, coverage and census to live/ before WAITING_REVIEW), with one difference: its camera/routing population input is the regenerated routing database that the request's routing selection pin names, reached through the tree's own routing substitution as 24m2d resolves it (host.json records sha256 before and after). All other 53 inputs as listed in out/SCENE_REBUILD_INPUTS.md. If building it needs a change to a gate or the verifier, stop this item and write `out/SCENE_REBUILD_BLOCKER.md`. Time the step in the log.
1. Apply HOST24L4R.patch to `L/work/tree_r1` (now 96ff9a03 from 24m2c; fuzz 0); the seal must equal 92fe11f8, and every hash must match UNCHANGED24L4R.json (or untar the package's tree and compare); refuse and report otherwise. Rebuild kits q, n, kit_n_go and kit_qd on the new tree (k/t_*.tar, source inventory, code capsule, dependent seals).
2. Bind the pointing list in all four kits' decoded configs as exactly `{"path": <staged path>, "sha256": "d21e374f...", "role": "protected_rooms", "stream": "pointing"}` after the first 11 pinned lists and before NAMING_REMOVE; set `r1_training.launch22.removal_order` to the actual order; stage it as u/<sha> like the other lists and keep role/stream through localisation. Regenerate every receipt and pin that depends on remove_files (room audit, preparation, target filter, config identity, seals; see PROTECTED_ROOMS_API.md and the 24l4 report: stale receipts refuse). If a receipt can only be regenerated on the production stores (not on Trinity), make it an in-job step that only calls the tree's own native function on the authenticated staged inputs and binds its output, as the 24m2c scene-rebuild step does; if even that needs a gate or verifier change, stop this item and write `out/REMOVAL_RECEIPTS_BLOCKER.md`.
3. Census: the in-job census step (24m2c item 2d) calls check_protected_rooms for pose, vqa, routing and pointing with complete source rows before removals and the rows actually admitted after them, per the API contract (no samples, no summaries), and publishes each return value plus the census per stream to live/ before WAITING_REVIEW. Launch kits: any refusal stops the job by name at once. Kit qd: WOULD_REFUSE as above, then continue. Tests on the fixture: a protected pointing row left in refuses in kit q and is WOULD_REFUSE in qd (and qd goes on); a list key outside a protected room refuses; a clean fixture passes; the 320-key shape binds.
4. A kit-delta tool `out/bind_protected.py <stream> <list.jsonl>` that adds one more role list (for pose or routing lists built from the discovery census by fb_pack's `mk_room_removal.py`) to all four kits, restages, regenerates the dependent receipts, reseals, and writes an upload diff; test it on a fixture pose list. No tree change.
5. Discovery wrapper `out/jd.sh` (outside the kit seal): keep 24m2c's form, plus (ORCH 2305Z) a background loop that, once `<n_root>/o/<jobid>/routing_selection.json` exists, runs `python3 -B -I -s <x_22c714e1>/dbb2.py "$N" "<n_root>/o/<jobid>"` every 60 s until it succeeds (at most 180 tries); dbb2.py is `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/dbb2.py` (sha256 a7cbfb9f3093ee50bf373838cd952405de190cb8b5dbcc29a0ab0aa1a48d06e5; copy it to `out/dbb2.py` unchanged; it writes db_bytes.json with size, sha256, first 100 bytes hex and sha256 of bytes 100..end of each SQLite file under */p/q/selection, then a header search over bytes 96-99 with 8 processes). Test the loop against a fixture root.
6. Rerun the decoded scans, the kit/naming/resolver/guard/live/routing/review-wait suites, the hidden-path look-ahead (plan_payload modes r and q on real receipt bytes) and the census tests for q, n, n_go and qd. Reseal. Write `out/UPLOADS_24M3.json`/`.list` (diff after 24m2d, with stream root; top dirs q, n, qd, u), `out/UPLOADS_24M3_GO.json`, update `out/N_CARD_KIT_ROWS.md` (pointing list, census expectations, tree 92fe11f8), package `out/tree_rebuild_b24m3_<seal8>.tar` with `out/DELIVERY_24M3.json`, `out/BUILD24M3_REPORT.md` under 30 lines (line 1: tree seal and kit seals; line 2: scene-rebuild step built or stopped; line 3: receipts regenerated, in-job or built here; line 4: the expected first refusal or WOULD_REFUSE of the discovery job).

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under L (minus the excluded files). No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Beyond the tree patch and the list binding, do not change the tree, admission, legality, other removals, opener rows, the step-544 lineage, the resolver identity checks or the DEFERRED boundary. GO stays false except in `out/kit_n_go`, which is not uploaded.
EOPY
sha256sum $W/prompts/build24m3.md
