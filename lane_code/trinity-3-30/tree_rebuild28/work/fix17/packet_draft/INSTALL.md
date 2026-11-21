# INSTALL n34 (kit 7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771 = 929ab213 + fix16 DIFF 6dd5ffcc); not installed by fix17

Source: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w34/n_go (tar W/w34/s34_n_go.tar sha256 @TARSHA@; mirror trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/fix17/s34_n_go.tar, same sha256, compared on both ends).

## Upload order (to Orchard X/n, which holds 929ab213 today; by the installer)
1. Check first that X/n is 929ab213: `sha256sum SHA256SUMS.txt` = 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57 and `sha256sum -c SHA256SUMS.txt` all OK. If not, install fresh from the tar instead (all members), same post-install check.
2. The three changed members (every other member byte-identical, mode 0644 unchanged):
   - b/a.py   c5bdb533fe9a145213e81ea14bd5866e45a2525dac6f896a31b0ef37c56e6e6a  (was 891d105f)
   - b/pf.py  ceef90f0f76827aea677e418f86034ff7af500080b686f51290acf990a2f7a61  (was 531567f2)
   - k/j.json 2ca9c9bd75e78580dcc2540335882143a9683b011dc2da23cd68ccf6a3160821  (was b718d5d9; decoded shell 9f7a02bb958028e52a3ae177e43e0db21a3d006eed2c82c0adb7a7d2add47bc8, was 65891ca5)
3. Last, so the seal flips only when every member is in place: X/n/BUILD.json 3cdcf5345a0963f89ab2544c9320cf75f9ef619dba975b30974d5a7290df5d5b, then X/n/SHA256SUMS.txt 7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771.
No X/u object is new: the routing selection pin u/a49f117f (k/h.json e693876e) and the F1 receipt u/a7682dae are unchanged.

## Post-install seal check (on Orchard, in X/n)
- `sha256sum -c SHA256SUMS.txt` -> every line OK (55 members; list in kit_SHA256SUMS.txt here); `sha256sum SHA256SUMS.txt` = 7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771.
- File count in X/n = SHA256SUMS lines + 2 (SHA256SUMS.txt, BUILD.json); no other file (no __pycache__).
- BUILD.json decoded (base64-json payload): kit_sha256 = 7e23bbddb052a6f3ddb1915858dc03e8951d35d87cc9a3cd276f8853414d5771; config_sha256 = 76de3706b8eba5b8e0c6317f96a48d432f597358dfcda94bf1445589c6199bd7 = sha256(k/c.json); every other field as in 929ab213.
- Unchanged pins: k/t_e047002134f979bd.tar 5f2d77c4bc9905d877a259b666ac4a7fa6005de538730b806ceb249468699e38; k/c.json 76de3706...; k/n.json 4b8b9533eb12434186a9f42a06b44962574c3dedd51f9b8405d1f7e33d2504b9; k/p.json 77525f28cdbc24b8b1ce918460c91878708e200ebc05c7a17725a10787712694; k/y.json 9ce253964ef8d060ae99be248dab4d743035ef61fd49ee3a5b9642f543a434c2; k/h.json e693876efa3dea18d717d948db5bdd43111f128560e47a1c17822675343231fe.
- k/j.json decoded: base64-decode the payload; its sha256 = the capsule's sha256 field = 9f7a02bb...; in it, the a.py, d.py, h.py, rv.py, t.py lines take $Q_NS paths.
- Every arm/install record that pins the kit seal or k/j.json must name 7e23bbdd... and j decoded 9f7a02bb... (929ab213 and 65891ca5 before).
