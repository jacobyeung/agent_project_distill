The H1 selection and SHA-pinned EQUAL report pass the round-7 deriver guard; production preparation is pending on Orchard.
Selection: eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9; exact r.json bytes, never relabeled.
EQUAL report: e48ab85bb9364aab228da7b23033605935e384761f76b0e6527c5e221b1c14b4; raw/final differences [], all 12 native indices verified.
H1 implementation: 2a4ef06888c59743516f5f7edad4ac3d45c6868cc5d3034ddae13654c8a6cc9c; tool: 2d5397aaf186a6be1637f2c68b53d5b45dae620a4a85dfd99d8468c2ad2d3b38.
Config identity: eb45ebfd7664a57226a6a9202c365ffba268d0bd0f295d879ad6adedde07a0c8; pending-review key: d12ae795 (read final reviewed key from compare.json).
Contract: 9a5270923627a9fae982acf90ac20ee4b695ac1932b98ae13038b63710a03ff9 (unchanged); KH x_3fdda0fb; persistent root r/39504485.
run_key 17c4ffa4, all 44 EXPORT_OBJECTS, trainer/tree and production wrapper bytes remain unchanged.
Final-config audit: native validate/authenticate and s1_routing implementation check PASS with real selection bytes; build reaches missing r16 at line 219 with isolated relocation/model fixtures.
Full native local admit stops on missing production pointing receipt; full production preparation is not claimed locally. Local kit remains FIXTURE.
Tests: test_admission_config + all five fix7 tests PASS; 19 deriver checks, 7 patch cases, gate binding, 12 real indices, deterministic rebuild PASS.
Proof: build/a_8c74b291.sh (also payload); SHA256 22ddf08a37c911682043c0149f4ae5923e98c11afb0235245b23a875227e86b3.
Proof uses certified FINAL KH, exact production staging/preflight/mode p (prepare_only), CUDA_VISIBLE_DEVICES='', then stops before first batch/mode t.
Proof isolates /tmp, slots and KH mirrors under /tmp/jjyeung/p_8c74b291_<job>; real job reuses nothing; jb.sh/go.json/training wrappers are untouched.
Submit: TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap8c74b291 -o "$KH/o/%j.proof.out" -e "$KH/o/%j.proof.err" -A mt01 -p general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue "$BUN/a_8c74b291.sh"
Four hours includes 1 h 39 min margin beyond 1 h 51 min mode p + 30 min staging; mode p requires zero GPUs; general availability is unqueried.
Outputs: KH/o/<job>.proof.json (admission, prepared seals, bindings, timing, rc), .proof.log/.out/.err and native step/preflight logs.
Local dry tests: shell success/failure, seal refusal and real filesystem namespace isolation PASS; 13 submission receipt cases PASS. Production proof NOT RUN.
Patch: build/c_patch.sh SHA256 c642f2343237413bba08aa2ac62212d4373d97d19f3185e27e069f3c7f481975; guarded retained live bundle i_1be16f28 state; backs up to v_8; refusal stops.
Payload sums: 25a9554487488c2d303e766c67f6bc3ce34f6519954ffa682cb9830ca02c9f28; upload p_6c368db0485677ea.tar SHA256 6c368db0485677eaa7096c326b04fd98e0f22fd96bdb7e73a09c3d372d51f574.
Operator order: patch -> o.sh -> g.sh -> review.json -> z.sh derive -> anon/certify -> proof job -> go.json -> s.sh.
The user launches one Devin tool+pin review; review/anon/GO records remain operator-supplied. REPORT.md gives exact commands and bindings.
Set/export PROOF_JOB from sbatch; require PASS/rc=0 plus final config/manifest match; s.sh enforces proof before submission.
Full hashes and audit evidence: evidence/fix8_admission/ and SHA256SUMS.txt. No SSH/network/Orchard/GPU/Git/deletion.
