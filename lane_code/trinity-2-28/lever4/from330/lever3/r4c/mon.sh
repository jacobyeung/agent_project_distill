P=/project/community/jjyeung/okh7/a15_cot_ap87f4ae5c2f44f; J=173978
echo "$(date -u +%T) $(TZ=UTC sacct -j $J -X -n -o State,Elapsed,ExitCode,NodeList | tr -s ' ')"; TZ=UTC sstat -j $J.batch -n -o AveCPU,MaxRSS,MaxDiskRead 2>/dev/null | tr -s ' ' | head -1
ls $P/a 2>/dev/null | tr '\n' ' '; echo; ls /project/community/jjyeung/okh7/af87f4ae5c2f44fc 2>/dev/null | tr '\n' ' '; echo; df -BG --output=avail /project/community | tail -1
