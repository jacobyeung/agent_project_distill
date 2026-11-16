set +e
export TZ=UTC
R=/home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz
for f in PLAN.json SPEC.json CODE_PINS.json RELEASE.json AUTHORIZATION.json HARDWARE.json STEPS.jsonl COMPLETE.json direct/camera/request.json direct/camera/kit/CODE_PINS.json direct/camera/LAYOUT_ADMISSION.json; do echo "==== $f"; tar xzOf $R $f; echo; done
echo "==== members"; tar tzf $R | sed -n 60,420p | grep -v '/results/' 
