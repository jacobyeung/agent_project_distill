# REPORT_CV2 (lever7; text saved by the lane from the builder's reply; 2026-11-22T02:36Z)
- k6's Orchard venv (one read-only call, cv2k6/oq1.sh/.out): Python 3.12.3, cv2 4.14.0 (opencv_python_headless-4.14.0.94, cp37-abi3-manylinux_2_28_x86_64), numpy 2.2.6; build 2026-07-28T09:22:32Z, baseline SSE SSE2 SSE3, dispatch SSE4_1 SSE4_2 AVX FP16 AVX2 AVX512_SKX, libpng 1.6.58, zlib 1.2.11.
- Earlier misses: local cv2 4.10.0.84 + numpy 1.26.4 (this node's EPYC 9224 also has AVX-512), so the cause was 4.10 vs 4.14, not dispatch.
- Wheels, sha256 equal to PyPI's: opencv 61,960,165 B 211e581f5a4670acbbe08fff36a35e9946039d2eea28b80394632d036d1be527; numpy 16,527,618 B fd83c01228a688733f1ded5201c678f0c53ecc1006ffbc404db9f7a899ac6249 (under 20 MB, unregistered).
- Stream lever7_gtcd_cv2 (cv2k6/stage_cv2.sh): registered 01:58:05Z (tier 3, pull, 8 MB/s, io-weight 1, priority 950), admitted 02:34:26Z, exited 02:34:38Z PIPE_RC=0 0, record lever7_gtcd_cv2.done.1795314878.
- Env /scratch/jjyeung/envs/k6cv2 (uv CPython 3.12.13; offline install; caches on /scratch); build info matches Orchard's.
- Decode (cv2k6/run_decode_k6.sh, the unchanged decoder): frames_k6/ (12,551 frames, 3.5 GB), DECODE_ARKIT_K6.json: 18/18 captures OK, 576/576 anchors byte-equal, no misses or errors, exit 0. frames/ and DECODE_ARKIT.json are untouched.
