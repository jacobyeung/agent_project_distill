# Outside-encoder downloads

This lane has no network access and has downloaded nothing. Exact published metadata absent from the local evidence is marked **UNAVAILABLE**, not inferred from rounded model-card sizes. Such inputs remain ineligible for staging until the downloader records the missing fields. Gated encoders are optional and require the account holder's licence acceptance.

| Arm/input | Exact file URL | File | Exact size (bytes) | Published SHA256 / evidence | Gate |
|---|---|---|---:|---|---|
| A4 G3T | https://huggingface.co/thatbrguy/g3t/resolve/c55e91a04f1cbbad67359072536351201fd19e8b/model.safetensors | `model.safetensors` | Approximately 5.5 GB (review2 source-host report; private namespace hides local stat) | `d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702`, integration weight pin | Present on source host per review2; stage target path from STAGING_INVENTORY |
| A4 config | https://huggingface.co/thatbrguy/g3t/resolve/c55e91a04f1cbbad67359072536351201fd19e8b/config.json | `config.json` | UNAVAILABLE | `5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7`, integration pin | Optional |
| A5 C-RADIOv4 | https://huggingface.co/nvidia/C-RADIOv4-SO400M/resolve/main/model.safetensors | `model.safetensors` | UNAVAILABLE; design reports ~1.72 GB | UNAVAILABLE; published LFS SHA256 and immutable revision must be supplied | Optional, ungated according to local design |
| A6 DINOv3 | https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m/resolve/main/model.safetensors | `model.safetensors` | UNAVAILABLE; design reports ~1.21 GB | UNAVAILABLE; published LFS SHA256 and immutable revision must be supplied | **Gated and optional** |
| D2 DINOv2 registers | https://huggingface.co/facebook/dinov2-with-registers-large/resolve/main/model.safetensors | `model.safetensors` | UNAVAILABLE | UNAVAILABLE; published LFS SHA256 and immutable revision must be supplied | Optional diagnostic |
| A7 SAM 3 weights | https://huggingface.co/facebook/sam3/resolve/main/sam3.pt | `sam3.pt` | **3,450,062,241**, local receipt | `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`, **local checkpoint hash; published provenance not available offline** | **Gated and optional download**; local weights already exist |
| A7 SAM source | https://github.com/facebookresearch/sam3/archive/5dd401d1c5c1d5c3eedff06d41b77af824517619.tar.gz | `5dd401d1c5c1d5c3eedff06d41b77af824517619.tar.gz` | UNAVAILABLE | Archive hash unavailable; six extracted source hashes are pinned by `SAM3_RECEIPT.json` | Local source copy required |

The exact source root for A7 is `/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src`. `SAM_SOURCE_CHECK.json` checks each of the receipt's six files there. The local source copy contains 193 inventoried files totaling 4,739,916 bytes, and all six receipt checks PASS. Do not accept an archive merely because its revision name matches: its extracted file hashes must match the receipt.

The downloader can obtain published file sizes and LFS hashes from these exact metadata endpoints:

- https://huggingface.co/api/models/thatbrguy/g3t/revision/c55e91a04f1cbbad67359072536351201fd19e8b?blobs=true
- https://huggingface.co/api/models/nvidia/C-RADIOv4-SO400M?blobs=true
- https://huggingface.co/api/models/facebook/dinov3-vitl16-pretrain-lvd1689m?blobs=true
- https://huggingface.co/api/models/facebook/dinov2-with-registers-large?blobs=true
- https://huggingface.co/api/models/facebook/sam3?blobs=true

`work/resolve_download_metadata.py` consumes metadata already staged by the downloader, without networking. It writes the immutable revision URLs, exact sizes, and published LFS SHA256 values to `DOWNLOADS_RESOLVED.json`. It refuses missing sizes or hashes for weight files. Ordinary Git-managed files may publish a Git blob SHA1 rather than SHA256; record that as such and compute a separate local SHA256 for the runtime pin. Do not label a locally computed digest as published.

Stage all configuration, preprocessing and custom Python source from the same immutable revision as the weights. Each HF input folder requires `LOCAL_PIN.json` with a full 40-character revision and a SHA256 for every consumed JSON, Python and weight file. RADIO's custom code must expose the tested backbone-block interface and its `sam3` adaptor. A compatible stub establishes the adapter contract; the staged real provider still needs the prescribed smoke.

The downloader owns transfer authorization and cluster throttling. These are unresolved hand-off dependencies, not permission for this lane to fetch them. No outside arm runs with absent inputs or unverified runtime pins.
