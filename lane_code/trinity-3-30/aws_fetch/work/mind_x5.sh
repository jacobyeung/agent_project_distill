cd /lab_data/tarrlab/jacoby/agent_project/aws_evac/d || exit 1
T=w19/ms/ap_f2ad01ad_runs_49becb79_m200.tar
echo "== host $(hostname)"
time tar tvf $T 2>&1 | head -20
for m in $(tar tf $T | grep -E 'artifact.json$|_evac_manifest/'); do echo "== member $m"; tar xOf $T "$m" | sha256sum; tar xOf $T "$m" | wc -c; done
A=$(tar tf $T | grep -E 'artifact.json$' | head -1); echo "B64 $A"; tar xOf $T "$A" | base64 -w0; echo
M=$(tar tf $T | grep -E '_evac_manifest/' | head -1); tar xOf $T "$M" | cut -c1-300
echo "== gcs tools"; which gsutil gcloud 2>&1; ls -d ~/google-cloud-sdk ~/.config/gcloud 2>&1
