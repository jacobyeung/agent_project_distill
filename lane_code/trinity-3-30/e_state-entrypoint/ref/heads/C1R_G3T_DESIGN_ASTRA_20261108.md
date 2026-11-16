**I recommend camera-token alignment plus a weaker patch-token loss, with GT pose supervision remaining dominant. Keep both at the final LM layer and retain reduced alignment during mixed training.**

Camera tokens supervise scene geometry at the pose readout. Patch tokens supply local geometry useful for depth and pointing. G3T pose predictions should serve as diagnostics; they should not replace the available GT.

| Setting | Recommendation |
|---|---|
| Student positions | Exactly 32 CAMs after the video and before the question; final post-norm states. Patch alignment uses final visual-token states. Keep native causal attention. |
| Teacher | Detached G3T layer-23 camera and patch features from the existing cache. |
| Layout | Follow the fusion probe. Enable patches for duplicate or paired layouts; reject patch alignment with spread. |
| Projectors | Separate `Linear(H,2H) → GELU → Linear(2H,2048)` modules; zero biases; FP32 computation. This width matches the [released 3DRS projector](https://github.com/Visual-AI/3drs/blob/main/llava/model/language_model/qwen2/modeling_qwen2.py#L949). |
| Pose path | Feed the **unnormalized** camera-projector output into the existing four-block pose head. Normalize only inside the feature loss. |
| Loss | Preserve C1’s GT pose loss. Add camera and patch `1−cos` losses, each averaged within frames and then across rows. Token count must not multiply their weight. |
| Weights | Steps 1–400: camera **0.5**, patch **0.1**. Steps 400–800: cosine-decay them to **0.1** and **0.025**, respectively. No additional loss warmup. |
| Optimization | Preserve C1: LM `1e−5`, heads/projectors `1e−4`, AdamW, weight decay `0.01`, 3% LR warmup, cosine LR decay, clipping 1, frozen base ViT, batch 32, 800 steps. The LR split follows [Cambrian-P’s released recipe](https://github.com/cambrian-mllm/cambrian-p/blob/main/cambrianp/scripts/Cambrian-P-7B.sh). |

**Balance gradients, not numerical loss values.** On the first microbatch at step 1 and every 25 steps, measure task and combined alignment gradients at the **input to the last LM block**.
Set a detached multiplier `a = min(1, 0.5‖g_task‖/(‖g_align‖+ε))`; apply it to both scheduled alignment terms until the next measurement.
Aggregate norms across ranks and save `a` on resume. Log gradient cosine as well.
This is a proposed control heuristic. Final visual states alone are unsuitable for this comparison: the CAM pose loss does not consume those terminal visual outputs.

G3T’s convention risk is real and resolvable.
Its local head predicts gravity-to-camera rotation and FoV; its global head supplies translation and yaw.
The [released decoder](https://github.com/g3t-paper/g3t/blob/main/vggt/utils/inference_utils.py#L101) composes:

\[
E_i=L_iG_i,\qquad T_{C_i\leftarrow C_1}=E_iE_1^{-1}.
\]

Including frame 1 does **not** make its gravity frame equal its camera frame.
For teacher diagnostics, decode XYZW quaternions, compose both heads, rebase, and undo square-padding when comparing FoV.
