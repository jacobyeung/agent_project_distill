set +e
cd /home/jjyeung/okit/tmp
nohup bash -c 'while pgrep -u jjyeung -f "mv x27env /project/community/jjyeung/okh7/x27tmp/" >/dev/null; do sleep 10; done; for f in x27c x27b x27c.tar.gz x27_pull.tar x27c_list.txt; do mv $f /project/community/jjyeung/okh7/x27tmp/ 2>/dev/null && echo "moved $f"; done; du -sh /home/jjyeung; echo DONE' > /project/community/jjyeung/okh7/x27tmp/move2.log 2>&1 < /dev/null &
echo started $!
