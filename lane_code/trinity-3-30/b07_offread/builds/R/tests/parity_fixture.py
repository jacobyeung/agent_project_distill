"""Run the accepted prompt proof with a local chat-template stand-in."""
from pathlib import Path
import sys
package=Path(sys.argv[1])
sys.path.insert(0,str(package/'proof'))
import fakes
class Processor(fakes.Processor):
    def apply_chat_template(self,messages,**kwargs):
        return '<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>'+messages[0]['content'][1]['text']+'<|im_end|>\n<|im_start|>assistant\n<think>\n'
fakes.install(Processor())
# Install a small transformer loader without importing the real transformer runtime.
from types import SimpleNamespace
fakes.module('transformers',AutoProcessor=SimpleNamespace(from_pretrained=lambda *a,**k:Processor()))
sys.path.insert(0,str(package/'parity'))
import prove_prompts
from line_capture import capture
with capture(Path(sys.argv[2]).parent/'metadata/PARITY_LINES.json'):
    prove_prompts.prove(sys.argv[2],processor_dir='/unused',kit_root=package/'reader')
