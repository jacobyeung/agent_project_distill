# ORCH NOTE: trainer fix coming from h1_headsft
Own-value rows train nothing after the first response (carrier_c1_routing.py:443-447, per h1_headsft). h1_headsft builds a tested fix; carry it in build 7.
