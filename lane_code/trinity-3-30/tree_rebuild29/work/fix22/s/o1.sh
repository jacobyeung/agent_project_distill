export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X || exit 1
df -BG --output=avail /project/community | tail -1
echo "qd seal $(sha256sum qd/SHA256SUMS.txt | cut -c1-16) bad $(cd qd && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find qd -type f | wc -l) pyc $(find qd -name __pycache__ | wc -l)"
(cd rcj && sha256sum * | cut -c1-16,65-)
ls -d c_* s2* s3* 2>/dev/null | tr '\n' ' '; echo
ls -la u/53faadaa0fe7f198369ecc2cd15a01a663cf26e968ffdca6dea686fece36b47e u/5e35c3ce* u/a49f117f* u/4e8e6c04* 2>&1 | cut -c1-160
ls u | wc -l; ls o | tail -5 | tr '\n' ' '; echo
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
sinfo -p preempt -h -o "%a %D %T" | head -5
