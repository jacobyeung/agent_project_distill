# INSTALL kit w35 (ea058fed) on Orchard. Not done by fix21; follows the lane's install procedure (held submission, sessions, release)

n_root = X = /project/community/jjyeung/okh7/x_22c714e1 (k/p.json n_root); the kit folder is X/n (jn8.sh ROOT=$X/n). Each file below is under 20 MB, so each moves one at a time and unregistered, per LANE_RULES.

1. Before the kit, upload two n_root files (z.py copy_resolved_payload copies every k/p.json upload from n_root/u):
   - X/u/da19bb3ad9e9227e12bc28161713ae6a1f2a680e559039e290caa2cff0bc6eca, 129,141 B: the code record (decoded k/c0.json; bytes in w35/final/u_da19bb3a...). Mode r #2 may already have placed it; if so, check its sha256.
   - X/u/c672ad47b28d05d81e524baddb6d164f0f41c0b23a8cf0a1f49bfd045e93ec46, 10,997 B: the selection. It is byte-equal to X/o/174415/routing_selection.json; copy it on Orchard and check its sha256.
   - X/u/4e8e6c04... (P DB, 837,255,168 B) and X/u/ca0616db... (routing base) are unchanged and must still be present.
2. Move the old tree tar out of the kit folder (a move, not a deletion): X/n/k/t_e047002134f979bd.tar -> X/n_old_7e23bbdd/t_e047002134f979bd.tar. The seal checks (z.seal, launch_r1.build.verify) compare every file in the kit folder with SHA256SUMS.txt, so a leftover old tar refuses every step with E13 or R1_KIT_CONTENT_DIFFERS.
3. Upload the changed and added kit members from the tar (s35_n_go.tar, member n_go/...), mode 0644 (as in the kit):
   - b/il.py 9d310f19, b/dp.py 56d56112, b/pc.py 3fe4eed4;
   - k/t_db42866fd9e8d009.tar f5db525f;
   - k/a.json 9268ee79, k/7.json 66de88aa, k/c0.json 27d781b8, k/c.json 64a6465b, k/n.json dca3400c, k/p.json 1031e040, k/h.json ae72bfee, k/r.json 2f693cd0, k/j.json 5c2b0075;
   - then BUILD.json 86393eab, then SHA256SUMS.txt ea058fed last.
4. Post-install check on Orchard: `python3 -B -I -s X/n/b/v.py X/n` prints ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591. Also check that `sha256sum -c` of X/n/SHA256SUMS.txt is all OK and that no file in X/n is missing from it.
5. Wrapper: X/jn8.sh = packet jn8.sh, sha256 2de401bd4370b13ebaf50663f7f1bbd9f924c1fd5f90b1762dbd76662388c684. Submit with jn8.sh (held), mint sessions per k/y.json (unchanged, 112), then release.
6. Rehearsal at the gate: fix21/rh_ext (s/mk_orchard.sh, s/o_start.sh), run by the coordinator before review.json. It leaves about 270 GB on the node's /tmp. Read the PERSIST_SECONDS line in go.log.
