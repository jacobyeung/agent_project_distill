S=/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso
ls -la $S >&2
sha256sum $S/* >&2
ls /scratch/jjyeung/devs1_frames | head -5 >&2; ls /scratch/jjyeung/devs1_frames | wc -l >&2
du -sh /scratch/jjyeung/devs1_frames >&2
cd $S/.. && tar cf - run_iso
