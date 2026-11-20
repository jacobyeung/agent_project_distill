export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; cat > /dev/null; exit 1; }
test -e $X/e2 && { echo E2_EXISTS; cat > /dev/null; exit 1; }
tar xf - -C $X && chmod 700 $X/e2 && cd $X && sha256sum e2/* && ls -l e2/
