D=/project/community/jjyeung/distill
ls -la $D 2>&1 | head; ls -la $D/okit 2>&1 | head -30
timeout 120 find $D -maxdepth 5 \( -name 'rt_*' -o -iname '*r16*' -o -iname '*vxm*' -o -name '*5e1d07a4*' \) -printf '%y %s %TY-%Tm-%Td %p\n' 2>/dev/null | head -40
ls /project/community/jjyeung | head -30
