from pathlib import Path
import json
from tokenizers import Tokenizer,models,pre_tokenizers
from transformers import PreTrainedTokenizerFast,LlavaProcessor,CLIPImageProcessor
D=Path(__file__).resolve().parent/'assets2';D.mkdir()
vocab={'t'+str(i):i for i in range(248047)}
for i,name in {0:'[UNK]',1:'<|vision_start|>',2:'<|vision_end|>',3:'<|image_pad|>',4:'<|video_pad|>',5:'A',6:'B',7:'Check',248044:'<|endoftext|>',248045:'<|im_start|>',248046:'<|im_end|>'}.items():vocab.pop('t'+str(i));vocab[name]=i
for i in range(80):vocab.pop('t'+str(i+100));vocab['Q'+str(i)]=i+100
t=Tokenizer(models.WordLevel(vocab,unk_token='[UNK]'));t.pre_tokenizer=pre_tokenizers.Whitespace()
tok=PreTrainedTokenizerFast(tokenizer_object=t,eos_token='<|im_end|>',unk_token='[UNK]',additional_special_tokens=['<|endoftext|>','<|im_start|>','<|vision_start|>','<|vision_end|>','<|image_pad|>','<|video_pad|>'])
template="{% for message in messages %}{{ '<|im_start|>' + message['role'] + '\n' }}{% if message['content'] is string %}{{ message['content'] }}{% else %}{% for part in message['content'] %}{% if part['type'] == 'text' %}{{ part['text'] }}{% endif %}{% endfor %}{% endif %}{{ '<|im_end|>\n' }}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
p=LlavaProcessor(image_processor=CLIPImageProcessor(),tokenizer=tok,chat_template=template)
p.save_pretrained(D)
(D/'config.json').write_text(json.dumps(dict(model_type='llava',architectures=['LlavaForConditionalGeneration'])))
print('assets',sorted(f.name for f in D.iterdir()))
from transformers import AutoProcessor
p=AutoProcessor.from_pretrained(D,local_files_only=True,trust_remote_code=False)
print(type(p).__name__,p.tokenizer.encode('<|endoftext|>'),p.tokenizer.eos_token_id)
