set -u; R=/project/community/jjyeung/vla_libero/out/rerun_20261116
if [ -e $R/phase.log ]; then echo "ALREADY STARTED"; tail -5 $R/phase.log; exit 0; fi
mkdir -p $R; cat > $R/rerun_driver.sh <<'DRV'
__DRIVER__
DRV
cd $R && setsid nohup bash $R/rerun_driver.sh > $R/driver.out 2>&1 < /dev/null & disown
sleep 20; hostname; cat $R/phase.log; ls $R/V; uptime
