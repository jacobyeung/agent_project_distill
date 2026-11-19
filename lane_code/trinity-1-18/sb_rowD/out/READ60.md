# Away-row trace audit

Seed: `20261118`; Python `random.Random(seed).sample`, without replacement, from all 8,511 matching rows ordered by store index.

A separate step is a standalone trace line after the toward relation and before the derived away relation and answer. A numbered `Step 3` label is not required.

| Form | Sample | Full population |
|---|---:|---:|
| separate_half_turn_step | 60 | 8511 |
| half_turn_merged_or_out_of_order | 0 | 0 |
| keeps_toward_heading | 0 | 0 |
| no_explicit_half_turn | 0 | 0 |

All 60 complete questions, options and target traces appear below.

## Ten examples per observed form

### Sample 1: vsi590k_147870_away_opp

Store index: 199240. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the table, is the blanket to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: door in frame 1; table in frame 21; blanket in frame 14.
If I stood at the door facing the table, the blanket would be to my right.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the blanket to my left.
</think>

A
```

### Sample 2: vsi590k_039994_away_opp

Store index: 201519. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the office chair and facing in the opposite direction of the telephone, is the door to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: office chair in frame 30; telephone in frame 23; door in frame 15.
If I stood at the office chair facing the telephone, the door would be to my left.
The question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the door to my right.
</think>

A
```

### Sample 3: vsi590k_139221_away_opp

Store index: 197121. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the power strip and facing in the opposite direction of the kettle, is the heater to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: power strip in frame 16; kettle in frame 28; heater in frame 18.
If I stood at the power strip facing the kettle, the heater would be to my right.
The question has me facing in the opposite direction of the kettle. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the heater to my left.
</think>

A
```

### Sample 4: vsi590k_040606_away_opp

Store index: 196646. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the nightstand and facing in the opposite direction of the refrigerator, is the radiator to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: nightstand in frame 3; refrigerator in frame 22; radiator in frame 15.
If I stood at the nightstand facing the refrigerator, the radiator would be to my left.
The question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the radiator to my right.
</think>

B
```

### Sample 5: vsi590k_015685_away_opp

Store index: 196198. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the bookshelf and facing in the opposite direction of the couch, is the radiator to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-left | B. back-right | C. front-right | D. front-left

Answer: A

```text
<think>
Seen: bookshelf in frame 22; couch in frame 17; radiator in frame 22.
If I stood at the bookshelf facing the couch, the radiator would be in front of me, on my right.
The question has me facing in the opposite direction of the couch. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the radiator at my back-left.
</think>

A
```

### Sample 6: vsi590k_135539_away_opp

Store index: 199590. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the door, is the keyboard to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. left | C. back

Answer: B

```text
<think>
Seen: heater in frame 32; door in frame 21; keyboard in frame 8.
If I stood at the heater facing the door, the keyboard would be out to my right.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the keyboard to my left.
</think>

B
```

### Sample 7: vsi590k_232035_away_opp

Store index: 202149. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the tv and facing in the opposite direction of the stove, is the washer to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-left | B. front-left | C. back-right | D. front-right

Answer: A

```text
<think>
Seen: tv in frame 24; stove in frame 14; washer in frame 18.
If I stood at the tv facing the stove, the washer would be in front of me, on my right.
The question has me facing in the opposite direction of the stove. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the washer at my back-left.
</think>

A
```

### Sample 8: vsi590k_130001_away_opp

Store index: 201080. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the table and facing in the opposite direction of the door, is the sofa to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: A

```text
<think>
Seen: table in frame 5; door in frame 22; sofa in frame 15.
If I stood at the table facing the door, the sofa would be out to my left.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the sofa to my right.
</think>

A
```

### Sample 9: vsi590k_231870_away_opp

Store index: 204006. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the stove and facing in the opposite direction of the table, is the washer to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. front-left | B. front-right | C. back-left | D. back-right

Answer: C

```text
<think>
Seen: stove in frame 23; table in frame 14; washer in frame 18.
If I stood at the stove facing the table, the washer would be in front of me, on my right.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the washer at my back-left.
</think>

C
```

### Sample 10: vsi590k_151016_away_opp

Store index: 202840. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the sofa and facing in the opposite direction of the microwave, is the chair to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: sofa in frame 28; microwave in frame 24; chair in frame 22.
If I stood at the sofa facing the microwave, the chair would be to my left.
The question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the chair to my right.
</think>

B
```

`half_turn_merged_or_out_of_order`: no examples exist in the sample or census.

`keeps_toward_heading`: no examples exist in the sample or census.

`no_explicit_half_turn`: no examples exist in the sample or census.

## Remaining sampled rows

### Sample 11: vsi590k_245467_away_opp

Store index: 198608. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the stove and facing in the opposite direction of the table, is the refrigerator to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: B

```text
<think>
Seen: stove in frame 8; table in frame 22; refrigerator in frame 15.
If I stood at the stove facing the table, the refrigerator would be ahead of me, slightly to my right.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the refrigerator at my back.
</think>

B
```

### Sample 12: vsi590k_129061_away_opp

Store index: 199462. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the headphones, is the tv to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. right | C. left

Answer: C

```text
<think>
Seen: door in frame 25; headphones in frame 24; tv in frame 32.
If I stood at the door facing the headphones, the tv would be out to my right.
The question has me facing in the opposite direction of the headphones. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the tv to my left.
</think>

C
```

### Sample 13: vsi590k_016016_away_opp

Store index: 195958. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the nightstand and facing in the opposite direction of the tv, is the backpack to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. front-left | B. front-right | C. back-right | D. back-left

Answer: C

```text
<think>
Seen: nightstand in frame 22; tv in frame 9; backpack in frame 25.
If I stood at the nightstand facing the tv, the backpack would be in front of me, on my left.
The question has me facing in the opposite direction of the tv. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the backpack at my back-right.
</think>

C
```

### Sample 14: vsi590k_123206_away_opp

Store index: 199657. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the suitcase and facing in the opposite direction of the blanket, is the keyboard to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. left | C. right

Answer: B

```text
<think>
Seen: suitcase in frame 30; blanket in frame 28; keyboard in frame 30.
If I stood at the suitcase facing the blanket, the keyboard would be out to my right.
The question has me facing in the opposite direction of the blanket. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the keyboard to my left.
</think>

B
```

### Sample 15: vsi590k_141947_away_opp

Store index: 196778. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the toilet, is the suitcase to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: heater in frame 14; toilet in frame 17; suitcase in frame 11.
If I stood at the heater facing the toilet, the suitcase would be to my right.
The question has me facing in the opposite direction of the toilet. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the suitcase to my left.
</think>

B
```

### Sample 16: vsi590k_233461_away_opp

Store index: 201964. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the bathtub and facing in the opposite direction of the table, is the toilet to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-left | B. front-right | C. front-left | D. back-right

Answer: D

```text
<think>
Seen: bathtub in frame 4; table in frame 32; toilet in frame 8.
If I stood at the bathtub facing the table, the toilet would be in front of me, on my left.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the toilet at my back-right.
</think>

D
```

### Sample 17: vsi590k_037267_away_opp

Store index: 196005. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the bookshelf and facing in the opposite direction of the keyboard, is the telephone to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: bookshelf in frame 21; keyboard in frame 14; telephone in frame 32.
If I stood at the bookshelf facing the keyboard, the telephone would be to my left.
The question has me facing in the opposite direction of the keyboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the telephone to my right.
</think>

A
```

### Sample 18: vsi590k_116646_away_opp

Store index: 199314. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the whiteboard and facing in the opposite direction of the telephone, is the cup to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. right | C. back

Answer: C

```text
<think>
Seen: whiteboard in frame 7; telephone in frame 10; cup in frame 5.
If I stood at the whiteboard facing the telephone, the cup would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the cup at my back.
</think>

C
```

### Sample 19: vsi590k_136740_away_opp

Store index: 200414. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the rack and facing in the opposite direction of the microwave, is the pan to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: rack in frame 29; microwave in frame 25; pan in frame 19.
If I stood at the rack facing the microwave, the pan would be to my right.
The question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the pan to my left.
</think>

B
```

### Sample 20: vsi590k_118272_away_opp

Store index: 201727. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the laptop and facing in the opposite direction of the door, is the coat hanger to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: B

```text
<think>
Seen: laptop in frame 16; door in frame 31; coat hanger in frame 12.
If I stood at the laptop facing the door, the coat hanger would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the coat hanger at my back.
</think>

B
```

### Sample 21: vsi590k_131189_away_opp

Store index: 197482. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the trash can, is the shoes to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. back | C. right

Answer: B

```text
<think>
Seen: heater in frame 27; trash can in frame 1; shoes in frame 12.
If I stood at the heater facing the trash can, the shoes would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the shoes at my back.
</think>

B
```

### Sample 22: vsi590k_140376_away_opp

Store index: 204393. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the keyboard and facing in the opposite direction of the printer, is the monitor to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: keyboard in frame 10; printer in frame 10; monitor in frame 19.
If I stood at the keyboard facing the printer, the monitor would be to my right.
The question has me facing in the opposite direction of the printer. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the monitor to my left.
</think>

B
```

### Sample 23: vsi590k_023346_away_opp

Store index: 199316. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the trash can, is the plant to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. right | C. back

Answer: B

```text
<think>
Seen: door in frame 3; trash can in frame 17; plant in frame 4.
If I stood at the door facing the trash can, the plant would be behind me, on my left.
The question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the plant to my right.
</think>

B
```

### Sample 24: vsi590k_153780_away_opp

Store index: 202295. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the basket and facing in the opposite direction of the ceiling lamp, is the heater to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: basket in frame 1; ceiling lamp in frame 29; heater in frame 25.
If I stood at the basket facing the ceiling lamp, the heater would be to my left.
The question has me facing in the opposite direction of the ceiling lamp. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the heater to my right.
</think>

A
```

### Sample 25: vsi590k_038297_away_opp

Store index: 198263. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the couch and facing in the opposite direction of the mirror, is the door to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: couch in frame 7; mirror in frame 30; door in frame 30.
If I stood at the couch facing the mirror, the door would be to my left.
The question has me facing in the opposite direction of the mirror. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the door to my right.
</think>

B
```

### Sample 26: vsi590k_242463_away_opp

Store index: 199416. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the bathtub and facing in the opposite direction of the stool, is the bed to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: A

```text
<think>
Seen: bathtub in frame 20; stool in frame 28; bed in frame 23.
If I stood at the bathtub facing the stool, the bed would be out to my left.
The question has me facing in the opposite direction of the stool. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bed to my right.
</think>

A
```

### Sample 27: vsi590k_128129_away_opp

Store index: 199700. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the shoes and facing in the opposite direction of the laptop, is the trash can to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. right | C. left

Answer: A

```text
<think>
Seen: shoes in frame 4; laptop in frame 14; trash can in frame 13.
If I stood at the shoes facing the laptop, the trash can would be ahead of me, slightly to my right.
The question has me facing in the opposite direction of the laptop. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the trash can at my back.
</think>

A
```

### Sample 28: vsi590k_124317_away_opp

Store index: 197656. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the cutting board and facing in the opposite direction of the refrigerator, is the power strip to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. right | C. left

Answer: C

```text
<think>
Seen: cutting board in frame 22; refrigerator in frame 20; power strip in frame 19.
If I stood at the cutting board facing the refrigerator, the power strip would be out to my right.
The question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the power strip to my left.
</think>

C
```

### Sample 29: vsi590k_030986_away_opp

Store index: 203997. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the radiator and facing in the opposite direction of the couch, is the trash can to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: radiator in frame 14; couch in frame 7; trash can in frame 23.
If I stood at the radiator facing the couch, the trash can would be to my right.
The question has me facing in the opposite direction of the couch. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the trash can to my left.
</think>

B
```

### Sample 30: vsi590k_138039_away_opp

Store index: 202900. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the whiteboard and facing in the opposite direction of the printer, is the heater to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: whiteboard in frame 24; printer in frame 21; heater in frame 11.
If I stood at the whiteboard facing the printer, the heater would be to my right.
The question has me facing in the opposite direction of the printer. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the heater to my left.
</think>

A
```

### Sample 31: vsi590k_152751_away_opp

Store index: 199443. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the telephone and facing in the opposite direction of the cup, is the whiteboard to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: telephone in frame 26; cup in frame 8; whiteboard in frame 17.
If I stood at the telephone facing the cup, the whiteboard would be to my right.
The question has me facing in the opposite direction of the cup. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the whiteboard to my left.
</think>

B
```

### Sample 32: vsi590k_241457_away_opp

Store index: 196741. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the toilet and facing in the opposite direction of the bathtub, is the stool to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. left | C. back

Answer: A

```text
<think>
Seen: toilet in frame 25; bathtub in frame 5; stool in frame 16.
If I stood at the toilet facing the bathtub, the stool would be out to my left.
The question has me facing in the opposite direction of the bathtub. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the stool to my right.
</think>

A
```

### Sample 33: vsi590k_117484_away_opp

Store index: 203518. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the paper bag and facing in the opposite direction of the refrigerator, is the bucket to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: B

```text
<think>
Seen: paper bag in frame 5; refrigerator in frame 9; bucket in frame 15.
If I stood at the paper bag facing the refrigerator, the bucket would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bucket at my back.
</think>

B
```

### Sample 34: vsi590k_138321_away_opp

Store index: 198859. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the computer tower and facing in the opposite direction of the door, is the bookshelf to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: computer tower in frame 29; door in frame 5; bookshelf in frame 10.
If I stood at the computer tower facing the door, the bookshelf would be to my right.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bookshelf to my left.
</think>

B
```

### Sample 35: vsi590k_092185_away_opp

Store index: 200087. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the blanket and facing in the opposite direction of the whiteboard, is the bowl to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. front-right | B. front-left | C. back-left | D. back-right

Answer: D

```text
<think>
Seen: blanket in frame 17; whiteboard in frame 29; bowl in frame 27.
If I stood at the blanket facing the whiteboard, the bowl would be in front of me, on my left.
The question has me facing in the opposite direction of the whiteboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the bowl at my back-right.
</think>

D
```

### Sample 36: vsi590k_145696_away_opp

Store index: 198412. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the heater and facing in the opposite direction of the paper bag, is the monitor to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: heater in frame 28; paper bag in frame 10; monitor in frame 27.
If I stood at the heater facing the paper bag, the monitor would be to my right.
The question has me facing in the opposite direction of the paper bag. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the monitor to my left.
</think>

B
```

### Sample 37: vsi590k_035469_away_opp

Store index: 202481. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the office chair and facing in the opposite direction of the lamp, is the bookshelf to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: office chair in frame 4; lamp in frame 17; bookshelf in frame 11.
If I stood at the office chair facing the lamp, the bookshelf would be to my left.
The question has me facing in the opposite direction of the lamp. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bookshelf to my right.
</think>

A
```

### Sample 38: vsi590k_021443_away_opp

Store index: 202059. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the backpack, is the tv to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. left | C. back

Answer: C

```text
<think>
Seen: door in frame 28; backpack in frame 4; tv in frame 2.
If I stood at the door facing the backpack, the tv would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the backpack. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the tv at my back.
</think>

C
```

### Sample 39: vsi590k_138884_away_opp

Store index: 201764. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the toilet and facing in the opposite direction of the bed, is the kettle to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: toilet in frame 5; bed in frame 22; kettle in frame 9.
If I stood at the toilet facing the bed, the kettle would be to my left.
The question has me facing in the opposite direction of the bed. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the kettle to my right.
</think>

A
```

### Sample 40: vsi590k_142519_away_opp

Store index: 196842. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the microwave, is the table to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: door in frame 11; microwave in frame 7; table in frame 16.
If I stood at the door facing the microwave, the table would be to my left.
The question has me facing in the opposite direction of the microwave. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the table to my right.
</think>

A
```

### Sample 41: vsi590k_149209_away_opp

Store index: 196936. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the office chair and facing in the opposite direction of the bed, is the bookshelf to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: office chair in frame 15; bed in frame 10; bookshelf in frame 29.
If I stood at the office chair facing the bed, the bookshelf would be to my left.
The question has me facing in the opposite direction of the bed. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bookshelf to my right.
</think>

B
```

### Sample 42: vsi590k_123463_away_opp

Store index: 200747. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the whiteboard and facing in the opposite direction of the mouse, is the ceiling lamp to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. left | C. right

Answer: A

```text
<think>
Seen: whiteboard in frame 9; mouse in frame 11; ceiling lamp in frame 16.
If I stood at the whiteboard facing the mouse, the ceiling lamp would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the mouse. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the ceiling lamp at my back.
</think>

A
```

### Sample 43: vsi590k_123900_away_opp

Store index: 201509. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the table and facing in the opposite direction of the trash can, is the ceiling lamp to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. back | C. right

Answer: B

```text
<think>
Seen: table in frame 22; trash can in frame 29; ceiling lamp in frame 1.
If I stood at the table facing the trash can, the ceiling lamp would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the trash can. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the ceiling lamp at my back.
</think>

B
```

### Sample 44: vsi590k_127199_away_opp

Store index: 202074. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the trash can and facing in the opposite direction of the chair, is the laptop to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. left | C. back

Answer: C

```text
<think>
Seen: trash can in frame 17; chair in frame 16; laptop in frame 13.
If I stood at the trash can facing the chair, the laptop would be ahead of me, slightly to my right.
The question has me facing in the opposite direction of the chair. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the laptop at my back.
</think>

C
```

### Sample 45: vsi590k_244250_away_opp

Store index: 198454. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the dishwasher and facing in the opposite direction of the refrigerator, is the chair to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: C

```text
<think>
Seen: dishwasher in frame 15; refrigerator in frame 24; chair in frame 15.
If I stood at the dishwasher facing the refrigerator, the chair would be out to my right.
The question has me facing in the opposite direction of the refrigerator. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the chair to my left.
</think>

C
```

### Sample 46: vsi590k_233000_away_opp

Store index: 202428. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the refrigerator and facing in the opposite direction of the dishwasher, is the table to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. front-left | B. back-left | C. front-right | D. back-right

Answer: A

```text
<think>
Seen: refrigerator in frame 8; dishwasher in frame 10; table in frame 22.
If I stood at the refrigerator facing the dishwasher, the table would be behind me, on my right.
The question has me facing in the opposite direction of the dishwasher. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the table at my front-left.
</think>

A
```

### Sample 47: vsi590k_250944_away_opp

Store index: 200319. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the refrigerator and facing in the opposite direction of the stove, is the table to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: refrigerator in frame 19; stove in frame 25; table in frame 9.
If I stood at the refrigerator facing the stove, the table would be to my right.
The question has me facing in the opposite direction of the stove. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the table to my left.
</think>

A
```

### Sample 48: vsi590k_037826_away_opp

Store index: 201421. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the refrigerator and facing in the opposite direction of the bed, is the microwave to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: refrigerator in frame 23; bed in frame 9; microwave in frame 21.
If I stood at the refrigerator facing the bed, the microwave would be to my right.
The question has me facing in the opposite direction of the bed. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the microwave to my left.
</think>

A
```

### Sample 49: vsi590k_242644_away_opp

Store index: 197717. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the stool and facing in the opposite direction of the stove, is the sofa to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. left | C. right

Answer: C

```text
<think>
Seen: stool in frame 10; stove in frame 25; sofa in frame 6.
If I stood at the stool facing the stove, the sofa would be out to my left.
The question has me facing in the opposite direction of the stove. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the sofa to my right.
</think>

C
```

### Sample 50: vsi590k_143545_away_opp

Store index: 199120. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the table and facing in the opposite direction of the door, is the trash can to my left or to my right?

Options: A. left | B. right

Answer: A

```text
<think>
Seen: table in frame 22; door in frame 28; trash can in frame 29.
If I stood at the table facing the door, the trash can would be to my right.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the trash can to my left.
</think>

A
```

### Sample 51: vsi590k_121464_away_opp

Store index: 200423. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the telephone and facing in the opposite direction of the power strip, is the coat hanger to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. back | C. right

Answer: C

```text
<think>
Seen: telephone in frame 13; power strip in frame 19; coat hanger in frame 29.
If I stood at the telephone facing the power strip, the coat hanger would be out to my left.
The question has me facing in the opposite direction of the power strip. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the coat hanger to my right.
</think>

C
```

### Sample 52: vsi590k_095677_away_opp

Store index: 203012. Family: object_rel_direction_hard. Form: separate_half_turn_step.

Question: If I am standing by the table lamp and facing in the opposite direction of the heater, is the door to my front-left, front-right, back-left, or back-right?
The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).

Options: A. back-right | B. front-left | C. front-right | D. back-left

Answer: C

```text
<think>
Seen: table lamp in frame 13; heater in frame 14; door in frame 32.
If I stood at the table lamp facing the heater, the door would be behind me, on my left.
The question has me facing in the opposite direction of the heater. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the door at my front-right.
</think>

C
```

### Sample 53: vsi590k_145065_away_opp

Store index: 203628. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the monitor and facing in the opposite direction of the door, is the cup to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: monitor in frame 14; door in frame 27; cup in frame 24.
If I stood at the monitor facing the door, the cup would be to my left.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the cup to my right.
</think>

B
```

### Sample 54: vsi590k_131598_away_opp

Store index: 198322. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the door and facing in the opposite direction of the laptop, is the pillow to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. right | C. back

Answer: C

```text
<think>
Seen: door in frame 25; laptop in frame 18; pillow in frame 11.
If I stood at the door facing the laptop, the pillow would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the laptop. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the pillow at my back.
</think>

C
```

### Sample 55: vsi590k_129311_away_opp

Store index: 198379. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the bed and facing in the opposite direction of the monitor, is the microwave to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. right | B. back | C. left

Answer: B

```text
<think>
Seen: bed in frame 12; monitor in frame 16; microwave in frame 20.
If I stood at the bed facing the monitor, the microwave would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the monitor. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the microwave at my back.
</think>

B
```

### Sample 56: vsi590k_154757_away_opp

Store index: 196979. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the trash can and facing in the opposite direction of the whiteboard, is the door to my left or to my right?

Options: A. left | B. right

Answer: B

```text
<think>
Seen: trash can in frame 15; whiteboard in frame 30; door in frame 13.
If I stood at the trash can facing the whiteboard, the door would be to my left.
The question has me facing in the opposite direction of the whiteboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the door to my right.
</think>

B
```

### Sample 57: vsi590k_136659_away_opp

Store index: 199861. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the shoes and facing in the opposite direction of the laptop, is the kettle to my left or to my right?

Options: A. right | B. left

Answer: B

```text
<think>
Seen: shoes in frame 12; laptop in frame 31; kettle in frame 30.
If I stood at the shoes facing the laptop, the kettle would be to my right.
The question has me facing in the opposite direction of the laptop. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the kettle to my left.
</think>

B
```

### Sample 58: vsi590k_116022_away_opp

Store index: 202094. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the telephone and facing in the opposite direction of the door, is the whiteboard to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. back | B. left | C. right

Answer: C

```text
<think>
Seen: telephone in frame 18; door in frame 11; whiteboard in frame 28.
If I stood at the telephone facing the door, the whiteboard would be out to my left.
The question has me facing in the opposite direction of the door. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the whiteboard to my right.
</think>

C
```

### Sample 59: vsi590k_243357_away_opp

Store index: 203542. Family: object_rel_direction_medium. Form: separate_half_turn_step.

Question: If I am standing by the sofa and facing in the opposite direction of the tv, is the refrigerator to my left, right, or back?
An object is to my back if I would have to turn at least 135 degrees in order to face it.

Options: A. left | B. right | C. back

Answer: B

```text
<think>
Seen: sofa in frame 12; tv in frame 26; refrigerator in frame 23.
If I stood at the sofa facing the tv, the refrigerator would be out to my left.
The question has me facing in the opposite direction of the tv. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the refrigerator to my right.
</think>

B
```

### Sample 60: vsi590k_250687_away_opp

Store index: 202684. Family: object_rel_direction_easy. Form: separate_half_turn_step.

Question: If I am standing by the bed and facing in the opposite direction of the sofa, is the chair to my left or to my right?

Options: A. right | B. left

Answer: A

```text
<think>
Seen: bed in frame 20; sofa in frame 29; chair in frame 8.
If I stood at the bed facing the sofa, the chair would be to my left.
The question has me facing in the opposite direction of the sofa. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the chair to my right.
</think>

A
```

