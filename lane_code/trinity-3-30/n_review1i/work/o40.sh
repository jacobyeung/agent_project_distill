X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ
for k in q n; do echo "== X/$k"; cd $X/$k < /dev/null || continue; sha256sum SHA256SUMS.txt < /dev/null; nice -n 10 sha256sum -c --quiet SHA256SUMS.txt < /dev/null; echo "check_rc=$? listed=$(wc -l < SHA256SUMS.txt) files=$(find . -type f < /dev/null | wc -l)"; find . -type f < /dev/null | sed 's|^\./||' | sort > /tmp/n_rv1i_f_$k; awk '{print $2}' SHA256SUMS.txt | sort > /tmp/n_rv1i_l_$k; echo "unlisted: $(comm -23 /tmp/n_rv1i_f_$k /tmp/n_rv1i_l_$k | tr '\n' ' ')"; grep -o '"GO": *[a-z]*' BUILD.json < /dev/null; done
cd $X; sha256sum jn6.sh < /dev/null; ls -la jn6.sh < /dev/null
for h in a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df; do ls -la u/$h < /dev/null; nice -n 10 sha256sum u/$h < /dev/null; done
df -BG /project/community < /dev/null | tail -1; TZ=UTC date +%TZ
