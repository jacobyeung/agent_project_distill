cd /scratch/jjyeung/orch_n30/trin_read/work
exec /usr/bin/python3 -s launch_pull.py trin_read_fr20 -160000000 - /scratch/jjyeung/orch_n30/trin_read/dl/frames20.tar "$(cat fr_remote.txt)" NEED20.txt
