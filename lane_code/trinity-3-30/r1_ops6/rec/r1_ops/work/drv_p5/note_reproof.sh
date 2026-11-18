export TZ=UTC
umask 077
KH=/project/community/jjyeung/okh7/x_69d2930d
F=$KH/o/171335.canary.reproof.json
[[ ! -e "$F" ]] && printf '%s\n' '{"canary_marker":"171335.canary.json","training_job":"171337","proof_job_attempt1":"171335","attempt1_state":"CANCELLED","proof_job":"171356","proof_partition":"general","utc":"2026-11-18T02:03:07Z","reason":"attempt 1 held the single advanced node per user and blocked the training job"}' > "$F" && echo NOTE_WRITTEN
