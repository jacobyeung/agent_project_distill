set -u; R=/project/community/jjyeung/45e92888780e/out/rerun_20261116b
if [ -e $R/phase.log ]; then echo "ALREADY STARTED"; tail -5 $R/phase.log; exit 0; fi
mkdir -p $R; cat > $R/rerun_driver.sh <<'DRV'
__DRIVER__
DRV
cd $R && setsid nohup bash $R/rerun_driver.sh > $R/driver.out 2>&1 < /dev/null & disown
sleep 20; hostname; cat $R/phase.log; ls $R/V; uptime
