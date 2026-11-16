export TZ=UTC
MR=/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
BASE=/project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar
DRY=/project/community/jjyeung/okh7/d9c35d0a/dry_v1g
mkdir -p $DRY/snap
date -u +%T; ls -la $MR 2>&1 | head -3
echo "== base tar members (strip 3)"; nice tar tvf $BASE | awk '{print $1, $3, $6}' > $DRY/basels.txt; awk '{n=split($3,a,"/"); s=""; for(i=4;i<=n;i++) s=s (i>4?"/":"") a[i]; print $1, $2, s}' $DRY/basels.txt
echo "== extract small members into dry root"
SMALL=$(awk '$2<100000000 && $1 ~ /^-/ {print $3}' $DRY/basels.txt)
nice tar xf $BASE -C $DRY/snap --strip-components=3 $SMALL && ls -la $DRY/snap
echo "== bwrap dry bind at the logical model root (staged bwrap)"
cp /project/community/jjyeung/cp4tk_rt/kit/bwrap $DRY/bw && chmod +x $DRY/bw
$DRY/bw --unshare-net --die-with-parent --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 --proc /proc --dev /dev --dir /project --dir /project/community --ro-bind $DRY/snap $MR -- /usr/bin/python3 -c "
import json,os
r='$MR'; print('exists',os.path.isdir(r)); print(sorted(os.listdir(r)))
for f in ('config.json','preprocessor_config.json','tokenizer_config.json','video_preprocessor_config.json','model.safetensors.index.json'):
    p=os.path.join(r,f); json.load(open(p)); print('json ok',f)
idx=json.load(open(os.path.join(r,'model.safetensors.index.json'))); print('shards named in index',sorted(set(idx['weight_map'].values())))
" 2>&1
echo "bwrap rc $?"
