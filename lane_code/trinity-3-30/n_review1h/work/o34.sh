X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ
for h in a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73 5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84; do
  f=$X/u/$h; ls -la $f < /dev/null; nice -n 10 sha256sum $f < /dev/null; done
ls /project/community/jjyeung/okh7 < /dev/null | head -30
for h in a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73; do ls -la /project/community/jjyeung/okh7/u/$h < /dev/null 2>&1; done
sha256sum $X/o/173912/routing_selection.json $X/o/173912/receipt.json $X/o/173912/db_bytes.json $X/o/173881/routing_selection.json $X/o/173881/receipt.json < /dev/null 2>&1
TZ=UTC date +%TZ
