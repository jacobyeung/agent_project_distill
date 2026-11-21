# R0 mesh scan, option (ii): decision rule (registered 2026-11-21 before any vertex is read; ORCH ANSWER 1836Z)

Population: 100 R0-dev ScanNet++ scenes against 738 others (685 division-A3 train, 53 benchmark or withheld), meshes
`/data2/jjyeung/raw_datasets/scannetpp/data/<scene>/scans/mesh_aligned_0.05.ply` (one layout: binary LE, 15 B per vertex).
Reads (one governed stream): the full vertex block of every dev scene, plus a strided sample of every other scene: 32 chunks of
4,368 vertices (65,520 B), evenly spaced through the vertex block. Dev signatures are computed on the same strided chunk positions
as the others, so every signature uses the same sampling.

Signature (invariant to rotation about the vertical z axis and to the origin), computed on the sampled vertices:
- H: height = z 99th minus 1st percentile.
- E1 >= E2: horizontal extents along the two principal axes of the xy point cloud (PCA), each the 99th minus 1st percentile.
- A: footprint area = number of occupied 0.10 m x 0.10 m xy cells x 0.01 m^2.
- R: radial histogram of horizontal distance from the xy centroid, 8 bins of 0.75 m (0-6 m, last bin open), as fractions.
Candidate pair: |H-H'|, |E1-E1'|, |E2-E2'| and |A-A'| each <= 5% of the larger value, AND L1(R,R') <= 0.10.
If the rule yields more than 30 pairs, tighten once to 3% and L1 <= 0.07, say so, and stop there.
Each candidate pair, and each of the 6 pairs within 0.1% of vertex/face counts from stage a, is settled by looking at three frames
of each scene (copied from local /scratch, no NFS read): same physical room or not, with one line of reason, or unsettled.
For candidates, the trained scene's full vertex block is then read (a later governed stream) to compare full-resolution signatures.
A same-room finding is a BLOCKER. Zero is recorded as "no recapture found by extent signature and inspection" (weaker than a proof).
