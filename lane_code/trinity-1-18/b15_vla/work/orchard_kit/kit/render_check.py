"""Run one LIBERO-Spatial task with a random policy (renderer from MUJOCO_GL). Usage: random_episode.py <suite> <task_id> <steps> [camera_task_name]"""
import sys, os, time, numpy as np
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv
suite, tid, steps = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
bm = benchmark.get_benchmark_dict()[suite]()
task = bm.get_task(tid)
print('suite', suite, 'n_tasks', bm.n_tasks, '| task', tid, task.name, '|', task.language)
bddl = os.path.join(get_libero_path('bddl_files'), task.problem_folder, task.bddl_file)
env = OffScreenRenderEnv(bddl_file_name=bddl, camera_heights=128, camera_widths=128)
env.seed(0); env.reset()
init = bm.get_task_init_states(tid)
obs = env.set_init_state(init[0])
t = time.time(); rng = np.random.default_rng(0); r_tot = 0.0
for _ in range(10): obs, *_ = env.step([0, 0, 0, 0, 0, 0, -1])   # let objects settle
for i in range(steps):
    a = rng.uniform(-1, 1, 7); a[6] = rng.choice([-1, 1])
    obs, r, done, info = env.step(a); r_tot += r
    if done: break
img = obs['agentview_image']; print('obs keys', sorted(obs.keys())[:6], '... agentview', img.shape, img.dtype, 'mean %.1f std %.1f' % (img.mean(), img.std()))
print('steps', i + 1, 'reward', r_tot, 'done', done, 'sec/step %.3f' % ((time.time() - t) / (i + 1)))
import imageio; imageio.imwrite(os.path.join(os.environ['VLA_LOG_DIR'], 'render_%s_%s.png' % (suite, os.environ.get('MUJOCO_GL', ''))), img[::-1])
env.close(); print('EPISODE_OK')
