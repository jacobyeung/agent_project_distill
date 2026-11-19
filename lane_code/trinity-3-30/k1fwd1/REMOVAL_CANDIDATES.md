# k1fwd1 removal candidates (none deleted by the lane)
- Orchard /project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5: e/0-3 and f/0-3 and s.tar are hard links (no own bytes while the source packages exist; e/ shares inode group 1417811857 with a15_cot_apda6f7936c1779, f/ with e6fc152498, s.tar with h_6ed2c7aa/m400). Own bytes ~25 MB (overlay tars 2 x 8.5 MB, a.json copies, scripts) plus returns (P544 ~21 MB, P400 ~100 MB). Remove after fb_pack1 has scored and the RESULT is accepted.
- trinity-3-30 /scratch/jjyeung/orch_n30/k1fwd1: small files only (~3 MB).
