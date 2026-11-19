flock() {
    printf 'flock %s\n' "$*" >> "$TRACE"
    if [[ "$1" == -w ]]; then shift 2; fi
    /usr/bin/flock -w 0.1 "$@"
}
