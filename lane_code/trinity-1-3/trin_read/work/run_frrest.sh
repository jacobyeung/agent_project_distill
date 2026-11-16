cd /scratch/jjyeung/orch_n30/trin_read/work
exec /usr/bin/python3 -s launch_pull.py trin_read_frrest -1200000000 - /scratch/jjyeung/orch_n30/trin_read/dl/frames_rest.tar "$(cat fr_remote.txt)" NEED_REST.txt
