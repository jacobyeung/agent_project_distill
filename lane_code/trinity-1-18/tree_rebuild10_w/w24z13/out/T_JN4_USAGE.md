`t_jn4.sh` is byte-identical to `jn4.sh` (SHA-256 `80c80de72e9909f7567844ad9d14ba069b99b5de2aedac03439f7c1972eead83`). Submit `jn4.sh` itself; this file is not a submission driver. The lane must place it at X/jn4.sh with the existing kit at X/n.

```sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:10:00 --job-name=a15_cot_ap4ad76d6b4a7d X/jn4.sh
```

X denotes `/project/community/jjyeung/okh7/x_22c714e1`. The same command with the real path is:

```sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:10:00 --job-name=a15_cot_ap4ad76d6b4a7d /project/community/jjyeung/okh7/x_22c714e1/jn4.sh
```

Expected exit status: 3. Expected line: `<UTC timestamp> fewer than 4 H100; stop before staging`.
The existing screened tail is `X/o/<job>/j2.log`; stderr is `X/o/<job>/j2.err`. The publisher does not create `X/o/<job>/live/j2.log`. Its target is unchanged from jn3.sh.
The EXIT trap invokes the final publisher once. The existing periodic publisher remains separate and may also publish at startup.

With zero GPUs reported by nvidia-smi, the guard exits before `b/v.py`, `b/resolve.py`, and `job.sh`; no staging or training starts. The existing publisher imports `b/z.py` and reads screening metadata, so the guard does not precede all kit code. Local call traces are in `work/build24m4z13/a2/g0_4/events.jsonl`.
No Orchard submission or scheduler check was run here. The named ORCH ruling file was absent; this command follows the user-supplied item-1 instructions. The local tests establish behavior when the GPU query returns zero; Orchard device visibility remains to be checked by this submission.
