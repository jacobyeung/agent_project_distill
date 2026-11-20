import multiprocessing,runpy
if __name__ == "__main__":
 multiprocessing.set_start_method('spawn')
 runpy.run_path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z6d/out/diag_173911/mp_spawn/observe.py',run_name="__main__")
