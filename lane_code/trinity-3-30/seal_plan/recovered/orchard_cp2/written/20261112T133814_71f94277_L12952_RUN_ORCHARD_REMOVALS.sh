<!-- recovered by seal_plan: transcript=71f94277 line=12952 utc=2026-11-12T13:38:14.595Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/out/RUN_ORCHARD_REMOVALS.sh  -->
#!/bin/bash
# For the USER to run on the Orchard login node (agents never run this).
# Source lists: ORCHARD_REMOVAL_LIST_20261112.md (project space, 1,127.4 GiB) and ORCHARD_HOME_REMOVABLE.md (/home, about 2.3 GB).
# Every path was checked on 2026-11-12 against the two live kits (LEG-S1 and the pending jobs 168042/168043); neither reads any of them.
echo "== before"; df -h /project/community | tail -1
P=/project/community/jjyeung
set -x
# --- project space, largest first
rm -rf $P/cp4tk_rt/arm/prestage
rm -rf $P/cp4tk_rt/ckpt/r1tk_3e52bed2_t25/state_a
rm -rf $P/p1_rt/aws/1_0050
rm -rf $P/p1_rt/aws/2_0128
rm -rf $P/p1_rt/ckpt/r1p1_1ccab006_w4/state_b
rm -rf $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/state_b
rm -rf $P/cp4tk_rt/arm/frozen
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_50.tar
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_100.tar
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_150.tar
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_200.tar
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_250.tar
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_300.tar
rm -f $P/p1c_rt/ckpt/r1p1c_2a6be879_w4/milestones/milestone_350.tar
rm -f $P/cp4tk_rt/ckpt/r1tk_3e52bed2_t25/milestones/milestone_100.tar
rm -f $P/cp4tk_rt/ckpt/r1tk_3e52bed2_t25/milestones/milestone_200.tar
rm -f $P/p1_rt/ckpt/r1p1_1ccab006_w4/milestones/milestone_150.tar
rm -f $P/cp4tk_f17/f17.tar.part
rm -f $P/cp4tk_rt/probe/nfs8g_165057.bin
rm -rf $P/p1c_rt/arm.v1_568b7cdc.20261105T193441Z
rm -rf $P/cp4tk_rt/arm/t6tk
rm -rf $P/cp4tk_rt/stage32/s160
rm -f $P/distill/okit/in/cr/rt_03b3a017a7d4.tar
rm -f $P/distill/okit/in/cr/rt_309f19bf6ee5.tar
rm -f $P/distill/okit/in/cr/rt_a0253b3f6f1f.tar
rm -f $P/distill/okit/in/cr/rt_af8edf79ab85.tar
rm -f $P/distill/okit/in/cr/rt_a9c55e9355d1.tar
rm -f $P/distill/okit/in/cr/18d26ee0473f.p00
rm -f $P/distill/okit/in/cr/24ceff72d9ec.p00
rm -f $P/distill/okit/in/cr/9e2912b39ee5.p00
rm -f $P/distill/okit/in/cr/rt_07b20cd4a498.tar
rm -f $P/distill/okit/in/cr/rt_140a527cb80f.tar
rm -f $P/distill/okit/in/cr/rt_39875bde0afa.tar
rm -f $P/distill/okit/in/cr/rt_dc989a8a632b.tar
# --- /home/jjyeung (quota)
H=/home/jjyeung
rm -f $H/okit/p/d59945c1/4fe70504.tar.part $H/okit/p/d59945c1/4fe70504.tar.sha256.part
rm -f $H/okit/p/d59945c1/50011a59.05 $H/okit/p/d59945c1/SHA256SUMS.50011a59.05 $H/okit/p/d59945c1/qtest
rm -f $H/okit/okit_v13_push.tar $H/okit/okit_cr_push.tar
rm -rf $H/okit/x/8865619b.prev $H/okit/x/b6827881.prev
rm -rf $H/okit/x/8865619b.fst_20261112T002530Z $H/okit/x/8865619b.fst_20261112T002530Z.st
rm -f $H/okit/tmp/.qprobe $H/home_top.txt
set +x
echo "== after"; df -h /project/community | tail -1
