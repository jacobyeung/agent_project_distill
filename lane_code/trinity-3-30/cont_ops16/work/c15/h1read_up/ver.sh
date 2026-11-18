D=/project/community/jjyeung/okh7/af83c921
stat -c '%a %s %n' $D $D/d81f4a26.tar $D/e52a690b.jsonl
printf '%s  %s\n' 2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21 $D/d81f4a26.tar | sha256sum -c -
printf '%s  %s\n' 1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b $D/e52a690b.jsonl | sha256sum -c -
