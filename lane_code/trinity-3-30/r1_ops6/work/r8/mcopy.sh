#!/bin/bash
# r1_ops8: copy the non-weight files of C''s model manifest (model.json cc724d5e) from the job's staged root to pool (tree_rebuild10 0140Z item 2-3 default)
export TZ=UTC; set -uo pipefail; umask 077
DST=/project/community/jjyeung/okh7/h_6ed2c7aa/m400/model; [[ -e $DST ]] && { echo "REFUSED: $DST exists"; exit 3; }
mkdir -p -m 700 $DST
timeout 300 srun --overlap --jobid 172660 -n1 -N1 timeout 240 nice -n 19 ionice -c2 -n7 bash -s $DST <<'S'
DST=$1; SRC=/tmp/jjyeung/a_6ed2c7aa/root/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
ls -la $SRC | head -20
for n in chat_template.jinja config.json merges.txt model.safetensors.index.json preprocessor_config.json tokenizer.json tokenizer_config.json video_preprocessor_config.json vocab.json; do
  [[ -f $SRC/$n ]] || { echo "ABSENT $n"; continue; }
  cat "$SRC/$n" > "$DST/$n.part" && mv "$DST/$n.part" "$DST/$n"
done
cd $DST && sha256sum * 
S
echo "srun rc=$?"
