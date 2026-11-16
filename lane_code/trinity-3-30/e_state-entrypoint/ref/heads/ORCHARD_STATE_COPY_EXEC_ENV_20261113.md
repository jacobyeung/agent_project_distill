# Orchard state-copy task launch under an empty exported environment

## Question and answer

Why can a verified helper bundle fail before Python starts under `srun --export=NONE`?

The first task executable must resolve without a caller-supplied PATH. Bare `env` fails with `execve(): env: No such file or directory`. The authenticated absolute executable `/usr/bin/python3.12` succeeds in the intended compute environment. Test the complete generated launch line with an empty environment; a login-only detached fixture does not test this node-side boundary.

## Evidence

The failed launch used bundle `acf803e79532c9044c11beb7d6590d628e1ad427e60134e8f60f752f9b4b3bdc`, bootstrap `3c2d74e81d5e0f0be6b9706c79148d83b476043ae686b015dacfc45e07a819ec`, and nonce `bd55ff0e842f0d02d1dc5c650848a7b9` in allocation 169097.

The complete 140-byte task return has SHA256 `113a8cb10231b4f8ebf60ccf42b47808e24adc495c42a7f83d375b7f262272dd`:

```text
error: execve(): env: No such file or directory
srun: error: orchard-community-2: task 0: Exited with exit code 2
```

The source is `/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097/result.raw`. Its authenticated `exit.json` has SHA256 `f5a8cf9da5ce69b512841f58b1d6dfc4d4e863350ff70875379dc9de7d8e0ce2`, return code 2, complete output and unbounded inherited address-space limits. No node helper, archive, upload or manifest ran.

The ordinary production monitor validates all four ranks through step 144 after the failed task. Retained durations for steps 142–144 are 133.766, 132.636 and 130.400 seconds. `around_launch_timings.json`, SHA256 `3d9ba9912f88e5379a16d3d6905915240866591b2dde78270fcbe2bb38c2aa6c`, pins the observations. They establish continued progress, not a synchronized causal no-slowdown test.

## Options and reasons

- **Bare executable names:** rejected by the observed task-exec failure.
- **Export the entire caller environment:** weakens isolation and can propagate unrelated settings; it is not needed to resolve a known executable.
- **Add a shell solely to repair PATH:** adds another executable and an implicit environment dependency.
- **Use absolute executables and audit the full node-side command:** preserves the environment boundary and makes path assumptions explicit. The absolute paths still need verification in the intended compute environment.

