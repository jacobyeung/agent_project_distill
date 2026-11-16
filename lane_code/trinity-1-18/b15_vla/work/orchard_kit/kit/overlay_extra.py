

# ---------------------------------------------------------------------------
# vla_libero overlay (2026-11-11): few-demo subsets d<demos per task>_s<seed> of every LIBERO suite.
#   vll_<suite>_<sub>  one suite;  vll_libero4_<sub>  the four suites jointly (40 tasks; one merged franka statistics set)
# ---------------------------------------------------------------------------
_VLL_SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
for _sub in ("d1_s0", "d5_s0", "d50_s0"):
    for _s in _VLL_SUITES:
        DATASET_NAMED_MIXTURES[f"vll_{_s}_{_sub}"] = [(f"{_s}_{_sub}_lerobot", 1.0, "libero_franka")]
    DATASET_NAMED_MIXTURES[f"vll_libero4_{_sub}"] = [(f"{_s}_{_sub}_lerobot", 1.0, "libero_franka") for _s in _VLL_SUITES]
for _name in ("libero_spatial_d50_s0_lerobot", "libero_spatial_d5_s2_lerobot", "libero_spatial_d1_s1_lerobot"):
    DATASET_NAMED_MIXTURES["pilot_" + _name.replace("_lerobot", "")] = [(_name, 1.0, "libero_franka")]
