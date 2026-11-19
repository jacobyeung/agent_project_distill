"""Depth selection and a thin constructor for the delivered backend default."""
from dataclasses import replace
import numpy as np
from .ground_v3 import GroundV3
from .ground_sources import file_sha256
from .geometry_profiles import legacy_from_heads, scaled_from_heads, ContractAdapter

def load_geometry(path, frame_map, depth_source='depth_head'):
    if depth_source == 'depth_head':
        from rk.programs import load_heads
        return legacy_from_heads(path, frame_map, load_heads)
    if depth_source == 'tower_scaled':
        with np.load(path,allow_pickle=False) as z:
            unscaled='profile' in z and str(z['profile'])=='scaled_g3t_depth'
        if unscaled:return scaled_from_heads(path, frame_map)
        # E3's heads_g3s64 exports contain metric depth and metric translations.
        # The explicit switch declares their provenance; never multiply s again.
        from rk.programs import load_heads
        legacy=legacy_from_heads(path,frame_map,load_heads)
        contract=replace(legacy.contract,profile='scaled_g3t_metric',depth_source='g3t',depth_scale_count=1)
        return ContractAdapter(load_heads(path),contract,depth_identity=file_sha256(path))
    raise ValueError('depth_source must be depth_head or tower_scaled')


def build_profile(name, scene, geometry, source, *, depth_source='depth_head', **kwargs):
    import ofs
    from ofs import core as O
    if name!='native_selector':raise ValueError('unknown_ground_profile:'+str(name))
    expected={'depth_head':('legacy_v3122',),'tower_scaled':('scaled_g3t_depth','scaled_g3t_metric')}
    if geometry.contract.profile not in expected[depth_source]:raise ValueError('profile_depth_source_mismatch')
    return GroundV3(scene,geometry,source,mask_source='svp_sam3',selector=ofs,
        selector_identity=file_sha256(O.__file__),geometry_profile=geometry.contract.profile,**kwargs)

def export_values(backend,names):
    values=O.empty_values(len(names))
    for q,name in enumerate(names):
        slot=backend.question_slots[name]
        if slot.values is None:raise ValueError('Grounded name has no export: '+name)
        for key in values:values[key][q]=slot.values[key][0]
    return values
