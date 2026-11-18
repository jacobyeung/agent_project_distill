export TZ=UTC
T=/project/community/jjyeung/okh7/af83c921
cd $T && mv d81f4a26.tar.partial d81f4a26.tar && mv e52a690b.jsonl.partial e52a690b.jsonl
chmod 0700 $T; chmod 0600 $T/d81f4a26.tar $T/e52a690b.jsonl
stat -c '%a %s %n' $T $T/d81f4a26.tar $T/e52a690b.jsonl
printf '%s  %s\n' '2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21' "$T/d81f4a26.tar" | sha256sum -c -
printf '%s  %s\n' '1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b' "$T/e52a690b.jsonl" | sha256sum -c -
date -u +%FT%TZ; squeue -j 170620 -o '%i %j %T %M %l %S %r' ; squeue -j 170620 --start -h -o '%S'
