export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; df -BG /project/community | tail -1
du -sk o/173912; ls -la o/173912 | head -40; ls u | grep -c .; ls u | grep -E "^(a49f117f|5e35c3ce|4e8e6c04|38c52f00|74640a29)" ; ls -la j/173912.log
grep -n "PIN_MISSING\|Error\|rdiff\|header_search" j/173912.log | tail -8 | cut -c1-300
