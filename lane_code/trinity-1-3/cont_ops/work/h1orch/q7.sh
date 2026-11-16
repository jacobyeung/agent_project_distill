echo "### SRC x_07ca49df"; cat /tmp/c8_src_modes.txt; echo "### E"; cat /tmp/c8_e_modes.txt
echo "### P"; cd /project/community/jjyeung/okh7/i_1be16f28/p && find . -printf '%m %y %s %P\n' | sort -k4
echo "### SRC sizes"; cd /project/community/jjyeung/okh7/x_07ca49df && find . -printf '%m %y %s %P\n' | sort -k4
