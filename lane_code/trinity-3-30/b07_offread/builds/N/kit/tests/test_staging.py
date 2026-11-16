import io
import tarfile
import pytest
from offnative.staging import archive, validate_media
from offnative.io import tar_bytes,sha
from offnative.cohort import cohort,media302

def test_stage_reuses_r_archive_reader(tmp_path):
    p=tmp_path/'a.tar';p.write_bytes(tar_bytes({'1':b'weights stand-in','2':b'config stand-in'}))
    result=archive(p,sha(p),tmp_path/'stage',max_bytes=100000)
    assert result['bytes']==31
    assert (tmp_path/'stage/1').read_bytes()==b'weights stand-in'

def test_hardlink_input_rejected(tmp_path):
    p=tmp_path/'b.tar'
    with tarfile.open(p,'w') as f:
        m=tarfile.TarInfo('1');m.type=tarfile.LNKTYPE;m.linkname='2';f.addfile(m)
    with pytest.raises(ValueError):archive(p,sha(p),tmp_path/'stage',max_bytes=100000)

def test_media_pin_admission():
    need=media302(cohort('revsi999t32'))
    assert len(validate_media(need,production=False)['missing'])==41
    with pytest.raises(ValueError):validate_media(need,production=True)
