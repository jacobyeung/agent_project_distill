import json,os
C='/scratch/jjyeung/orch_n30/cont_ops16/work/c15'
EV='events/cont_ops/'
K=C+'/h1read/kit/build/'
rows=[
# read_id, source, format, set, vehicle, job, purpose, reported_by, extra
('673bc60f_s200_devS1R0_direct_a8102c3207b',K+'a8102c3207b/fetched','kit','dev-S1+R0-dev','direct',172646,'R1 step-200 direct read; pooled harm rule decision',EV+'20261118T2202Z_RESULT_r1_m200_direct_read_verdict_PASS_harm_rule_silent.md',{}),
('673bc60f_s200_facing_direct_a2e46c0504e',C+'/h1face/kit/build/a2e46c0504e/fetched','kit','facing-twins','direct',172658,'R1 step-200 facing gate',EV+'20261118T2241Z_RESULT_facing_gate_m200_PASS_toward_holds_not.md',{}),
('359fcc3c_s200_R0_direct_ae470417b41',K+'ae470417b41/fetched','kit','dev-S1+R0-dev','direct',170757,'D0 step-200 R0-dev read',EV+'20261117T1349Z_RESULT_d0_m200_r0dev_done_d0_m100_submitted_170777.md',{}),
('17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936',K+'a24ea1a1936/fetched','kit','dev-S1+R0-dev+facing-twins','direct',170808,'H1-1 step-100 read',EV+'20261117T1522Z_RESULT_h1_1_m100_export_verified_h1read_submitted_170808.md',{}),
('359fcc3c_s100_devS1R0facing_direct_af35386aa3e',K+'af35386aa3e/fetched','kit','dev-S1+R0-dev+facing-twins','direct',170786,'D0 step-100 read',EV+'20261117T1513Z_RESULT_d0_m100_read_170786_complete.md',{}),
('469ddece_s544_devS1R0_direct_adff67f7ae9',K+'adff67f7ae9/fetched','kit','dev-S1+R0-dev','direct',171197,'LEG-S1 step-544 R0-dev direct baseline',EV+'20261118T0123Z_RESULT_step544_r0dev_direct_baseline_171197.md',{}),
('673bc60f_s100_devS1R0_direct_a5d2d909067',K+'a5d2d909067/fetched','kit','dev-S1+R0-dev','direct',172466,'R1 step-100 direct read; calibration',EV+'20261118T1035Z_RESULT_r1_m100_direct_read_calibration_would_stop_counting.md',{}),
('469ddece_s544_vsti_direct_acb2faedd41',C+'/h1vsti/kit/build/acb2faedd41/fetched','kit','VSTI-dev','direct',172475,'VSTI dev step-544 baseline',EV+'20261118T1112Z_RESULT_vsti_dev_step544_baseline_172475.md',{}),
('673bc60f_s200_vsti_direct_a35f73e87f0',C+'/h1vsti/kit/build/a35f73e87f0/fetched','kit','VSTI-dev','direct',172654,'R1 step-200 VSTI gate',EV+'20261118T2217Z_RESULT_vsti_gate_m200_PASS.md',{}),
('469ddece_s544_R0_direct_aed15a8b7cb_partial',K+'aed15a8b7cb/fetched','kit','dev-S1+R0-dev','direct',170928,'LEG-S1 step-544 R0-dev read, cancelled at 90% (superseded by 171197)',EV+'20261117T2146Z_RESULT_170928_cancelled_at_90pct_for_proof.md',{'partial':True}),
('673bc60f_s200_devS1_routed_A4',C+'/r1route/out3/A4/ret','routed','dev-S1-routed','routed',172744,'R1 step-200 routed read (camera, distance, room)',EV+'20261119T0306Z_RESULT_r1_m200_routed_A_H3_silent_capped_0.md',{'inputs':C+'/r1route/out3/A4'}),
('673bc60f_s200_room134_routed_B5',C+'/r1route/out3/B5/ret','routed','room-134 (dev-S1 36 + R0-dev 98)','routed',172858,'R1 step-200 routed room read',EV+'20261119T0400Z_RESULT_r1_m200_routed_read_complete_room_and_distance.md',{'inputs':C+'/r1route/out3/B5'}),
('469ddece_s544_devS1_routed_b1',C+'/r1route/out3/bases/b1/work/ret','routed','dev-S1-routed','routed',171253,'step-544 routed baseline (read 0 null_argmax, read 1 candidates_argmax distance)',EV+'20261119T0306Z_RESULT_r1_m200_routed_A_H3_silent_capped_0.md',{'inputs':C+'/r1route/out3/bases/b1'}),
('469ddece_s544_room134_routed_b2',C+'/r1route/out3/bases/b2/work/ret','routed','room-134 (dev-S1 36 + R0-dev 98)','routed',172456,'step-544 routed room baseline',EV+'20261119T0400Z_RESULT_r1_m200_routed_read_complete_room_and_distance.md',{'inputs':C+'/r1route/out3/bases/b2'}),
]
inv=[]
for rid,src,fmt,st,veh,job,purp,rep,ex in rows:
    m={'read_id':rid,'set':st,'vehicle':veh,'job_id':job,'purpose':purp,'reported_by':rep,'official':False}
    json.dump(m,open('meta/%s.json'%rid,'w'),indent=1)
    inv.append(dict(m,source=src,format=fmt,**ex))
json.dump(inv,open('INGEST_PLAN.json','w'),indent=1)
print(len(inv))
