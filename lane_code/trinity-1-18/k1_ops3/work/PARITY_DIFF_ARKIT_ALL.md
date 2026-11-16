# PARITY_DIFF_ARKIT_ALL (k1_ops3, trinity-1-18)

All 2,200 mismatching pinned ARKit frames. Pinned PNG from the Orchard replica (packed tar sha256 8049ab2e...); decoded PNG from wa.py on 1-18 (cv2 4.10.0, numpy 1.26.4). Orchard k6 used opencv-python-headless 4.14.0.94, numpy 2.2.6.

- sha256 equals pin: 2200 of 2200; shape equal: 2200
- max abs difference per frame (grey levels): {1: 2200}
- differing pixels per frame (of 307,200): min/median/p90/p99/max = [1, 1, 4, 7, 13]
- frames over a limit (max diff > 1 or differing pixels > 0.1% = 307): 0 in 0 captures; substitutable: 2200

| canonical | index | max diff BGR | differing px |
|---|---:|---|---:|
