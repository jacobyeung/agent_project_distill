W=/project/community/jjyeung/okh7/e6fc152498; cd $W
mv a2.tar.partial a2.tar && mv a4.tar.partial a4.tar && ls -la a2.tar a4.tar
D=$W/x/sj/b01ec87a6f29b/d; mkdir -p $D
nohup nice -n 19 bash -c "tar xf $W/a4.tar -C $D && tar xf $W/a2.tar -C $D s k/SAM3_RECEIPT.json && echo 'dx rc=0' >> $W/x.done || echo 'dx fail' >> $W/x.done" > /dev/null 2>&1 < /dev/null &
cat x.done
