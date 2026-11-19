O=/project/community/jjyeung/okh7
cd $O
sha256sum 7c9f2d84/receipt.json; cat 7c9f2d84/receipt.json; echo
P='93b21a3a|9a7f3310|524b14f9|3d1d2d05|faa0cfc4|c48d5b62|5deb54bc|b32359ce|0b95850a|fd60ac2f|c1a42588|30612832|1e7b491b'
echo "== SHA256SUMS hits"; grep -H -E "^($P)" SHA256SUMS* */SHA256SUMS* */*/SHA256SUMS* 2>/dev/null | cut -c1-250 | head -40
echo "== names"; ls | sed -n 50,139p | tr '\n' ' '; echo
ls -d */f/h/r16 */s/q127808 */h/r16 */r16 */vxm_m4 2>/dev/null | head
