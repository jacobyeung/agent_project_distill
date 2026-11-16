Question: Which Reviewer 2 systems can provide a reproducible baseline against SPLIT on the same RGB video questions?

Answer: Evaluate VISPROG with an explicit framewise wrapper and a shared answer layer. The inspected releases of SpatialPIN, VLM-Grounder and GeoProg3D need services or scene representations that the RGB question interface does not supply. The comparison uses identical questions and official scorers for VISPROG, SPLIT and baseline.

Status: All twelve static VISPROG and ViperGPT comparisons use the authenticated v6 answer policy and remain provisional candidates. All three moving timing units and all four moving accuracy cells pass CPU admission, official-scoring, recovery and shared-answer fixture proofs. The moving comparison template contains verified SPLIT/baseline scores and awaits final system reports. ReSTI-500 has two confirmed wrapper defects pending stored-program replay; the post-drain census determines the complete replay list. The launcher owns production calls.

| System | Entry and required input | Dependencies or missing piece | Video interface and verdict |
|---|---|---|---|
| VISPROG | `notebooks/gqa.ipynb`; one RGB image and question; `engine/utils.py` generates and executes the program | Retired text-davinci-003; OWL-ViT-large and BLIP VQA checkpoints | No sequence API. RUNS WITH A DISCLOSED ADAPTATION: one program, 32 independent image executions, text voting and option mapping, explicit unit conversion and disclosed numeric aggregation. |
| SpatialPIN | `main/process_2d.py`, LaMa prediction, `main/process_3d.py`, `main/render_animate.py`; single RGB image, scene list, masks, inpainted images, reconstructed object meshes and Blender scene | GPT API, public GitHub upload credentials, Sudo/One-2-3-45++ API; local LangSAM/SAM, LaMa and depth/intrinsics models | Rendered output videos are not a video-input API. CANNOT RUN under the local-only reconstruction and data rules. The release provides no local replacement for its external reconstruction call. |
| VLM-Grounder | `vlm_grounder/grounder/visual_grouder.py`; referring query, RGB views, depth, intrinsics, poses/axis alignment, scene metadata, detections and cross-view matches | GPT-4o, SAM-H, PATS, Grounding-DINO 1.5 API or released YOLO-World alternative | Accepts static posed RGB-D views and outputs one 3D box. CANNOT RUN on the supplied RGB-only QA interface without adding reconstruction and question-to-measurement logic. |
| GeoProg3D | `code/geoprog3d/notebooks/main.ipynb`; query/task config, trained Gaussian geometry/color and language fields, autoencoder, scene views/cameras and geographic references | OpenAI program API, LoG, LangSplat, CLIP, GroundingDINO; missing per-scene trained assets and geographic/metric calibration | Queries a prepared static city field, with no time-indexed video representation. CANNOT RUN directly from 32 RGB frames. |

Quotable source-grounded descriptions:

VISPROG answers image questions with a generated program and pretrained image modules; its release has no video-sequence interface. A framewise evaluation therefore measures those released modules together with a disclosed aggregation rule.

SpatialPIN reconstructs objects from a single image through an external One-2-3-45++ service and a public-image upload step. Replacing that service and adding temporal fusion would evaluate a newly assembled video pipeline.

VLM-Grounder requires depth and camera calibration for multiple views and returns the 3D box of a referred object. Adapting it to RGB-only video questions would evaluate added reconstruction and question-answering components as well as the released grounder.

GeoProg3D requires a trained scene-specific 3D language field and geographic references that an RGB video question does not provide. Constructing those assets for each video, and adding a temporal representation for moving objects, would evaluate a substantially extended system.

Evidence:

- VISPROG commit `9626868c0d1007c41d8f210fe99f5c1facc3325f`: `engine/utils.py:10–46` takes an image state; `49–88` generates a question-only program with text-davinci-003; `engine/step_interpreters.py:145–174` uses BLIP VQA; `195–245` uses OWL-ViT-large at detection threshold 0.1 and NMS threshold 0.5; `1336–1360` registers the GQA module set.
- SpatialPIN wrapper commit `d7ec15cb2c4101d814b940ef573f9e6e4189959e` pins core submodule `2257120b7a8507f4f1da718907d889cefa14db14`. Its README requires GitHub and Sudo APIs. Core `main/process_3d.py:459–505` provisions the external object-reconstruction workflow; `main/render_animate.py:919–951` contains the spatial-reasoning prompt entry.
- VLM-Grounder commit `b8d7d42eda7c512a27a612caba1a67e1b8a93df3`: `vlm_grounder/grounder/visual_grouder.py:83–125` loads SAM, scene/detection/query records and matching; `665–733` projects/fuses points and returns an axis-aligned box. `vlm_grounder/utils/info_handler.py` supplies the image, depth and camera metadata.
- GeoProg3D commit `5e57a23af2b65b424fbd17c4caf1d38474598238`: `code/geoprog3d/config/config.yml:1–38` and `config/urban3d/campus.yml` name georeferencing and trained LoG/LangSplat checkpoints. `notebooks/main.ipynb` selects a dataset, scene and task, executes programs over those assets, and scores scene annotations. Fly-through training views do not create a temporal inference API.
- `out/SOURCES.json` preserves archive SHA-256 and byte counts. The source audit used repository archives and executed no upstream inference.
