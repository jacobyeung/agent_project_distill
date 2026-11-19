W=/scratch/jjyeung/orch_n30
echo "== sb_framepool STATUS"; head -c 3500 $W/sb_framepool/STATUS.md; echo
echo "== gt_rasters STATUS"; head -c 2500 $W/gt_rasters/STATUS.md; echo
echo "== need files"; for f in $W/trin_read/root/x/need_frames.txt $W/trin_read/work/NEED20.txt $W/trin_read/work/NEED_X27.txt $W/trin_read/work/NEED_REST.txt; do wc -l $f; head -2 $f | cut -c1-300; done
echo "== parts"; for d in $W/trin_read/root/k6tk/parts/*; do ls -la $d | head -6; done
echo "== frame_map"; zcat $W/sb_framepool/work/frame_map.jsonl.gz | head -2 | cut -c1-700; zcat $W/sb_framepool/work/frame_map.jsonl.gz | wc -l
ls -la $W/sb_framepool/work/blobs | head -5; ls $W/sb_framepool/work/archive_stores | head -5; ls $W/sb_framepool/out | head -20
