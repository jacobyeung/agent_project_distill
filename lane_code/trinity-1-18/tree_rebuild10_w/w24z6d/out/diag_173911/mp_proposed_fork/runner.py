import sys, http.client
sys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z6d/out/diag_173911')
from strict_sink import Connection
if http.client.HTTPSConnection.__module__ == 'http.client': http.client.HTTPSConnection=Connection
import multiprocessing,runpy
if __name__ == "__main__":
 multiprocessing.set_start_method('fork')
 runpy.run_path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z6d/out/diag_173911/mp_proposed_fork/observe.py',run_name="__main__")
