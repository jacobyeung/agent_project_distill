cd /scratch/jjyeung/orch_n30
echo ---rr3; ls -la rows_rebuild3/out/rows/d0_v5/ rows_rebuild3/out/rows/d0_v5/vqa 2>&1 | head; 
echo ---rr; ls rows_rebuild rows_rebuild/out rows_rebuild/work 2>&1 | head -60
echo ---away; find evalx27/work/pull/x27/res/e193/merged/away evalx27/work/pull/x27/res/e193/merged/forward -maxdepth 4 | head -60
du -sh evalx27/work/pull/x27/res/e193/merged/away evalx27/work/pull/x27/res/e193/merged/forward evalx27/work/pull/x27/res/e193/merged/main
echo ---kit; du -sh cont_ops/work/d0/readk/kit/* ; ls cont_ops/work/d0/readk/kit cont_ops/work/d0/readk/tests
echo ---d0; ls cont_ops/work/d0/ ; ls cont_ops/work/d0/readk/kit/build 2>&1
