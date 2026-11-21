X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173964; TZ=UTC date +%TZ; df -h /project/community | tail -1
stat -c '%n %s %y' $X/u/4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 $X/u/5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df $X/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73
sha256sum $X/u/4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 $X/u/5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df
ls -la $O | head -40; ls -la $O/j7 2>&1 | head -40; tail -5 $O/j2.log 2>/dev/null | cut -c1-300
