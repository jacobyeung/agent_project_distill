"""Budget contexts are built from source journals and verified receipts, never row flags."""
from copy import deepcopy
from budget import CLOSE, classify, generated_ids, validate_source
from evalpath.items import digest
from scoring import score_item
from token_audit import token_ids, prefix_score, check_score

POLICY = dict(answer_cap=64, answer_cap_policy='continuation_64; reuse_full_on_answer')
FLAGS=('forced_close','stopped_unclosed','think_tokens','answer_tokens','derivation_error')


class BudgetContext:
    def __init__(self, cfg, cell_index, budget, tokenizer):
        self.cfg,self.cell_index,self.budget,self.tokenizer=cfg,cell_index,budget,tokenizer
        self.arm_binding=digest(dict(request=cfg['binding'],cell=cell_index,budget=budget))
        self.merge_binding=digest(dict(request=self.arm_binding,cell=cell_index))
        self.rows={}

    def add(self, source, row, raw, receipt, task):
        from merge import check_row
        cell=self.cfg['cells'][self.cell_index]
        source_binding=digest(dict(request=self.cfg['binding'],cell=self.cell_index))
        validate_source(source,cell,source_binding)
        check_row(source,task,32,cell)
        prefix_score(source,task,cell,self.tokenizer)
        ids=token_ids(source,self.tokenizer)
        key=source['key']
        if row['key']!=key or receipt.get('source_key')!=key or receipt.get('key')!=key+':'+digest(raw):
            raise ValueError('Budget attribution differs')
        if receipt.get('binding')!=self.arm_binding or receipt.get('source_sha256')!=digest(source) or receipt.get('record_sha256')!=digest(raw):
            raise ValueError('Budget receipt binding/hash differs')
        if receipt.get('budget')!=self.budget or receipt.get('arm')!=f'B{self.budget}':
            raise ValueError('Budget receipt arm differs')
        classification=classify(self.tokenizer,ids,self.budget)
        if any(receipt.get(k)!=v for k,v in classification.items()):
            raise ValueError('Budget classification differs from source prefix')
        if any(row.get(k)!=source.get(k) for k in ('media','benchmark','example_id','question_type','model','decoding','thinking','frames','layout')):
            raise ValueError('Budget source/task metadata differs')
        error=receipt.get('derivation_error') is True
        reuse=not classification['forced_close'] and not classification['stopped_unclosed'] and not error
        if reuse:
            if row!=source:
                raise ValueError('Reused ON row must be unchanged')
            answer_tokens=len(ids)-classification['think_tokens']-1
            if receipt.get('answer_cap_policy')!='reuse_full_on_answer':
                raise ValueError('Budget reuse must declare full-answer exception')
            text,cap,finish=source['raw_generation'],cell['max_tokens'],source['finish_reason']
            short=prefix_score(source,task,cell,self.tokenizer)
        elif error:
            if row.get('binding')!=self.arm_binding or not row.get('derivation_error'):
                raise ValueError('Budget error binding differs')
            if row.get('raw_generation')!='' or row.get('token_ids')!=[] or row.get('finish_reason')!='error':
                raise ValueError('Budget error must be unanswered')
            text,cap,finish='',64,'error'
            answer_tokens=receipt.get('answer_tokens')
            short=row['at_4096']
            if short!={k:row[k] for k in ('raw_generation','response_text','score','extracted_answer','extract_branch','parse_failed','empty_think','hit_token_cap','output_tokens','max_new_tokens')}:
                raise ValueError('Budget error prefix differs')
        else:
            if row.get('binding')!=self.arm_binding or row.get('budget')!=self.budget or row.get('source_key')!=key:
                raise ValueError('Budget continuation binding differs')
            answer_ids=token_ids(row,self.tokenizer)
            answer_tokens=len(answer_ids)
            if answer_tokens>64 or receipt.get('answer_cap_policy')!='continuation_64':
                raise ValueError('Budget continuation cap differs')
            if row.get('continuation_suffix_ids')!=self.tokenizer.encode(CLOSE,add_special_tokens=False):
                raise ValueError('Budget forced close differs')
            text=self.tokenizer.decode(ids[:self.budget],skip_special_tokens=False)+CLOSE+row['raw_generation']
            if row.get('scoring_text')!=text or row.get('raw_answer')!=row['raw_generation']:
                raise ValueError('Budget reconstructed scoring text differs')
            cap,finish=64,row['finish_reason']
            short=dict(raw_generation=text,**score_item(dict(task,thinking=True),text,answer_tokens,cap=64,finish=finish))
            if row.get('at_4096')!=short:
                raise ValueError('Budget prefix/diagnostics differ')
        if receipt.get('answer_tokens')!=answer_tokens:
            raise ValueError('Budget answer token count differs')
        if any(receipt.get(k)!=row.get(k) for k in ('score','parse_failed')):
            raise ValueError('Budget receipt score differs')
        projected=dict(row,binding=self.merge_binding,budget=self.budget,arm=f'B{self.budget}')
        for name in FLAGS:
            projected[name]=receipt[name]
        if key in self.rows and self.rows[key][0]!=projected:
            raise ValueError('Conflicting complete rows: '+key)
        self.rows[key]=(deepcopy(projected),text,cap,finish,deepcopy(short))
        # Run the same full-score/diagnostic validation as ordinary merge.
        check_row(projected,task,32,cell,budget_context=self)
        return projected

    def scoring(self,row,task,cell):
        item=self.rows.get(row['key'])
        if item is None or row!=item[0] or cell!=self.cfg['cells'][self.cell_index]:
            raise ValueError('Row differs from authenticated budget context')
        return item[1:4]

    def prefix(self,row,task,cell):
        self.scoring(row,task,cell)
        return self.rows[row['key']][4]

    def error_score(self,row,scored):
        self.scoring(row,None,self.cfg['cells'][self.cell_index])
        return dict(scored,extract_branch='derivation_error',empty_think=row['think_tokens']==0)
