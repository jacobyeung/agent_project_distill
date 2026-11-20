from pathlib import Path
import json
from tokenizers import Tokenizer,models,pre_tokenizers
from transformers import PreTrainedTokenizerFast,Qwen2VLProcessor,Qwen2VLImageProcessor
D=Path(__file__).resolve().parent/'assets';D.mkdir()
vocab={'[UNK]':0,'<|im_end|>':1,'<|im_start|>':2,'<|vision_start|>':3,'<|vision_end|>':4,'<|image_pad|>':5,'<|video_pad|>':6}
t=Tokenizer(models.WordLevel(vocab,unk_token='[UNK]'));t.pre_tokenizer=pre_tokenizers.Whitespace()
tok=PreTrainedTokenizerFast(tokenizer_object=t,eos_token='<|im_end|>',unk_token='[UNK]',additional_special_tokens=list(vocab)[2:])
# Native training_text calls this template for both prefix and complete exchange.
template="{% for message in messages %}{{ '<|im_start|>' + message['role'] + '\\n' }}{% if message['content'] is string %}{{ message['content'] }}{% else %}{% for part in message['content'] %}{% if part['type'] == 'text' %}{{ part['text'] }}{% endif %}{% endfor %}{% endif %}{{ '<|im_end|>\\n' }}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\\n' }}{% endif %}"
p=Qwen2VLProcessor(image_processor=Qwen2VLImageProcessor(),tokenizer=tok,chat_template=template)
p.save_pretrained(D)
(D/'config.json').write_text(json.dumps(dict(model_type='qwen2_vl',architectures=['Qwen2VLForConditionalGeneration'])))
print('assets',sorted(f.name for f in D.iterdir()))
from transformers import AutoProcessor
p=AutoProcessor.from_pretrained(D,local_files_only=True,trust_remote_code=False)
print(type(p).__name__,p.tokenizer.encode('Q0'))
