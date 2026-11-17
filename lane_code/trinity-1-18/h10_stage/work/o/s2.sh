W=/project/community/jjyeung/okh7/e6fc152498; cat $W/sub2_ac6.nohup | tail -5; tail -40 $W/sub_b01ec87a6f29b00029ac6.out 2>/dev/null | cut -c1-600; TZ=UTC squeue -j 170706 -h -o '%i %T %M %N'
