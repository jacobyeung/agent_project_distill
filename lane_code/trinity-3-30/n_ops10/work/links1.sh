O=/project/community/jjyeung/okh7; C=/project/community/jjyeung/cp4tk_fr/k6tk/parts; echo "LINKS1 $(date -u +%FT%TZ)"
for n in a0n3 a1n3 a2n3 v0n3; do stat -c '%i %h %s %n' $O/db3954b2/parts/$n/${n}_000.tar $C/$n/${n}_000.tar 2>&1; done
ls $O/db3954b2/parts; ls $C 2>&1 | head
cd $O; for d in d9c35d0a probe37845077 db3954b2 i_1be16f28 i_1be16f28.f2 s_8805de22 x27tmp k1tmp af83c921 d46dd56e669a050f 313db5a47f11ff0c 313db5a47f11ff0c.tar d831527c89cce90a c1bd947e8183c03b b31a069738d1e2f9; do
  [ -e "$d" ] || { echo "$d absent"; continue; }
  timeout 60 nice -n 19 find "$d" -type f -printf '%n %s\n' 2>/dev/null | awk -v d="$d" '{n++; t+=$2; if($1==1) one+=$2; else {multi+=$2; m++}} END{printf "%s files=%d total=%d single_link_bytes=%d multi_link_files=%d multi_link_bytes=%d\n", d, n, t, one, m, multi}'
done
find i_1be16f28 -maxdepth 1 -name 'd_c95023e46d917107.json' -printf '%n %s %p\n'
df -B1 /project/community | tail -1
