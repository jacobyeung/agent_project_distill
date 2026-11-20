# cont_ops23 STATUS (trinity-3-30; started 23:36Z 11-19; rotate by 05:00Z)
Base: cont_ops22/STATUS.md "23:36Z ROTATE". Brief: briefs (cont_ops23).
## 23:43Z (exact)
- RUNNING general: 173412 H@544 remainder a15_cot_apdd982cd5c4b25 (418 items), orchard-community-0, since ~22:59Z; liveness tmux c22_monG412 -> cont_ops21/work/monG_173412.log.
- /project free 298.67 GiB (<300): o_fetch_hrem.sh guard would refuse. QUESTION 2339Z posted; DEFAULT = local route, zero /project bytes:
  1. pull: ossh 'bash -s' < work/o_pull2.sh | tar xf - -C /dev/shm/c23/okh7  (pool dir ae71c903/dd982cd5c4b250002a564 + package a/ minus a/e)
  2. place pool files as /dev/shm/c23/okh7/a15_cot_apdd982cd5c4b25/a/f/{0.tgz(=result.tar.gz),EXIT.json,RETURN_RECEIPT.json}
  3. python3 -B work/local_score.py /dev/shm/c23/okh7 /dev/shm/c23/okh7/813f42db/c21h544r-kit out/h544m /dev/shm/c23/work/h544m  (sealed kit's score(): authenticates via unpack/validate_exit/validate_receipt; writes SCORES, SCORES_vs_H400/H200, ALONE_H400/H200); python3 work/fmt.py out/h544m
  4. pool moves (renames) on Orchard: dd982cd5c4b250002a564 and dc863c3e6b41d0002a4ca -> ae71c903_fetched (o_cmp-style lines in work/o_post_bg.sh).
  5. corpus: parent 469ddece_s544_heldoutcam_H482p_173258 (src cont_ops21/work/H544/x, --inputs cont_ops21/work/H544, --archive-partial; dry-run OK in /dev/shm/c23/ingtest); remainder 469ddece_s544_heldoutcam_H418r_173412 (src = unpacked remainder from /dev/shm/c23/work/h544m/SCORES/current/remainder, --inputs /dev/shm/c23/inp_rem with package/ + src/).
  If /project >=300 GiB at job end: Orchard path instead: work/o_fetch_bg.sh then work/o_post_bg.sh.
- Local copies (RAM): /dev/shm/c23/okh7 = sealed kit (Orchard stage-kit), remainder package minus a/e, parent/H400/H200 packages (from cont_ops21/work/H*/pkg.tar). All four pass package_info. Test score H400 vs H200: out/test (5 s).
- Open: QUESTION 2054Z (11.7 GB partial tar on 3-30, user to delete); QUESTION 2339Z (above).
