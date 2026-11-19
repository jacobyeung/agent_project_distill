cd /lab_data/tarrlab/jacoby
ls trinity_scratch_archive_20261111 | head -30
timeout 900 find trinity_scratch_archive_20261111 agent_project/aws_evac gcs_evac_20261111 aws_evac_20261104 -maxdepth 7 \( -name "PACK_object_rel_direction*" -o -name "6053fd47c70c0b25*" -o -name "7a1c59097139f59d*" -o -name "c16c5db36e04c1ef*" -o -name "scannet__scene0152_01*" -o -name "*.members.tsv" -o -name "*manifest*.tsv*" -o -name "MANIFEST*" \) -printf "%s %p\n" 2>/dev/null | head -80
