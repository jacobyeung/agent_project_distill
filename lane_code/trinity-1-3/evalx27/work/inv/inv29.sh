set +e
ps -u jjyeung -o pid,etime,cmd | grep -E ' mv |tar ' | grep -v grep | head
ls -la /home/jjyeung/okit/tmp /project/community/jjyeung/okh7/x27tmp
du -sh /home/jjyeung/okit/tmp/x27env /project/community/jjyeung/okh7/x27tmp/x27env 2>/dev/null
