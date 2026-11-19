export TZ=UTC; P=/project/community/jjyeung/okh7/x_ee227714/o
ls $P | grep "\.gpu$" | head -10 | tr '\n' ' '; echo; stat -c %s $P/172660.gpu; head -c 600 $P/172660.gpu; echo; grep -m2 -i "h100\|a100\|name" $P/172660.gpu | cut -c1-200
