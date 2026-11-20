import multiprocessing,runpy
if __name__ == "__main__":
 multiprocessing.set_start_method('fork')
 runpy.run_path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z6d/out/diag_173911/mp_fork/observe.py',run_name="__main__")
