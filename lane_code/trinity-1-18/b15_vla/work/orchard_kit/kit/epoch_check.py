"""Does StarVLA's training loop advance the mixture dataset's sampling epoch? Builds the real dataset and DataLoader
(build_dataloader, num_workers=2, persistent), prepares it with accelerate, runs two passes the way VLATrainer does
(_reset_dataloader between them), and records the (epoch, index) each worker sees. usage: epoch_check.py DATA_ROOT MIX"""
import sys
from omegaconf import OmegaConf
from accelerate import Accelerator
import starVLA.dataloader.gr00t_lerobot.datasets as D
from starVLA.dataloader import build_dataloader
from starVLA.training.trainer_utils.trainer_tools import TrainerUtils
cfg = OmegaConf.create({"output_dir": "/tmp/vll_epoch_check", "datasets": {"vla_data": {
    "dataset_py": "lerobot_datasets", "data_root_dir": sys.argv[1], "data_mix": sys.argv[2], "action_type": "delta_qpos",
    "obs_image_size": [224, 224], "per_device_batch_size": 64, "load_all_data_for_training": True, "video_backend": "torchvision_av",
    "num_workers": 2, "sequential_step_sampling": False}}})
import os; os.makedirs(cfg.output_dir, exist_ok=True)
D.LeRobotMixtureDataset.__getitem__ = lambda self, i: {"epoch": self.epoch, "index": i, "draw": self.sample_step(i)[1:]}
collate = lambda b: b
dl = build_dataloader(cfg=cfg, dataset_py="lerobot_datasets"); dl.collate_fn  # noqa
from torch.utils.data import DataLoader
dl = DataLoader(dl.dataset, batch_size=64, collate_fn=collate, num_workers=2, persistent_workers=True)
dl = Accelerator().prepare(dl)
seen = []; it = iter(dl); ep = 0
for _ in range(2 * len(dl)):
    try: b = next(it)
    except StopIteration:
        it, ep = TrainerUtils._reset_dataloader(dl, ep); b = next(it)
    seen.append([(r["epoch"], r["index"], tuple(int(x) for x in r["draw"])) for r in b])
n = len(dl); first, second = [x for b in seen[:n] for x in b], [x for b in seen[n:] for x in b]
print("batches per pass", n, "samples per pass", len(first), "dataset len", len(dl.dataset))
print("epochs seen by workers: pass1", sorted({e for e, _, _ in first}), "pass2", sorted({e for e, _, _ in second}))
same = sum(a[2] == b[2] for a, b in zip(first, second))
print(f"pass2 draws identical to pass1: {same}/{len(first)}; distinct (traj,frame) draws per pass {len({x[2] for x in first})} of {len(dl.dataset)} frames")
print("EPOCH_REPLAY" if same == len(first) else "EPOCH_ADVANCES")
