cd /lab_data/tarrlab/jacoby/trinity_scratch_archive_20261111
ls */*.manifest.tsv | wc -l
grep -H -E 'weak_data/out/a3/PACK_object_rel_direction|6053fd47c70c0b25|7a1c59097139f59d|7e4e92918e312afd|9bf0518db09a07d8|9eecedf23da3bd91|b6ac18d55d697a23|ba96a4182147a384|c16c5db36e04c1ef|rows_a2/work/rasters/' */*.manifest.tsv | cut -c1-400 | head -60
echo RASTERS $(grep -h -c 'rows_a2/work/rasters/' */*.manifest.tsv | paste -sd+ | bc)
