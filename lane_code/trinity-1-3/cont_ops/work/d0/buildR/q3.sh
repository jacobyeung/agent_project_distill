B=/scratch/jjyeung/orch_n30/b07_offread/builds/R; K=/scratch/jjyeung/orch_n30/b07_offread/kit/offkit
sed -n 85,130p $K/bind.py; echo "#### rebind 100-135"; sed -n 100,135p $B/kit/rebind.py; echo "#### rebind 224-330"; sed -n 224,330p $B/kit/rebind.py
