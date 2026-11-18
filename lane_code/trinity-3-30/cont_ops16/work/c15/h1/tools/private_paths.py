"""Generate the same directory checks for each executable entry point."""
CHECK = '''umask 077
O=/project/community/jjyeung/okh7
private_dir() {
    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
        printf 'Directory must be mode 0700; run: chmod 700 -- %q\\n' "$1" >&2
        exit 3
    }
}
private_dir "$O"
'''
