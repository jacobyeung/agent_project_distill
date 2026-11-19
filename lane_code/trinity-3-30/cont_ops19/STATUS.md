# cont_ops19 STATUS (trinity-3-30; started 09:09Z 11-19; rotate by ~14:30Z)
Base state: /scratch/jjyeung/orch_n30/cont_ops18/STATUS.md (09:10Z section). Brief: orch_n30/briefs/cont_ops19_d.md.
## 09:15Z
- chain400 (tmux) alive, polling for m400 .done every 3 min (log cont_ops/work/h1read7/autosub400_a59a7bff4c4.log); not landed at 09:07Z.
- Plan when .done lands: direct auto-submits; I fill BIND400.json and build routed A/B (CPU, Orchard) while direct runs; post400.sh when direct ends.
- 09:26Z m400 ETA ~09:40-10:00Z per r1_ops8 STATUS (receipt may wait for checkpoint ~09:56Z). gov_fetch.py ready in work/ for a >=20 MB return (step-200 return was 11 MB).
## 09:45Z
- m400 export landed 09:31Z (RESULT r1_ops 0933Z; config 9459724f OK). Direct 173038 (a59a7bff4c4) submitted 09:34Z, PENDING Resources; tmux mon400_a59a7bff4c4.
- Routed 400: cont_ops17/work/BIND400.json filled; gen400b -> g400/; o_build10 on Orchard stage 813f42db/r10: A pkg a15_cot_apc9399fd2d1158, B pkg a15_cot_apcb2b4d58630bc (build10.out). o_place_pull_fill10 started (Orchard nohup pid 1390699, log 813f42db/r10/fill.log): pulls 4 parts, fills A then B, dry checks + 3.py check. GPU A/B wait until the facing+VSTI chain ends.
