set +e
R=/home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz
for f in metadata/ORCHARD_LAUNCHER.json metadata/STAGING.json metadata/EXPORT_ARTIFACT.json metadata/launch_card.txt logs/main_generate.log; do echo "==== $f"; tar xzOf $R $f; echo; done
