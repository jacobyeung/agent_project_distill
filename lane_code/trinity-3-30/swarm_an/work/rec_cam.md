### 10.15 Where the printed camera motion is wrong (`deep2_camhead`)
- **Displacement:** the 47 items with a truth of 0.5 m or less cost 11.5 of the 18.1 type points at both steps. Neither one offset nor one scale explains the error: short moves look like a noise floor while absolute error also grows with distance; the best global scale scores 82.1 leave-one-room-out against 81.9. Frame pairs one or two sampled frames apart score 63.9 and 65.0 (18 items).
- **Rotation:** the 59 items under 20 degrees cost 19.7 of the 23.7 points. The response prints signed yaw, positive to the left, and every answer copies it; 4 of 150 answers have the opposite sign and none looks like a wrap or a supplement.
- **Movement direction:** 7 of the 8 wrong items pick another axis and 1 the opposite direction; 5 of the 8 have two horizontal components within a factor of 1.5, as do 22 of the 142 right items.
- **The errors are stable across checkpoints:** displacement keeps its sign on 131 of 150 items (rank correlation 0.97), rotation on 129 of 150 (0.94). Rooms carry 28% of the displacement error variance and 7% of the rotation variance.
- No frame pair is shared between a displacement and a rotation item, so the two errors cannot be related on this set.

