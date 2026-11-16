"""Require loaded entries to expose their actual processor prompt inputs."""
def expected(frames,question):
    from .c8 import install
    install()
    from evalpath.official import build_prompt_context
    return dict(text_utf8=build_prompt_context(question,'ours').encode().hex(),
        anchor_indices=frames['anchor_indices'],fps=frames['fps'],
        total_num_frames=frames['total_num_frames'],timestamps=frames['timestamps'])

def verify_entry(entry,frames,question):
    method=getattr(entry,'prompt_inputs',None)
    if method is None:raise ValueError('loaded entry lacks processor prompt_inputs audit')
    actual=method(frames,question)
    if actual!=expected(frames,question):raise ValueError('loaded entry model prompt differs from direct kit')
    return actual
