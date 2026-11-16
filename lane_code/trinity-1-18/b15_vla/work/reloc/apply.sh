set -u
OLD=/project/community/jjyeung/vla_libero; NEW=/project/community/jjyeung/45e92888780e; T=/project/community/jjyeung/45e92888780e_w
[ -d $OLD ] && [ ! -e $NEW ] || { echo "REFUSE: OLD missing or NEW exists"; ls -ld $OLD $NEW; exit 1; }
ps -u jjyeung -o args | grep -F "$OLD" | grep -v grep && { echo "REFUSE: processes use OLD"; exit 1; }
[ -s $T/reloc_hits.txt ] || { echo "REFUSE: no hit list"; exit 1; }
cd $OLD && tar cf $T/pre_sed_backup.tar -T $T/reloc_hits.txt kit/SHA256SUMS kit/KIT_SHA256 && echo "backup $(wc -l < $T/reloc_hits.txt) files $(sha256sum $T/pre_sed_backup.tar | cut -c1-16)"
find . -type l -lname "$OLD*" -printf '%p\t%l\n' > $T/reloc_links.tsv; echo "links $(wc -l < $T/reloc_links.tsv)"
cd / && mv $OLD $NEW && echo "MOVED $OLD -> $NEW"
cd $NEW
while IFS= read -r f; do sed -i "s#$OLD#$NEW#g" "$f"; done < $T/reloc_hits.txt
echo "sed done; remaining OLD in hit files: $(xargs -d '\n' grep -l -F "$OLD" < $T/reloc_hits.txt 2>/dev/null | wc -l)"
while IFS=$'\t' read -r p l; do ln -sfn "${l/$OLD/$NEW}" "$p"; done < $T/reloc_links.tsv
echo "relinked; remaining OLD links: $(find . -type l -lname "$OLD*" | wc -l); broken links: $(find . -xtype l | wc -l)"
cd $NEW/kit
sed -i "s#$NEW/logs/slurm_%j.out#$NEW/logs/j_%j.out#; s#sbatch -J jjy_vll_<tag>#sbatch -J a15_cot_ap<opaque hex>#; s#sbatch -J jjy_vll_t<arm>#sbatch -J a15_cot_ap<opaque hex>#" train_arm.sh gpu_test.sh
for f in $(grep -l -F vla_libero $(find . -maxdepth 1 -type f ! -name SHA256SUMS ! -name KIT_SHA256)); do sed -i 's#vla_libero#this kit#g' "$f"; done
echo "kit vla_libero left (top-level files): $(grep -l -F vla_libero $(find . -maxdepth 1 -type f ! -name SHA256SUMS ! -name KIT_SHA256) | wc -l); slurm_/jjy_vll left: $(grep -l -E 'slurm_%j|jjy_vll' *.sh | wc -l)"
mkdir -p $NEW/out/reseal_20261116 && cp SHA256SUMS $NEW/out/reseal_20261116/SHA256SUMS.af431489 && cp KIT_SHA256 $NEW/out/reseal_20261116/KIT_SHA256.af431489
find . -type f ! -name SHA256SUMS ! -name KIT_SHA256 ! -path '*/__pycache__/*' | sort | xargs sha256sum > SHA256SUMS && sha256sum SHA256SUMS | cut -c1-64 > KIT_SHA256
echo "NEW KIT_SHA256 $(cat KIT_SHA256) lines $(wc -l < SHA256SUMS)"; cp SHA256SUMS KIT_SHA256 $NEW/out/reseal_20261116/
cd $NEW && ( . kit/vl_env.sh; echo "V=$V"; train_env; python -c 'import sys,torch;print(sys.prefix, torch.__version__)'; sim_env libero; python -c 'import sys,libero, robosuite;print(sys.prefix, libero.__file__)' ) 2>&1 | tail -4
