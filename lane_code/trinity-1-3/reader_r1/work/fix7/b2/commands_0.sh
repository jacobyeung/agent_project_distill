set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/f40065df28aa3
printf '%s  %s\n' 89cb14a499609741233996e4023e235901849232a3aa92a7637d252108878990 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
