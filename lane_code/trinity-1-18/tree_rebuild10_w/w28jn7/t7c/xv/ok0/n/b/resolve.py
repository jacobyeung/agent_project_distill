import argparse,json
p=argparse.ArgumentParser();p.add_argument("--pool");p.add_argument("--listing");p.add_argument("--output")
open(p.parse_args().output,"w").write("{}\n");print("R00 stub")
