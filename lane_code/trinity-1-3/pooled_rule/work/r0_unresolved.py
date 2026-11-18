"""For the scene aliases of store v7 that no alias map resolves: is each alias tied to the kit07 frame map (17aa3e9e),
an authority the R0 census removed room by room?  Appends the answer to R0_EXPOSURE_V7.json."""
import json, sqlite3, collections
d = json.load(open('R0_EXPOSURE_V7.json'))
un = set(d['unresolved_alias_list'])
con = sqlite3.connect('file:%s?mode=ro' % d['store'], uri=True)
FM = '17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3'
tied = collections.defaultdict(collections.Counter)
for (raw,) in con.execute('select row from rows'):
    r = json.loads(raw)
    alias = str(r.get('dataset')) + '/' + str(r.get('scene'))
    if alias in un:
        pv = r.get('provenance') or {}
        tied[alias]['kit07_frame_map' if pv.get('frame_map_sha256') == FM else 'no_frame_map:' + str(r.get('pool'))] += 1
with_map = sorted(a for a in un if tied[a]['kit07_frame_map'] > 0)
without = {a: dict(tied[a]) for a in sorted(un) if tied[a]['kit07_frame_map'] == 0}
d['unresolved_alias_tie'] = dict(frame_map_sha256=FM, aliases_with_a_row_on_the_frame_map=len(with_map),
                                 aliases_without=without,
                                 rows_on_aliases_without=sum(sum(v.values()) for v in without.values()))
json.dump(d, open('R0_EXPOSURE_V7.json', 'w'), indent=1)
print(json.dumps(d['unresolved_alias_tie']))
