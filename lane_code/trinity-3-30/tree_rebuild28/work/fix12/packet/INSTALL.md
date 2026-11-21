# INSTALL n33 (merged kit 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57); not installed by fix12

Source: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w33n/n_go (tar W/w33n/s33n_n_go.tar sha256 b0c03db32dadc4a8abf975e252a6f3bea108a2eabfd9451304b63ae2205b1d18; mirror trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/fix12/s33n_n_go.tar, same sha256 (compared on both ends)).

## Upload order (to Orchard, by the installer)
1. X/u/a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a (724 B, the F1 vqa receipt; copy: trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/u/, also in this folder). Check its sha256 on Orchard before step 2.
2. Kit members into X/n (changed vs the 9e809db4 generation; every other member is byte-identical, mode 0644 unchanged):
   - b/cn.py  90b3ca6cfa75b13eabb22f8a2c49c6ece0cf1b62156aea3f52e6aba8bf637d0d  (NEW file)
   - b/cs.py  0fba43e58ca9f6076ee771165c0c77a097b804b53a0d895e22a2f57a20f3fd0c
   - b/pf.py  531567f2055cbb168ecfd469ab22d4ead87e0527e74cf797ccc8b65fe1fee1f0
   - b/pl.py  ad29088af9e4bf71be97b99f32636ec2188c649161ada26b133dd778c76f84d2
   - b/sc.py  43d4cc263bf19de840860714719ac0ab0921a6a836e02b518f5fb2aa220bf274
   - b/sv.py  b4b4e20ed64c2fd35a22c73f91efa903c166862576a9991842f40fb787674d3d
   - k/c.json  76de3706b8eba5b8e0c6317f96a48d432f597358dfcda94bf1445589c6199bd7
   - k/j.json  b718d5d93ee50516927903654f26081eaeb1c1581b0407b75e823133207cc5a9
   - k/n.json  4b8b9533eb12434186a9f42a06b44962574c3dedd51f9b8405d1f7e33d2504b9
   - k/p.json  77525f28cdbc24b8b1ce918460c91878708e200ebc05c7a17725a10787712694
3. Last, so the seal flips only when every member is in place: X/n/BUILD.json b26fa29b2d545e1447b0c6ecea816e8f04f4a1a40553db97117088c775d0fec7 and X/n/SHA256SUMS.txt 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57.
(If X/n is installed fresh instead, upload all members of the tar; the same check applies.)

## Post-install seal check (on Orchard, in X/n)
- `sha256sum -c SHA256SUMS.txt` -> every line OK (55 members; the kit's list is kit_SHA256SUMS.txt here); `sha256sum SHA256SUMS.txt` = 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57.
- File count in X/n = SHA256SUMS lines + 2 (SHA256SUMS.txt, BUILD.json); no other file (no __pycache__).
- BUILD.json decoded (base64-json payload): kit_sha256 = 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57, config_sha256 = 76de3706b8eba5b8e0c6317f96a48d432f597358dfcda94bf1445589c6199bd7 = sha256(k/c.json).
- k/t_e047002134f979bd.tar = 5f2d77c4bc9905d877a259b666ac4a7fa6005de538730b806ceb249468699e38; k/y.json = 9ce253964ef8d060ae99be248dab4d743035ef61fd49ee3a5b9642f543a434c2; k/c.json 76de3706b8eba5b8e0c6317f96a48d432f597358dfcda94bf1445589c6199bd7; k/n.json 4b8b9533eb12434186a9f42a06b44962574c3dedd51f9b8405d1f7e33d2504b9; k/p.json 77525f28cdbc24b8b1ce918460c91878708e200ebc05c7a17725a10787712694.
- X/u/a7682dae... sha256 = a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a, 724 bytes.
- Every arm/install record that pins the kit seal or k/j.json (decoded a70b7551 before) must name 929ab2139b6dd408972e7b5bcffcf00588f70cecb006f6f9c0da44c55825dc57 and j decoded 65891ca554931f34c1fd2c04e668cbed52fe172127ae8ee4406d410dac0116d6.
