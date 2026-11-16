"""Small receipt fixture matching the production and CPU rehearsal layout."""
from guard_core import write

def stage_fixture(root,step=50,artifact='a'*64,proof=False):
    checker=dict(status='VERIFIED',step=step,artifact=dict(sha256=artifact),fixture=True)
    stage=dict(status='complete',run='359fcc3c',step=step,artifact_sha256=artifact,checker=checker,fixture=True)
    write(root/'CANDIDATE_STAGE.json',stage)
    write(root/'exports'/('359fcc3c_m'+str(step))/'CHECK.json',checker)
    if proof:
        write(root/'STAGING.json',dict(export=dict(sha256='b'*64),fixture=True))
        write(root/'exports/469ddece_m544/RECEIPT.json',dict(status='complete',step=544,fixture=True))
        write(root/'exports/469ddece_m544/CHECK.json',dict(status='VERIFIED',step=544,fixture=True))
    return dict(step=step,artifact_sha256=artifact)
