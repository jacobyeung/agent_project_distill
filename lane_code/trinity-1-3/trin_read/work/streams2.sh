# trin_read2: re-registration with launch_pull2.py (root bash no longer execs, so its comm stays bash across pause/resume).
cd /scratch/jjyeung/orch_n30/trin_read/work
tmux new-session -d -s trs_fr20 "cd /scratch/jjyeung/orch_n30/trin_read/work && PRIO=35 /usr/bin/python3 -s launch_pull2.py trin_read_fr20 -160000000 - /scratch/jjyeung/orch_n30/trin_read/dl/frames20.tar \"\$(cat fr_remote.txt)\" NEED20.txt > /scratch/jjyeung/orch_n30/trin_read/dl/fr20.log 2>&1"
sleep 8
tmux new-session -d -s trs_base "PRIO=50 /usr/bin/python3 -s /scratch/jjyeung/orch_n30/trin_read/work/launch_pull2.py trin_read_base 19329320960 - /scratch/jjyeung/orch_n30/trin_read/dl/base.tar 'cat /project/community/jjyeung/f3069074.tar' > /scratch/jjyeung/orch_n30/trin_read/dl/base.log 2>&1"
sleep 8
tmux new-session -d -s trs_frrest "cd /scratch/jjyeung/orch_n30/trin_read/work && PRIO=50 /usr/bin/python3 -s launch_pull2.py trin_read_frrest -1200000000 - /scratch/jjyeung/orch_n30/trin_read/dl/frames_rest.tar \"\$(cat fr_remote.txt)\" NEED_REST.txt > /scratch/jjyeung/orch_n30/trin_read/dl/frrest.log 2>&1"
sleep 8
