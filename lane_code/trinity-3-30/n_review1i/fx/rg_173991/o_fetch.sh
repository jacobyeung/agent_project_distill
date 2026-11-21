cd /project/community/jjyeung/okh7/x_22c714e1/o < /dev/null || exit 3
ls -la 173991/live 173991_gate < /dev/null 1>&2
du -sb 173991/live 173991_gate < /dev/null 1>&2
tar cf - 173991/live $( [ -d 173991_gate ] && echo 173991_gate ) < /dev/null | base64 -w0
