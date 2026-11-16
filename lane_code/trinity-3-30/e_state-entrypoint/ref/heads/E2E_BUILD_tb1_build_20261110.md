# TB-1 frozen-LM build

Status: BUILT; serial CPU checks pass. Training is on hold. The orchestrator must issue GO for a named host/card set. The two-hour 0-18 allocation after MDG-A belongs to reads and probe P-c, not TB-1 training.

## Question

Can an MDG-A-initialized decoder and a rank-32 adapter on grounding-call tokens reach useful placement while the 9B base remains frozen and every shared 48 GB card stays within 36 decimal GB reserved?

The launch kit supports worlds 2, 4 and 8. It preserves global batch eight with 4, 2 or 1 sequential clips per rank. CP1 m200 is the requested production base. The base artifact and matching bundle are explicit parameters; local verification uses T0 m800 and MDG-A step-1500 decoder weights.

## What the kit builds

- `mdg_train.train` dispatches to a separate frozen-base DDP trainer. Prefix capture stays under no_grad. Each label chunk carries gradients through the suffix and decoder, then frees its graph. LoRA targets all 152 attention/GDN projections: exactly 36,225,024 FP32 parameters at rank 32.
- Atomic `<ground` and `<gap` preserve the existing routing-token IDs. Their two input/output embedding rows add 16,384 FP32 parameters. The mask objective learns the input ground row; output and gap rows have zero task gradient because this stream has no LM CE or gap loss. a0 freezes these rows and installs no LoRA.
- `tb1` and `tb1_a0` differ only in LoRA rank. Both keep the same decoder initialization, data, tokens, optimizer schedule, sampler and validation schedule. Adapter initialization preserves the decoder's random sampling stream. Chunk normalization preserves the full-clip objective; BatchNorm updates once per clip. Clip accumulation averages gradients and takes one optimizer step per global batch.
- The trainer reads 300 internal label items every 300 steps, stops at step 600 unless in-mask >=0.68 and null >=0.70, and calibrates tau only on reserved training scenes. It exports every validation improvement and saves optimizer/scheduler/rank RNG/sampler state every 20 minutes and on termination.
- The first 20 real steps include the 20 longest training prefixes and log every rank's cumulative phase peaks, losses, LoRA norm and prefix parity. Reserved memory must stay <=36,000,000,000 bytes. `TB1_STOP_AFTER_PROBE=1` stops and checkpoints after those steps; no chunk-4 retry runs automatically.
- Preparation pins the admitted index, source manifests and longest-prefix order. The launcher validates a local GO notice, local paths and live free memory immediately before torchrun. It uses an included local vnice copy, local caches and local outputs. It does not transfer inputs or launch a sync service.
- Checkpoints contain only decoder/adapters/rows and training state. Exports contain mdg-head-v1, optional LoRA and pinned token rows. The optional backend handoff patch loads those rows before routed decode.

## Data and evidence

Real local r7 checks passed on two clips with 22 and 10 labels, 32 and 31 used frames, and exactly 4,527 prefix tokens each. Native RGB processing and the length predictor produced identical token IDs; targets were finite. These checks perform no LM forward. Fresh admission gives 8,224 train / 440 tau / 464 val clips (1,028 / 55 / 58 scenes); all 8,224 training prefixes span 4,516-4,563 tokens. The frozen index matches every fresh split digest and data identity `950513c516928b8aba4db719269d1d0962a2c8863c2999a5dc4d7ca22400e87c`. The current builder and cached-index real-input check both exit 0.

The serial release checks pass on both base trees: MDG-A overlay 64 passed / 4 skipped (68 cases); stage-B overlay 34 passed / 2 skipped (36 cases). The inherited 19 stage-B cases remain in that suite. All three patches apply with zero fuzz; shell syntax and Python AST checks pass. They cover frozen-base isolation, nonzero LoRA gradients, no LoRA in a0, nonzero-adapter prefix equality, actual backend QueryStream gate positions, exact checkpoint continuation/export reload, loss normalization, clip accumulation, batch preservation, the 20-step stop flag and launcher admission. Socket-dependent checks and the inherited full-size CPU measurement are explicitly skipped.

The T0 m800 9B model loaded, but the distributed test failed before its first batch: the sandbox cannot access a local loopback interface. The retained ordinary-shell check uses two ranks at one thread each. Its estimated RAM is 50-90 GB and runtime 2-6 h; neither was measured. No eight-rank 9B CPU check is authorized on this shared node.

## Options rejected

