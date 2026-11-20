K=/project/community/jjyeung/okh7; ST=$K/813f42db/c21h544r
du -sb $ST-kit; ls $ST-kit | head -50
cd $K; find a15_cot_apdd982cd5c4b25 -type f -size +4M -printf '%s %n %p\n'; find a15_cot_apdd982cd5c4b25 -type f -size -4M | wc -l; find a15_cot_apdd982cd5c4b25 -type f -size -4M -printf '%s\n' | awk '{s+=$1}END{print s}'
find $ST -type f -size +4M -printf '%s %n %p\n'
