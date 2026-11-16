import numpy as np
from fixtures_contracts import fixture, own_geometry
from trace_format.contracts import contract_epoch, status_text


def test_explicit_status_and_legacy_partial_grammar():
    from student_pilot.live_trace313 import parse_response
    assert status_text('heading unavailable')=='heading unavailable'
    assert status_text('heading unavailable','chair')=='chair: heading unavailable'
    for size in ('size 1.00 x 2.00 x 3.00 m','size unavailable'):
        parse_response('<ground obj="chair">','chair: heading unavailable\n'+size,'3.14')


def test_own_adapter_camera_transform_in_each_epoch():
    from student_pilot.ground_lifting import OwnGeometryAdapter
    own=own_geometry(fixture('nadir_positive')[1]())
    values=[]
    for enabled in (False,True):
        with contract_epoch(enabled):values.append(OwnGeometryAdapter(own).cam(2))
    for a,b in zip(*values):assert np.array_equal(a,b)


def test_recorded_depth_camera_and_metric_coordinates():
    own=own_geometry(fixture('nadir_positive')[1]())
    own.depth=None;own.recorded={'P1':([1.,2.,3.],.1)}
    values=[]
    for enabled in (False,True):
        with contract_epoch(enabled):values.append(own.click(2,[500,500],'P1'))
    assert values[0]==values[1] and values[1][0]==[1.,2.,3.]


def test_inherited_open_vocabulary_response_bytes():
    from tests.test_e2e_open_vocabulary import OpenVocabulary
    OpenVocabulary('test_unknown_name_flag_changes_no_response_bytes').test_unknown_name_flag_changes_no_response_bytes()
