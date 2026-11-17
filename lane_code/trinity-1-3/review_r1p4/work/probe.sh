set -euo pipefail
BW=(/usr/bin/bwrap)
for entry in /* /.[!.]* /..?*; do
    case "$entry" in /home|/dev|/proc) continue ;; esac
    [[ -e "$entry" || -L "$entry" ]] || continue
    if [[ -L "$entry" ]]; then BW+=(--symlink "$(readlink "$entry")" "$entry"); else BW+=(--ro-bind "$entry" "$entry"); fi
done
BW+=(--dev-bind /dev /dev --proc /proc --tmpfs /home --dir /home
     --remount-ro /home --unshare-user --uid "$(id -u)" --gid "$(id -g)")
"${BW[@]}" /bin/bash -c 'test -r /proc/self/status && test -w /dev/null && test -d /home'
printf '%s\n' 'nested production namespace preflight PASS'
