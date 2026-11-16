B=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
du -sh /scratch/jjyeung/orch_n30/b04host 2>/dev/null; ls $B; ls $B/work | head -30
cat $B/parity_kit/settings.json | cut -c1-1200; echo
python3 -c "
import json; r=json.load(open('$B/parity_kit/host_restore/RESTORE.json')); print(list(r.keys())); print({k:(v if not isinstance(v,(dict,list)) else '...') for k,v in r.items()})
" 2>&1 | cut -c1-1500
cat $B/work/host_restore_cmd* 2>/dev/null | head; ls $B/work/*.sh 2>/dev/null
head -c 1500 /scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd/vendor/SAM3_RECEIPT.json; echo
ls /scratch/jjyeung/envs/sam3_scipy_ovl | head; ls /scratch/jjyeung/envs/sam3_scipy_ovl/* | head -20
ls /scratch/jjyeung/orch_n30/b04_e2ehook_m544h/m544 | head
