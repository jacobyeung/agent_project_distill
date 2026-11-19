"""Record the agent's completed READ30 review; this script is not an automated prose judge."""
import json,re
from pathlib import Path
from stage_inputs import sha
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
# These observations were written after reading all thirty complete human-facing renderings.
OBSERVATIONS=[
('sb_rowB4_5dcea2bde044c64d11313ab5','C','All four objects are visible; coffee table is nearest.'),
('sb_rowB4_16e202bcc5e8a3d758fcdfb5','B','All four are out of view at 20; the cited past frames precede 20, and dishwasher is nearest.'),
('sb_rowB4_c639ad13c5cfa7ead219c2fa','B','Trash can first appears at 19 after 6; telephone has a past citation; table is nearest.'),
('sb_rowB4_d20f648832cd13d94dafa67f','A','Stool has a past sighting at 2; cabinet, fireplace, and tv have first appearances after 3; stool is nearest.'),
('sb_rowB4_7409f2e247a8635e47a00bca','C','Bookshelf and heater have past sightings; bookshelf is nearest despite being out of view at 28.'),
('sb_rowB4_86329c289c27acd971bd1b7d','C','All three are visible at 2; sink is nearest.'),
('sb_rowB4_a28286f1ba62953449ba510d','A','At frame 1 all citations are future first appearances; bathtub is nearest.'),
('sb_rowB4_e0bb7106752a8d309aadeab3','C','Refrigerator is visible and nearest; tv and shelf have past citations.'),
('sb_rowB4_8cd6332059dcb6359307a731','A','All first appearances follow frame 2; shelf is nearest.'),
('sb_rowB4_e768baf2c1464f62c36a10a2','B','Doorframe is visible; mug and cpu have past sightings; mug is nearest.'),
('sb_rowB4_29d39a358b82bae1414e4568','B','Both objects are visible; chair is nearer than tv.'),
('sb_rowB4_14fd38e13f8c53bb177974f7','A','Both objects first appear after frame 1; sofa is nearer than chair.'),
('sb_rowB4_eb85ca9abe2460f0ba214230','B','Box was last seen at 1; lamp is visible at 3 and nearer.'),
('sb_rowB4_61f5b9504d73e0cef48c6795','A','At 23, shoe rack cites past frame 14 and cupboard first appears at 24; shoe rack is nearer.'),
('sb_rowB4_68c9ba25c73f2d96089174e5','A','Both citations precede frame 28; tv is nearer than toilet.'),
('sb_rowB4_eee03d5080a07af7f0bced2b','A','Toilet bearing is smaller than bathtub bearing; both are visible; Left matches option A.'),
('sb_rowB4_7e69c5818def001606cb6003','B','Cabinet bearing is greater than toilet bearing; both cite frame 10 before 17; Right matches B.'),
('sb_rowB4_c57ae2ca26eed9c423f0776b','A','Tv is right of office chair; office chair first appears at 18 after 16; Right matches A.'),
('sb_rowB4_f43c1e46a59ef4ad1dd59d46','B','Cabinet is left of bed; both first appear after frame 1; Left matches B.'),
('sb_rowB4_be302dbd932f442db12cab8e','A','Stove is right of refrigerator; citations 26 and 13 precede 28; Right matches A.'),
('sb_rowB4_4173c01a6b7f7f80b4edd042','B','Both are visible; fireplace has the shorter closest-point distance; Near matches B.'),
('sb_rowB4_7d898b8791f672a82113e031','B','Both are out of view at 31 with past citations; bathtub is nearer; Near matches B.'),
('sb_rowB4_31afd5a6e6692c5429b3023e','A','Bathtub has the greater distance and cites 26 before 29; cabinet is visible; Far matches A.'),
('sb_rowB4_b1e6093ce4488f5553915d1f','B','Shelf first appears at 26 after 4; shelf is nearer than the visible tv; Near matches B.'),
('sb_rowB4_f3fb9bdfc0195367edcbacb1','A','Dishwasher was last seen at 4 and is farther than visible tv at 22; Far matches A.'),
('sb_rowB4_a0437124bc8f0c192712fbab','B','Both objects are visible at frame 32; cabinet height is lower than sink; Down matches B.'),
('sb_rowB4_2f1a5726b0731e07e0379e4f','B','Past citations 6 and 14 precede 19; table height is lower than shelf; Down matches B.'),
('sb_rowB4_e5e98ea86ff63423c8cb82bc','A','Fireplace is visible and lower than tv; tv cites frame 11 before 12; Down matches A.'),
('sb_rowB4_c88299cb1a1c068ceb779830','B','Both first appearances follow frame 7; table height is lower than stove; Down matches B.'),
('sb_rowB4_36b8751dc42a0a3ab7b9753a','B','Tv is higher than table; both sightings precede frame 22; Up matches B.'),
]
def main():
    sample=json.loads((OUT/'SAMPLE_SELECTION.json').read_text());ind=json.loads((OUT/'INDEPENDENT_CHECK.json').read_text())
    rows={r['qid']:r for r in map(json.loads,(OUT/'rows.jsonl').read_text().splitlines())}
    selected=[q for rr in sample['selection'].values() for q in rr]
    assert selected==[q for q,a,n in OBSERVATIONS] and len(set(selected))==30
    assert ind['status']=='PASS' and ind['false_citations']==0
    text=(OUT/'READ30.md').read_text();serialized=re.findall(r'```json\n(.*?)\n```',text,re.S)
    assert [json.loads(s) for s in serialized]==[rows[q] for q in selected]
    for q,answer,note in OBSERVATIONS:
        r=rows[q];assert r['answer']==answer and r['target'] in text and r['student_input']['question'] in text
    result=dict(status='PASS',input_sha256={str(p):sha(p) for p in [Path(__file__),OUT/'READ30.md',OUT/'rows.jsonl',OUT/'SAMPLE_SELECTION.json',OUT/'INDEPENDENT_CHECK.json']},
      reviewer='Codex /root, sb_rowB4',reviewed_qids=selected,reviewed_rows=30,
      scope='The agent read all thirty complete questions, options, traces, and answers, plus their visibility evidence and geometry_values. Full serialized rows are printed in READ30.md and checked mechanically; independent raster verification covers every sampled row.',
      grammar='PASS: frame references and object antecedents are clear, future sightings explicitly follow k, relations agree with option semantics, and the final letter selects the stated answer. Source question templates and relation phrasing remain unchanged.',
      observations=[dict(qid=q,answer=a,note=n) for q,a,n in OBSERVATIONS])
    (OUT/'READ30_REVIEW.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (ROOT/'STATUS.md').write_text('All thirty new sample rows have been read for grammar and correctness, and their complete serialized rows match READ30.md. Independent checks pass on all 8,050 rows with zero false citations. N’s gate admits every row. Final report and archive sealing remain.\n')
    print('READ30 review recorded: PASS, 30 new sources')
if __name__=='__main__':main()
