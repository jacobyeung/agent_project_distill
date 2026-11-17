# gt_audit removal candidates (lane folder on trinity-1-3; nothing removed by the lane)
- work/k1r/ (1.3 GB): copies of the 296 K1 GT rasters; originals on trinity-1-18 /scratch/jjyeung/orch_cd/dose_pool/out/{t1_gt,arkit_gt}/gt (sha = manifest pins).
- work/k1/, work/k1b/ (~56 MB): copies of K1 manifest, E3/GEO/lifting/scale-head outputs pulled from trinity-1-18 (originals there).
- work/remote/s118_pull1.tar (49 MB): tar stream of work/k1 (already extracted).
- work/mirror_gt_audit_1651Z.tar (76 MB): mirror tar (copy on trinity-1-18 /scratch/jjyeung/n30_mirror/gt_audit/, sha d6de7e42).
- work/geo/{stored,corrected,drop}/, work/lift/*/, work/scalehead/*/: rescored per-capture copies (reproducible from codeA scripts).
- work/r0/: extracted R0 code and question files (originals in the R0 archive mirror).
