import sys; sys.path.insert(0,'/scratch/jjyeung/orch_n30/rows_rebuild3/work/validator'); import trace_grammar as g
def T(q,body,ans,qt='object_counting',opts=()):
    r=dict(question_type=qt,answer=ans,target=f'<think>\n{body}\n</think>\n\n{ans}',student_input=dict(question=q,options=list(opts),frame_indices=list(range(32))))
    e=g.validate_row(r); print('PASS' if not e else [(x.rule_id,x.line,x.detail) for x in e]); 
q='How many chair(s) do we have in this room?'
T(q,'Step 1: list each distinct chair once, by the frame where it first appears: frame 3 (left); frame 3 (right); frame 9 (middle).\nSo there are 3 chairs.','3')
T(q,'Step 1: list each distinct chair once, by the frame where it first appears: frame 3, left; frame 3, right; frame 9, center.\nSo there are 3 chairs.','3')
T(q,'Step 1: the first chair is first seen in frame 3, at the left.\nStep 2: the second chair is first seen in frame 3, at the right.\nStep 3: the third chair is first seen in frame 9.\nSo there are 3 chairs.','3')
T(q,'Locate: the first chair, frame 3, left.\nLocate: the second chair, frame 3, right.\nLocate: the third chair, frame 9, center.\nSo the count is 3.','3')
T(q,'Step 1: chair 1 is first seen in frame 3, on the left.\nStep 2: chair 2 is first seen in frame 3, on the right.\nStep 3: chair 3 is first seen in frame 9.\nStep 4: that lists 3 distinct chairs.\nSo there are 3 chairs.','3')
T('In which frame does the sofa first appear?','Step 1: the sofa is first seen in frame 7, on the left.','7','first_seen_frame')
T('In which frame does the sofa first appear?','Step 1: the sofa first appears in frame 7.','7','first_seen_frame')
print('--- long lists / totals / appearance')
ords='first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth'.split()
T(q,'\n'.join(f'Locate: the {o} chair, frame {i+1}.' for i,o in enumerate(ords))+'\nSo the count is 12.','12')
T(q,'Step 1: list each distinct chair once, by the frame where it first appears: '+'; '.join(f'frame {i+1} (left)' for i in range(12))+'.\nSo the count is 12.','12')
T('What is the total number of backpack(s) and desk(s) in this room?','Step 1: find each distinct backpack, using its first-seen frame: frame 1 (left).\nStep 2: list the distinct desk instances by first appearance: frame 4 (middle); frame 5 (right).\nStep 3: add them: 1 + 2 = 3.\nSo there are 3 in total.','3')
T('What will be the first-time appearance order of the following categories in the video: bed, chair, lamp, sofa?','Step 1: find the first frame showing each object: bed frame 8; chair frame 3; lamp frame 18; sofa frame 14.\nStep 2: order them by first appearance: chair, bed, sofa, lamp.','A','obj_appearance_order',['A. chair, bed, sofa, lamp','B. bed, chair, sofa, lamp','C. lamp, bed, sofa, chair','D. sofa, lamp, chair, bed'])
T('In which frame does a chair first appear?','Step 1: a chair is first seen in frame 7 (middle).','7','first_seen_frame')
