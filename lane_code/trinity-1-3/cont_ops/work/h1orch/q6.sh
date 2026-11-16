O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
cd $O/x_07ca49df && find . -printf '%m %y %P\n' | sort -k3 > /tmp/c8_src_modes.txt
cd $B/e && find . -printf '%m %y %P\n' | sort -k3 > /tmp/c8_e_modes.txt
wc -l /tmp/c8_src_modes.txt /tmp/c8_e_modes.txt
diff /tmp/c8_src_modes.txt /tmp/c8_e_modes.txt | head -60
cd $B/p && find . -maxdepth 2 -printf '%m %y %P\n' | sort -k3 | head -40
