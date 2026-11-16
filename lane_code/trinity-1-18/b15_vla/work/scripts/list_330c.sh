cd /scratch/jjyeung
W=orch_n30/recover_map2/work
grep -i -E "mp3d|scene|vlnce|navrun|vla|habitat|r2r|libero" $W/LIST_0_13.txt $W/LIST_1_8*.txt $W/LIST_0_28*.txt 2>/dev/null | head -60
echo "== survey"; du -sh orch_cd/nav_survey/refs/*; find orch_cd/nav_survey/refs -maxdepth 4 | head -50
echo "== dl_reader2"; head -40 orch_cd/mp3d_dl/bin/dl_reader2.py; cat orch_cd/mp3d_dl/dl/venv.receipt.json; cat orch_cd/mp3d_dl/stage/to330_base.extract.log
tar tf orch_cd/mp3d_dl/stage/to330_base.tar 2>/dev/null | head -10
