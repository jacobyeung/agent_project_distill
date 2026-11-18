K=/project/community/jjyeung/okh7/x_69d2930d
sha256sum $K/b/c.sh $K/job.sh 2>/dev/null
sed -n 335,375p $K/b/c.sh
echo ====; grep -n "TK_JOBDIR" $K/b/c.sh $K/job.sh $K/b/*.sh 2>/dev/null | head -30
