set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/b9ef552934627
printf '%s  %s\n' 57d2a513b6770447680fc088a39fd02c00945491bdde46309e9ade0c84540f3e "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
