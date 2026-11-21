# ns3.sh <ns dir> <c7 replica> <command...>: as ns.sh, with the snapshot replica given separately.
NS=$1; C7=$2; shift 2
BW=(bwrap)
for e in /*; do case "$e" in /home|/dev|/proc|/tmp|/data|/data2|/data3|/project) continue;; esac
  [ -e "$e" ] || [ -L "$e" ] || continue
  if [ -L "$e" ]; then BW+=(--symlink "$(readlink "$e")" "$e"); else BW+=(--ro-bind "$e" "$e"); fi; done
BW+=(--tmpfs /tmp --bind "$NS/q_22c714e1" /tmp/q_22c714e1 --dev-bind /dev /dev --proc /proc
     --ro-bind "$C7" /project/community/jjyeung/c7d31ddd --unshare-user --uid "$(id -u)" --gid "$(id -g)")
exec "${BW[@]}" "$@"
