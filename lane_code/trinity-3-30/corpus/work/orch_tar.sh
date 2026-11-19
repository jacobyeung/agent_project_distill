set -u
cd /project/community/jjyeung/okh7 || exit 1
which gsutil || ls /home/*/google-cloud-sdk/bin/gsutil 2>/dev/null
mkdir -p cc886a29e4ef || exit 1
for d in ae71c903_fetched/a24ea1a1936 ae71c903_fetched/ae470417b41 ae71c903_fetched/af35386aa3e ae71c903_fetched/aed15a8b7cb ae71c903/a37de5787ed ae71c903/b01ec87a6f29b00029a7c ae71c903/b01ec87a6f29b00029a87 ae71c903/b01ec87a6f29b00029ab2 ae71c903/b01ec87a6f29b00029ac6 ae71c903/b01ec87a6f29b00029ad2 ae71c903/bf94a7976a7e900029b5e ae71c903/e09e45fda45db00029c87 n2r/* x27ret/* b7e31d84a90c62f5/170193/* b7e31d84a90c62f5/170206/* b7e31d84a90c62f5/170235/*; do [ -d "$d" ] && find "$d" -maxdepth 1 -type f -size -300M; done | sort > cc886a29e4ef/files.txt
wc -l < cc886a29e4ef/files.txt; xargs -a cc886a29e4ef/files.txt -d '\n' du -cb | tail -1
