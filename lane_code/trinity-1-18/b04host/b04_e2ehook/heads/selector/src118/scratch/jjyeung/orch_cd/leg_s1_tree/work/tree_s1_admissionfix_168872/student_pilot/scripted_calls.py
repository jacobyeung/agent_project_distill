"""Reference token choice only; responses always enter through the routed decoder."""
import re

GROUND = re.compile(r'<ground obj="([^"<>\x00-\x1f]+)"( mode="box")?>')
GAP = re.compile(r'<gap a="([^"<>\x00-\x1f]+)"((?: b="[^"<>\x00-\x1f]+")+) rule="sampled_box_512">')
ANGLE = re.compile(r'<angle S=P1 F=P2 Q=P3 rule=(medium|hard)>')


def validate_reference(ref):
    if isinstance(ref, dict) and ref.get('schema') == 'addressing-call-v1':
        segments = ref.get('segments')
        if (ref.get('free_answer') is not True or not isinstance(segments, list) or len(segments) != 1):
            raise ValueError('addressing reference requires exactly one ground and a free answer')
        segment = segments[0]
        match = GROUND.fullmatch(segment['call'])
        if (not match or match[2] or match[1] != ref.get('name') or
                segment['text'] != '<think>\n' + segment['call']):
            raise ValueError('addressing reference must ground the exact requested name')
        return segments
    if not isinstance(ref, dict) or ref.get('schema') != 'scripted-calls-v1' or ref.get('free_answer') is not True:
        raise ValueError('reference_trace: expected scripted-calls-v1 with free_answer=true')
    segments = ref.get('segments')
    if not isinstance(segments, list) or not 3 <= len(segments) <= 16:
        raise ValueError('reference_trace.segments: expected 3..16 complete call segments')
    names=[];boxed=None
    for i, seg in enumerate(segments):
        text,call=seg['text'],seg['call']
        if not isinstance(text,str) or not text.endswith(call) or len(text)>4000:
            raise ValueError('reference_trace: segment must end at its complete call')
        prefix=text[:-len(call)]
        if i==0:
            if not prefix.startswith('<think>\n'):raise ValueError('reference_trace: missing think prefix')
            prefix=prefix[len('<think>\n'):]
        if re.search(r'<[/A-Za-z_]',prefix):
            raise ValueError('reference_trace: hidden call, response or answer in prefix')
        if (m:=GROUND.fullmatch(call)):
            if i==len(segments)-1 or m[1] in names or m[1]!=m[1].strip():raise ValueError('reference_trace: invalid ground order/name')
            if boxed is not None and boxed!=bool(m[2]):raise ValueError('reference_trace: mixed point and box grounds')
            boxed=bool(m[2]);names.append(m[1])
        elif (m:=GAP.fullmatch(call)):
            operands=[m[1],*re.findall(r' b="([^"]+)"',m[2])]
            if i!=len(segments)-1 or not boxed or operands!=names:raise ValueError('reference_trace: gap operands must match preceding grounds in order')
        elif ANGLE.fullmatch(call):
            if i!=len(segments)-1 or boxed or len(names)!=3:raise ValueError('reference_trace: angle needs exactly three point grounds')
        else:raise ValueError('reference_trace: malformed/unsupported call '+str(call))
    if GROUND.fullmatch(segments[-1]['call']):raise ValueError('reference_trace: missing terminal measurement')
    return segments


class ReferenceChoice:
    """Wait for each intercepted live response before emitting the next segment."""
    def __init__(self, ref, tokenizer):
        segments=validate_reference(ref)
        self.calls=[s['call'] for s in segments]
        self.tokens=[tokenizer.encode(s['text'],add_special_tokens=False) for s in segments]
        for seg,tokens in zip(segments,self.tokens):
            if not tokens or tokenizer.decode(tokens,skip_special_tokens=False)!=seg['text']:
                raise ValueError('reference_trace: tokenizer cannot preserve reference bytes')
            if len(tokenizer.encode(seg['call'],add_special_tokens=False))>96:
                raise ValueError('reference_trace: call exceeds interception window')
        self.segment=self.offset=0
        self.forced_tokens=0

    def choose(self, records, logits):
        if self.segment and len(records)<self.segment:
            raise ValueError('reference_trace: call was not intercepted; forcing cannot skip it')
        if [r['call'] for r in records[:self.segment]]!=self.calls[:self.segment]:
            raise ValueError('reference_trace: intercepted call sequence differs')
        if self.segment==len(self.tokens):return int(logits.argmax(-1))
        token=self.tokens[self.segment][self.offset];self.offset+=1;self.forced_tokens+=1
        if self.offset==len(self.tokens[self.segment]):self.segment+=1;self.offset=0
        return token

    def check_complete(self,record):
        if self.segment!=len(self.tokens) or self.offset or [r['call'] for r in record['calls'][:len(self.calls)]]!=self.calls:
            raise ValueError('reference_trace: decoding stopped before every scripted call was answered')
        return dict(mode='scripted',reference_calls=len(self.calls),forced_choice_tokens=self.forced_tokens,
                    learned_routing='unmeasured',free_answer_eos=record['finish']=='eos')
