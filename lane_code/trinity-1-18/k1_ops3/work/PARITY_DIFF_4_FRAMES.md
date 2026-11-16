# PARITY_DIFF_4_FRAMES (k1_ops3, trinity-1-18)

Pinned PNG = Orchard replica cp4tk_fr/k6tk (sha256 verified against pin). Built PNG = wd.py on 1-18 from the /data2 mp4 (sha-verified), cv2 4.10 (4.13 gives identical bytes).

| capture | index | pinned sha | built sha | shape | differing pixels | max abs diff B,G,R | mean abs diff |
|---|---:|---|---|---|---:|---|---:|
| scannet/scene0232_02 | 249 | abc036811482 | 3f0004a0c8fb | (480, 640, 3) | 5 of 307200 | 0,1,1 | 0.000 |
| scannet/scene0370_01 | 1085 | 12a54e2cf5f2 | 0f3e0f31563c | (480, 640, 3) | 1 of 307200 | 0,1,1 | 0.000 |
| scannet/scene0398_00 | 988 | 14fbb934a25b | 8f015990373a | (480, 640, 3) | 1 of 307200 | 1,1,0 | 0.000 |
| scannet/scene0398_00 | 1235 | 0a026c4437f7 | 35b01a1d231c | (480, 640, 3) | 3 of 307200 | 0,0,1 | 0.000 |

Reading: every difference is at most 1 grey level, in 1 to 5 of 307,200 pixels. The mp4 bytes equal their pins, so the decoder or resize rounding differs from the one on Orchard, and the videos do not.
Fetch: one ossh call (work/o3.sh) walked each shard's tar headers with seeks and read only the 4 members (227,786 to 364,412 B each). Each sha256 equals its pin.
