# ns4.sh <host folder> <name under /tmp> <command...>: run a command with /tmp private and the host folder bound at /tmp/<name>.
H=$1; NAME=$2; shift 2
BW=(bwrap)
for e in /*; do case "$e" in /home|/dev|/proc|/tmp|/data|/data2|/data3|/project) continue;; esac
  [ -e "$e" ] || [ -L "$e" ] || continue
  if [ -L "$e" ]; then BW+=(--symlink "$(readlink "$e")" "$e"); else BW+=(--ro-bind "$e" "$e"); fi; done
BW+=(--tmpfs /tmp --bind "$H" "/tmp/$NAME" --dev-bind /dev /dev --proc /proc --unshare-user --uid "$(id -u)" --gid "$(id -g)")
exec "${BW[@]}" "$@"
