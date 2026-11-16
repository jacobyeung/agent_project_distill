# Qwen3.5-9B native 3D boxes vs ground truth (2026-11-08)

Status: done (lane box3d_probe, trinity-2-18). Archive of code, test set and outputs:
`/data3/jjyeung/box3d_probe_20261108/box3d_probe_20261108.tar.gz` (sha256 551785b5…). The working copy
`trinity-2-18:/scratch/jjyeung/orch_cd/box3d_probe/` also holds the frames and the downloaded weights, and /scratch clears it after 7 days.

## Question
The user asked how accurate Qwen3.5's native 3D boxes are compared with a head we could train. A `<box_3d>` tool needs
boxes for object size, for deduplicating counts across views, and for distance programs. I measured base Qwen3.5-9B's
single-image boxes against GT boxes. As references I composed boxes from the GT 2D mask plus depth: one with GT depth (the
ceiling for a composed box) and two with degraded depth.

## Answer
- **Native boxes are usable at no cost, but they are not accurate.** On 222 held-out objects, the median centre error is 0.21 m
  (11% of the object's depth). The median longest-side error is 15%, giving a VSI-style size MRA of 66.7, and the median 3D IoU is 0.21. The model
  has no metric-scale bias (median predicted/GT depth 1.02, median longest-side ratio 0.97). All 222 answers parsed as JSON.
- **A box composed from a GT mask and GT depth is far better.** Its MRA is 84.1, its IoU 0.61 and its centre error 0.04 m. Native Qwen
  matches a composed box whose depth carries one ±15% scale error per object (MRA 74, IoU 0.18, centre 0.21 m) on centre and
  IoU, but it is about 7 MRA worse on size.
- **Supplying the GT intrinsics in the prompt changes nothing** (MRA 66.5, IoU 0.22, centre 0.21 m).
- **The angles are in units of π, not radians.** The cookbook README says radians, but its drawing code multiplies the angles by 180 to get degrees.
  Under the π reading the boxes stand upright (median tilt 4.5°), the median yaw error is 15.6°, and 12% of boxes reach IoU ≥ 0.5. Under the radians reading
  the tilt is 20.6°, the yaw error 45.8° and only 5% reach IoU ≥ 0.5. Any parser must multiply the angles by π.

## Format and source
- Source: Qwen3-VL cookbook `cookbooks/3d_grounding.ipynb` (github.com/QwenLM/Qwen3-VL, fetched 2026-11-08). The
  Qwen3.5-9B model card lists Hypersim and nuScenes under "Spatial Intelligence" but gives no prompt of its own, so I used
  the Qwen3-VL format. The base model answered in it on 222 of 222 calls.
- Prompt, as in the cookbook's example 4, one object per call:
  `Detect the {label} in the image and predict the 3D box. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].`
