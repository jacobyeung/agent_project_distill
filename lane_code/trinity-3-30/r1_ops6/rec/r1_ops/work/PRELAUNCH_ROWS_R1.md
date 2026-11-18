# PRELAUNCH_ROWS_R1, VQA part (store v7 rows.sqlite sha256 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443; byte-equal to Orchard okh7/s_22b44165/d.db)
Five rows per question type, drawn with random.Random(20261117).sample over each type's row ids in the store; full target text. object_size_estimation is in the store but its cell is 0 (SIZE-V): no size row is drawn. Routing families come from the proof's loader audit on Orchard (separate section).

## box_3d (3813 rows in store)
### i=52628 qid=b08b9cc47a33b453001ff4eda dataset=d2
Q: Detect the ventilator in frame 11 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
Answer field: ```json
[{"bbox_3d":[-1.50, -1.16, 3.10, 0.76, 0.08, 0.79, -0.99, 0.39, 0.99],"label":"ventilator"}]
```
```
<think>
Step 1: find the ventilator in frame 11.
</think>

```json
[{"bbox_3d":[-1.50, -1.16, 3.10, 0.76, 0.08, 0.79, -0.99, 0.39, 0.99],"label":"ventilator"}]
```
```
### i=53125 qid=b3899ad53787d32effc8d08e7 dataset=d2
Q: Detect the books in frame 10 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
Answer field: ```json
[{"bbox_3d":[-0.42, -0.06, 0.88, 0.27, 0.31, 0.14, 0.80, 0.37, 0.83],"label":"books"}]
```
```
<think>
Step 1: find the books in frame 10.
</think>

```json
[{"bbox_3d":[-0.42, -0.06, 0.88, 0.27, 0.31, 0.14, 0.80, 0.37, 0.83],"label":"books"}]
```
```
### i=53357 qid=b4cd7dc76d444a96fa0f70dcc dataset=d1
Q: Detect the lamp in frame 6 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
Answer field: ```json
[{"bbox_3d":[-1.05, -0.51, 3.01, 0.55, 0.58, 0.32, 0.55, -0.37, -0.56],"label":"lamp"}]
```
```
<think>
Step 1: find the lamp in frame 6.
</think>

```json
[{"bbox_3d":[-1.05, -0.51, 3.01, 0.55, 0.58, 0.32, 0.55, -0.37, -0.56],"label":"lamp"}]
```
```
### i=53488 qid=b57face825eaca07d07dbf57e dataset=d1
Q: Detect the backpack in frame 30 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
Answer field: ```json
[{"bbox_3d":[0.10, 0.01, 2.41, 0.38, 0.42, 0.49, 0.49, 0.33, 0.51],"label":"backpack"}]
```
```
<think>
Step 1: find the backpack in frame 30.
</think>

```json
[{"bbox_3d":[0.10, 0.01, 2.41, 0.38, 0.42, 0.49, 0.49, 0.33, 0.51],"label":"backpack"}]
```
```
### i=56048 qid=bb64654a3263c933325bd13b5 dataset=d1
Q: Detect the cabinet in frame 25 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
Answer field: ```json
[{"bbox_3d":[-0.58, 0.06, 1.93, 1.20, 0.79, 0.52, 0.58, 0.34, 0.58],"label":"cabinet"}]
```
```
<think>
Step 1: find the cabinet in frame 25.
</think>

```json
[{"bbox_3d":[-0.58, 0.06, 1.93, 1.20, 0.79, 0.52, 0.58, 0.34, 0.58],"label":"cabinet"}]
```
```

## camera_obj_rel_dist_v1 (1951 rows in store)
### i=152563 qid=vstirel_b405aab7041c702a3a46b0d3 dataset=d2
Q: Measuring from the closest point of each object, which of these objects (table lamp, coasters, dining table, kitchen sink) is the closest to the camera in frame 31 of 32?
Options: ['A. table lamp', 'B. coasters', 'C. dining table', 'D. kitchen sink']
Answer field: D
```
<think>
Step 1: take the camera viewpoint of frame 31.
Step 2: locate the table lamp, first seen in frame 1.
Step 3: locate the coasters, first seen in frame 4.
Step 4: locate the dining table, first seen in frame 15.
Step 5: locate the kitchen sink, first seen in frame 25.
Step 6: ordered nearest to farthest from the camera viewpoint of frame 31, the objects are kitchen sink, then dining table, then table lamp, then coasters.
So the kitchen sink is closest to that camera viewpoint.
</think>

D
```
### i=152566 qid=vstirel_622080cc46574630bb4df549 dataset=d1
Q: Measuring from the closest point of each object, which of these objects (person, board, window, printer) is the closest to the camera in frame 12 of 32?
Options: ['A. person', 'B. board', 'C. window', 'D. printer']
Answer field: C
```
<think>
Step 1: take the camera viewpoint of frame 12.
Step 2: locate the person, first seen in frame 12.
Step 3: locate the board, first seen in frame 12.
Step 4: locate the window, first seen in frame 1.
Step 5: locate the printer, first seen in frame 2.
Step 6: ordered nearest to farthest from the camera viewpoint of frame 12, the objects are window, then board, then printer, then person.
So the window is closest to that camera viewpoint.
</think>

C
```
### i=152738 qid=vstirel_0ae78b7daa54181aa94d1376 dataset=d1
Q: Measuring from the closest point of each object, which of these objects (coat rack, clothes, pillow, shorts) is the closest to the camera in frame 2 of 32?
Options: ['A. coat rack', 'B. clothes', 'C. pillow', 'D. shorts']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 2.
Step 2: locate the coat rack, first seen in frame 6.
Step 3: locate the clothes, first seen in frame 8.
Step 4: locate the pillow, first seen in frame 2.
Step 5: locate the shorts, first seen in frame 11.
Step 6: ordered nearest to farthest from the camera viewpoint of frame 2, the objects are clothes, then shorts, then pillow, then coat rack.
So the clothes is closest to that camera viewpoint.
</think>

B
```
### i=152826 qid=vstirel_4af102cc115e33e3863cac5a dataset=d3
Q: Measuring from the closest point of each object, which of these objects (dishwasher, refrigerator, stove, tv) is the closest to the camera in frame 17 of 32?
Options: ['A. dishwasher', 'B. refrigerator', 'C. stove', 'D. tv']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 17.
Step 2: locate the dishwasher, first seen in frame 4.
Step 3: locate the refrigerator, first seen in frame 1.
Step 4: locate the stove, first seen in frame 7.
Step 5: locate the tv, first seen in frame 5.
Step 6: ordered nearest to farthest from the camera viewpoint of frame 17, the objects are dishwasher, then stove, then tv, then refrigerator.
So the dishwasher is closest to that camera viewpoint.
</think>

A
```
### i=152828 qid=vstirel_7a5832897cf7c1ff184adfef dataset=d2
Q: Measuring from the closest point of each object, which of these objects (window sill, hand sanitizer, office chair, table) is the closest to the camera in frame 6 of 32?
Options: ['A. window sill', 'B. hand sanitizer', 'C. office chair', 'D. table']
Answer field: C
```
<think>
Step 1: take the camera viewpoint of frame 6.
Step 2: locate the window sill, first seen in frame 1.
Step 3: locate the hand sanitizer, first seen in frame 7.
Step 4: locate the office chair, first seen in frame 1.
Step 5: locate the table, first seen in frame 1.
Step 6: ordered nearest to farthest from the camera viewpoint of frame 6, the objects are office chair, then table, then window sill, then hand sanitizer.
So the office chair is closest to that camera viewpoint.
</think>

C
```

## camera_obj_rel_dist_v2 (1983 rows in store)
### i=154096 qid=vstirel_faa8f23af81ddc2b5cf501d1 dataset=d3
Q: Measuring from the closest point of each object, which of these objects (chair, tv, cabinet) is the closest to the camera in frame 15 of 32?
Options: ['A. chair', 'B. tv', 'C. cabinet']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 15.
Step 2: locate the chair, first seen in frame 2.
Step 3: locate the tv, first seen in frame 3.
Step 4: locate the cabinet, first seen in frame 2.
Step 5: ordered nearest to farthest from the camera viewpoint of frame 15, the objects are tv, then chair, then cabinet.
So the tv is closest to that camera viewpoint.
</think>

B
```
### i=154198 qid=vstirel_8be355366b2a23789a804a3a dataset=d2
Q: Measuring from the closest point of each object, which of these objects (window, pin board, book) is the closest to the camera in frame 31 of 32?
Options: ['A. window', 'B. pin board', 'C. book']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 31.
Step 2: locate the window, first seen in frame 1.
Step 3: locate the pin board, first seen in frame 11.
Step 4: locate the book, first seen in frame 10.
Step 5: ordered nearest to farthest from the camera viewpoint of frame 31, the objects are pin board, then window, then book.
So the pin board is closest to that camera viewpoint.
</think>

B
```
### i=155026 qid=vstirel_4a829efe7b938f41b77c1656 dataset=d3
Q: Measuring from the closest point of each object, which of these objects (shelf, toilet, sink) is the closest to the camera in frame 21 of 32?
Options: ['A. shelf', 'B. toilet', 'C. sink']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 21.
Step 2: locate the shelf, first seen in frame 4.
Step 3: locate the toilet, first seen in frame 15.
Step 4: locate the sink, first seen in frame 15.
Step 5: ordered nearest to farthest from the camera viewpoint of frame 21, the objects are toilet, then sink, then shelf.
So the toilet is closest to that camera viewpoint.
</think>

B
```
### i=155600 qid=vstirel_73f86d83e9483ebe827bf35a dataset=d3
Q: Measuring from the closest point of each object, which of these objects (refrigerator, dishwasher, oven) is the closest to the camera in frame 17 of 32?
Options: ['A. refrigerator', 'B. dishwasher', 'C. oven']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 17.
Step 2: locate the refrigerator, first seen in frame 8.
Step 3: locate the dishwasher, first seen in frame 4.
Step 4: locate the oven, first seen in frame 8.
Step 5: ordered nearest to farthest from the camera viewpoint of frame 17, the objects are refrigerator, then oven, then dishwasher.
So the refrigerator is closest to that camera viewpoint.
</think>

A
```
### i=155899 qid=vstirel_05be499fd065215bf63a41b6 dataset=d1
Q: Measuring from the closest point of each object, which of these objects (door, laptop, keyboard) is the closest to the camera in frame 15 of 32?
Options: ['A. door', 'B. laptop', 'C. keyboard']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 15.
Step 2: locate the door, first seen in frame 9.
Step 3: locate the laptop, first seen in frame 4.
Step 4: locate the keyboard, first seen in frame 28.
Step 5: ordered nearest to farthest from the camera viewpoint of frame 15, the objects are door, then laptop, then keyboard.
So the door is closest to that camera viewpoint.
</think>

A
```

## camera_obj_rel_dist_v3 (1998 rows in store)
### i=156639 qid=vstirel_07d56a930998cd27d20a41c5 dataset=d2
Q: Measuring from the closest point of each object, which of these objects (plant, window sill) is the closest to the camera in frame 14 of 32?
Options: ['A. plant', 'B. window sill']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 14.
Step 2: locate the plant, first seen in frame 31.
Step 3: locate the window sill, first seen in frame 1.
Step 4: ordered nearest to farthest from the camera viewpoint of frame 14, the objects are plant, then window sill.
So the plant is closest to that camera viewpoint.
</think>

A
```
### i=156657 qid=vstirel_64c43305905198ee4701b36a dataset=d2
Q: Measuring from the closest point of each object, which of these objects (travelling bag, heater) is the closest to the camera in frame 5 of 32?
Options: ['A. travelling bag', 'B. heater']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 5.
Step 2: locate the travelling bag, first seen in frame 21.
Step 3: locate the heater, first seen in frame 1.
Step 4: ordered nearest to farthest from the camera viewpoint of frame 5, the objects are travelling bag, then heater.
So the travelling bag is closest to that camera viewpoint.
</think>

A
```
### i=156781 qid=vstirel_65266483d9746e86402ad9d9 dataset=d3
Q: Measuring from the closest point of each object, which of these objects (sofa, toilet) is the closest to the camera in frame 23 of 32?
Options: ['A. sofa', 'B. toilet']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 23.
Step 2: locate the sofa, first seen in frame 2.
Step 3: locate the toilet, first seen in frame 6.
Step 4: ordered nearest to farthest from the camera viewpoint of frame 23, the objects are sofa, then toilet.
So the sofa is closest to that camera viewpoint.
</think>

A
```
### i=157043 qid=vstirel_6820e4dfb9d36606973736c5 dataset=d3
Q: Measuring from the closest point of each object, which of these objects (bed, refrigerator) is the closest to the camera in frame 6 of 32?
Options: ['A. bed', 'B. refrigerator']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 6.
Step 2: locate the bed, first seen in frame 2.
Step 3: locate the refrigerator, first seen in frame 16.
Step 4: ordered nearest to farthest from the camera viewpoint of frame 6, the objects are bed, then refrigerator.
So the bed is closest to that camera viewpoint.
</think>

A
```
### i=157504 qid=vstirel_4d0c2ccf554f8da0e45bbb1f dataset=d2
Q: Measuring from the closest point of each object, which of these objects (cable duct, bottle) is the closest to the camera in frame 25 of 32?
Options: ['A. cable duct', 'B. bottle']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 25.
Step 2: locate the cable duct, first seen in frame 5.
Step 3: locate the bottle, first seen in frame 6.
Step 4: ordered nearest to farthest from the camera viewpoint of frame 25, the objects are cable duct, then bottle.
So the cable duct is closest to that camera viewpoint.
</think>

A
```

## first_seen_frame (7076 rows in store)
### i=188490 qid=b12fs_be39d50dfb818dfdacc1689c dataset=d1
Q: Which frame is the first one that shows the nightstand?
Answer field: 16
```
<think>
Step 1: the nightstand is first seen in frame 16 (right).
</think>

16
```
### i=190789 qid=b12fs_f1443212540cbfc84f1dbe6f dataset=d2
Q: In which frame does a curtain first appear?
Answer field: 7
```
<think>
Step 1: a curtain is first seen in frame 7 (middle).
</think>

7
```
### i=191379 qid=b12fs_7ee1103ecf0223abf07a594f dataset=d3
Q: In which frame does a stool first appear?
Answer field: 1
```
<think>
Step 1: a stool first appears in frame 1 (right).
</think>

1
```
### i=191693 qid=b12fs_86feaae9dc6a45d30747fa1e dataset=d3
Q: In which frame does the chair first appear?
Answer field: 2
```
<think>
Step 1: the chair is first seen in frame 2 (middle).
</think>

2
```
### i=193536 qid=b12fs_9156630ef1636deb3e343d84 dataset=d3
Q: Which frame is the first one that shows the tv?
Answer field: 2
```
<think>
Step 1: the tv first appears in frame 2 (left).
</think>

2
```

## obj_appearance_order (27791 rows in store)
### i=27969 qid=qd0dd9d4dd6ec657486ad168e dataset=d1
Q: What will be the first-time appearance order of the following categories in the video: ball, cabinet, counter, dishwasher?
Options: ['A. counter, dishwasher, cabinet, ball', 'B. counter, ball, cabinet, dishwasher', 'C. ball, counter, dishwasher, cabinet', 'D. cabinet, ball, counter, dishwasher']
Answer field: A
```
<think>
Step 1: find the first frame showing each object: ball frame 26; cabinet frame 21; counter frame 1; dishwasher frame 7.
Step 2: order them by first appearance: counter, dishwasher, cabinet, ball.
</think>

A
```
### i=40994 qid=q65134fb201982919fb44adfd dataset=d1
Q: What will be the first-time appearance order of the following categories in the video: bag, dart board, door, nightstand?
Options: ['A. nightstand, door, bag, dart board', 'B. bag, door, dart board, nightstand', 'C. nightstand, dart board, bag, door', 'D. dart board, bag, door, nightstand']
Answer field: A
```
<think>
Step 1: find the first frame showing each object: bag frame 7; dart board frame 9; door frame 4; nightstand frame 1.
Step 2: order them by first appearance: nightstand, door, bag, dart board.
</think>

A
```
### i=68609 qid=q3d50c056b447eb0ec3f8f7f4-p1 dataset=d2
Q: In what order do these object categories first appear in the video: apple, bathroom cabinet, bed, cabinet?
Options: ['A. apple, bathroom cabinet, cabinet, bed', 'B. bed, cabinet, apple, bathroom cabinet', 'C. cabinet, bed, bathroom cabinet, apple', 'D. apple, bed, cabinet, bathroom cabinet']
Answer field: B
```
<think>
Step 1: find the apple, the bathroom cabinet, the bed, the cabinet.
Step 2: order them by first appearance: bed, cabinet, apple, bathroom cabinet.
</think>

B
```
### i=181253 qid=b12ao_f6774eab20ca9b29a31e36a6 dataset=d2
Q: What will be the first-time appearance order of the following categories in the video: cabinet, chair, shelf, towel?
Options: ['A. shelf, cabinet, chair, towel', 'B. shelf, cabinet, towel, chair', 'C. towel, cabinet, shelf, chair', 'D. towel, chair, shelf, cabinet']
Answer field: B
```
<think>
Step 1: find the first frame showing each object: cabinet frame 6; chair frame 27; shelf frame 1; towel frame 12.
Step 2: order them by first appearance: shelf, cabinet, towel, chair.
</think>

B
```
### i=181502 qid=b12ao_87206755ddaa522ecad17e84 dataset=d2
Q: What will be the first-time appearance order of the following categories in the video: box, broom, monitor, pants?
Options: ['A. monitor, pants, box, broom', 'B. box, monitor, pants, broom', 'C. monitor, broom, box, pants', 'D. box, broom, monitor, pants']
Answer field: D
```
<think>
Step 1: find the first frame showing each object: box frame 1; broom frame 3; monitor frame 5; pants frame 16.
Step 2: order them by first appearance: box, broom, monitor, pants.
</think>

D
```

## obj_obj_relative_pos_lr (1998 rows in store)
### i=159157 qid=vstirel_758205f9499415331425b385 dataset=d2
Q: In frame 30 of 32, relative to bottle, is canopy bed to the [Left/Right]?
Options: ['A. Right', 'B. Left']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 30.
Step 2: locate the canopy bed, first seen in frame 2.
Step 3: locate the bottle, first seen in frame 5.
Step 4: from the camera viewpoint of frame 30, the canopy bed is to the right of the bottle.
So the canopy bed is right relative to the bottle.
</think>

A
```
### i=194672 qid=vstirel_55927e0da65b0383c1b6184b dataset=d3
Q: In frame 6 of 32, relative to fireplace, is tv to the [Left/Right]?
Options: ['A. Right', 'B. Left']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 6.
Step 2: locate the tv, first seen in frame 2.
Step 3: locate the fireplace, first seen in frame 2.
Step 4: from the camera viewpoint of frame 6, the tv is to the right of the fireplace.
So the tv is right relative to the fireplace.
</think>

A
```
### i=195300 qid=vstirel_4f6f09ee1adc70e132bb173c dataset=d3
Q: In frame 2 of 32, relative to tv, is refrigerator to the [Left/Right]?
Options: ['A. Right', 'B. Left']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 2.
Step 2: locate the refrigerator, first seen in frame 4.
Step 3: locate the tv, first seen in frame 7.
Step 4: from the camera viewpoint of frame 2, the refrigerator is to the right of the tv.
So the refrigerator is right relative to the tv.
</think>

A
```
### i=195435 qid=vstirel_55d5ff7672606c173a61ebc8 dataset=d3
Q: In frame 28 of 32, relative to sink, is bathtub to the [Left/Right]?
Options: ['A. Right', 'B. Left']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 28.
Step 2: locate the bathtub, first seen in frame 1.
Step 3: locate the sink, first seen in frame 1.
Step 4: from the camera viewpoint of frame 28, the bathtub is to the left of the sink.
So the bathtub is left relative to the sink.
</think>

B
```
### i=195466 qid=vstirel_cf42222814116794516fccb7 dataset=d3
Q: In frame 11 of 32, relative to bed, is cabinet to the [Left/Right]?
Options: ['A. Right', 'B. Left']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 11.
Step 2: locate the cabinet, first seen in frame 1.
Step 3: locate the bed, first seen in frame 1.
Step 4: from the camera viewpoint of frame 11, the cabinet is to the left of the bed.
So the cabinet is left relative to the bed.
</think>

B
```

## obj_obj_relative_pos_nf (2000 rows in store)
### i=159455 qid=vstirel_f8ce9e888766ad0f871db340 dataset=d3
Q: In frame 6 of 32, relative to the camera, is sink [Near/Far] compared to cabinet?
Options: ['A. Near', 'B. Far']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 6.
Step 2: locate the sink, first seen in frame 4.
Step 3: locate the cabinet, first seen in frame 14.
Step 4: from the camera viewpoint of frame 6, the sink is nearer than the cabinet.
So the sink is nearer than the cabinet relative to that camera viewpoint.
</think>

A
```
### i=159660 qid=vstirel_05454bcdd47e8d698c4e6dd6 dataset=d3
Q: In frame 4 of 32, relative to the camera, is dishwasher [Near/Far] compared to refrigerator?
Options: ['A. Near', 'B. Far']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 4.
Step 2: locate the dishwasher, first seen in frame 2.
Step 3: locate the refrigerator, first seen in frame 3.
Step 4: from the camera viewpoint of frame 4, the refrigerator is nearer than the dishwasher.
So the dishwasher is farther than the refrigerator relative to that camera viewpoint.
</think>

B
```
### i=160288 qid=vstirel_c85e3b32dd604a264f0c3cf0 dataset=d2
Q: In frame 24 of 32, relative to the camera, is paper towel dispenser [Near/Far] compared to laptop stand?
Options: ['A. Near', 'B. Far']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 24.
Step 2: locate the paper towel dispenser, first seen in frame 3.
Step 3: locate the laptop stand, first seen in frame 19.
Step 4: from the camera viewpoint of frame 24, the laptop stand is nearer than the paper towel dispenser.
So the paper towel dispenser is farther than the laptop stand relative to that camera viewpoint.
</think>

B
```
### i=160427 qid=vstirel_d237570577b5b6a0d6fccd5c dataset=d3
Q: In frame 2 of 32, relative to the camera, is sink [Near/Far] compared to bathtub?
Options: ['A. Near', 'B. Far']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 2.
Step 2: locate the sink, first seen in frame 1.
Step 3: locate the bathtub, first seen in frame 1.
Step 4: from the camera viewpoint of frame 2, the sink is nearer than the bathtub.
So the sink is nearer than the bathtub relative to that camera viewpoint.
</think>

A
```
### i=161044 qid=vstirel_cd2b71bb8c766c283764b5fd dataset=d3
Q: In frame 1 of 32, relative to the camera, is bed [Near/Far] compared to bathtub?
Options: ['A. Far', 'B. Near']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 1.
Step 2: locate the bed, first seen in frame 3.
Step 3: locate the bathtub, first seen in frame 7.
Step 4: from the camera viewpoint of frame 1, the bed is nearer than the bathtub.
So the bed is nearer than the bathtub relative to that camera viewpoint.
</think>

B
```

## obj_obj_relative_pos_ud (1996 rows in store)
### i=161517 qid=vstirel_4d398e12a5c5f8df12f778c7 dataset=d3
Q: In frame 27 of 32, relative to tv, is shelf to the [Up/Down]?
Options: ['A. Up', 'B. Down']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 27.
Step 2: locate the shelf, first seen in frame 3.
Step 3: locate the tv, first seen in frame 4.
Step 4: in frame 27's level horizon, the centre of the shelf is lower than the centre of the tv.
So the shelf is down relative to the tv.
</think>

B
```
### i=162321 qid=vstirel_50dfdce104484db8e927d49c dataset=d2
Q: In frame 9 of 32, relative to shower, is backpack to the [Up/Down]?
Options: ['A. Down', 'B. Up']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 9.
Step 2: locate the backpack, first seen in frame 4.
Step 3: locate the shower, first seen in frame 22.
Step 4: in frame 9's level horizon, the centre of the backpack is lower than the centre of the shower.
So the backpack is down relative to the shower.
</think>

A
```
### i=162372 qid=vstirel_d02d29d96364fe19e006db5c dataset=d2
Q: In frame 5 of 32, relative to trash can, is blinds rail to the [Up/Down]?
Options: ['A. Down', 'B. Up']
Answer field: B
```
<think>
Step 1: take the camera viewpoint of frame 5.
Step 2: locate the blinds rail, first seen in frame 9.
Step 3: locate the trash can, first seen in frame 7.
Step 4: in frame 5's level horizon, the centre of the blinds rail is higher than the centre of the trash can.
So the blinds rail is up relative to the trash can.
</think>

B
```
### i=162886 qid=vstirel_04783bbe65d74af1d3578a64 dataset=d2
Q: In frame 7 of 32, relative to broom, is toaster to the [Up/Down]?
Options: ['A. Up', 'B. Down']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 7.
Step 2: locate the toaster, first seen in frame 5.
Step 3: locate the broom, first seen in frame 3.
Step 4: in frame 7's level horizon, the centre of the toaster is higher than the centre of the broom.
So the toaster is up relative to the broom.
</think>

A
```
### i=163051 qid=vstirel_323071cd7ee0d1db5056dada dataset=d3
Q: In frame 26 of 32, relative to bed, is fireplace to the [Up/Down]?
Options: ['A. Up', 'B. Down']
Answer field: A
```
<think>
Step 1: take the camera viewpoint of frame 26.
Step 2: locate the fireplace, first seen in frame 3.
Step 3: locate the bed, first seen in frame 7.
Step 4: in frame 26's level horizon, the centre of the fireplace is higher than the centre of the bed.
So the fireplace is up relative to the bed.
</think>

A
```

## object_counting (20669 rows in store)
### i=49909 qid=q842e3d472af0d4cef92f8194 dataset=d2
Q: How many kitchen cabinet(s) do we have in this room?
Answer field: 2
```
<think>
Step 1: list each distinct kitchen cabinet once, by the frame where it first appears: frame 1; frame 1.
So the count equals 2.
</think>

2
```
### i=51691 qid=q3ced9fb01708d5fa4d7c6bf2 dataset=d2
Q: How many bedside table(s) do we have in this room?
Answer field: 2
```
<think>
Step 1: locate each distinct bedside table at its first appearance: frame 27; frame 29.
So the count is 2.
</think>

2
```
### i=94264 qid=qc3d602f46e21eb1e90d83bf1-p1 dataset=d1
Q: How many book(s) are there in the room shown in the video?
Answer field: 3
```
<think>
Step 1: find each distinct book, across the frames, and count it once.
</think>

3
```
### i=170195 qid=b12ct_6fe798ebacfe2c55ad2aab9d dataset=d2
Q: What is the total number of door(s) and heater(s) and power strip(s) in this room?
Answer field: 5
```
<think>
Step 1: list each distinct door once, by the frame where it first appears: frame 4 (right).
Step 2: list each distinct heater once, by the frame where it first appears: frame 3 (left); frame 8 (left); frame 9 (right).
Step 3: locate each distinct power strip at its first appearance: frame 20 (left).
Step 4: add them: 1 + 3 = 4; 4 + 1 = 5.
So there are 5 in total.
</think>

5
```
### i=173027 qid=b12ct_2d1bbeee369fa6d2ac7dedaa dataset=d3
Q: Count the table(s) and tv(s) in this room together. How many are there in total?
Answer field: 3
```
<think>
Step 1: list each distinct table once, by the frame where it first appears: frame 3 (middle); frame 19 (left).
Step 2: list each distinct tv once, by the frame where it first appears: frame 19 (left).
Step 3: add them: 2 + 1 = 3.
So there are 3 in total.
</think>

3
```

## object_rel_direction_easy (27993 rows in store)
### i=16453 qid=qf5d4f26da60e34df9cb30f6b dataset=d3
Q: From my position at the table, facing toward the dishwasher, is the washer to the left or right of the dishwasher?
Options: ['A. right', 'B. left']
Answer field: A
```
<think>
Step 1: locate the table, the dishwasher and the washer.
Step 2: I stand at the table facing the dishwasher; I find the washer to my right.
The question asks me to face the dishwasher, so I keep that heading.
So I find the washer to my right.
</think>

A
```
### i=17467 qid=q6eb073e65383133092ef075d dataset=d1
Q: When positioned beside the door and looking at the lamp, is the backpack placed on the left or right?
Options: ['A. right', 'B. left']
Answer field: B
```
<think>
Step 1: find the door and the lamp, then the backpack.
Step 2: facing the lamp from the door, I find the backpack to my left.
The question asks me to face the lamp, so I keep that heading.
So I find the position of the backpack to my left.
</think>

B
```
### i=18991 qid=q780e124d52982cf59e394be5 dataset=d3
Q: If I am standing by the table and facing the stool, is the shelf to the left or the right of the stool?
Options: ['A. left', 'B. right']
Answer field: A
```
<think>
Step 1: locate the table, the stool and the shelf.
Step 2: I find the shelf to my left when I stand at the table facing the stool.
The question asks me to face the stool, so I keep that heading.
So I find the shelf to my left.
</think>

A
```
### i=24030 qid=q67e31974495fe051cef2dd86 dataset=d3
Q: If I am standing by the oven and facing the sink, is the refrigerator to the left or the right of the sink?
Options: ['A. right', 'B. left']
Answer field: A
```
<think>
Step 1: find the oven, the sink and the refrigerator.
Step 2: I find the refrigerator to my right when I stand at the oven facing the sink.
The question asks me to face the sink, so I keep that heading.
So I find the position of the refrigerator to my right.
</think>

A
```
### i=123343 qid=vsi590k_033627_away dataset=d1
Q: If I am standing by the printer and turned away from the clock, is the trash can to my left or to my right?
Options: ['A. right', 'B. left']
Answer field: A
```
<think>
Seen: printer in frame 5; clock in frame 26; trash can in frame 18.
If I stood at the printer facing the clock, the trash can would be to my left.
The question has me face away from the clock. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the trash can to my right.
</think>

A
```

## object_rel_direction_easy [away_opp, ReVSI wording] (3664 rows in store)
### i=197066 qid=vsi590k_249476_away_opp dataset=d3
Q: If I am standing by the refrigerator and facing in the opposite direction of the dishwasher, is the stove to my left or to my right?
Options: ['A. left', 'B. right']
Answer field: B
```
<think>
Seen: refrigerator in frame 22; dishwasher in frame 13; stove in frame 27.
If I stood at the refrigerator facing the dishwasher, the stove would be to my left.
The question has me facing in the opposite direction of the dishwasher. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the stove to my right.
</think>

B
```
### i=197202 qid=vsi590k_145935_away_opp dataset=d2
Q: If I am standing by the bookshelf and facing in the opposite direction of the suitcase, is the laptop to my left or to my right?
Options: ['A. right', 'B. left']
Answer field: A
```
<think>
Seen: bookshelf in frame 16; suitcase in frame 5; laptop in frame 11.
If I stood at the bookshelf facing the suitcase, the laptop would be to my left.
The question has me facing in the opposite direction of the suitcase. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the laptop to my right.
</think>

A
```
### i=197601 qid=vsi590k_145020_away_opp dataset=d2
Q: If I am standing by the bed and facing in the opposite direction of the toilet, is the power strip to my left or to my right?
Options: ['A. right', 'B. left']
Answer field: B
```
<think>
Seen: bed in frame 17; toilet in frame 27; power strip in frame 3.
If I stood at the bed facing the toilet, the power strip would be to my right.
The question has me facing in the opposite direction of the toilet. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the power strip to my left.
</think>

B
```
### i=200797 qid=vsi590k_035180_away_opp dataset=d1
Q: If I am standing by the refrigerator and facing in the opposite direction of the window, is the microwave to my left or to my right?
Options: ['A. left', 'B. right']
Answer field: B
```
<think>
Seen: refrigerator in frame 25; window in frame 29; microwave in frame 6.
If I stood at the refrigerator facing the window, the microwave would be to my left.
The question has me facing in the opposite direction of the window. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the microwave to my right.
</think>

B
```
### i=201351 qid=vsi590k_146948_away_opp dataset=d2
Q: If I am standing by the door and facing in the opposite direction of the sofa, is the laptop to my left or to my right?
Options: ['A. right', 'B. left']
Answer field: B
```
<think>
Seen: door in frame 2; sofa in frame 20; laptop in frame 15.
If I stood at the door facing the sofa, the laptop would be to my right.
The question has me facing in the opposite direction of the sofa. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the laptop to my left.
</think>

B
```

## object_rel_direction_hard (30407 rows in store)
### i=45412 qid=q2668ee7606c3417a70bbf45d dataset=d1
Q: Positioned at the sofa, looking directly toward the microwave, where exactly is the refrigerator: front-left, front-right, back-left, or back-right?
Options: ['A. front-right', 'B. back-left', 'C. front-left', 'D. back-right']
Answer field: C
```
<think>
Step 1: locate the sofa, the microwave and the refrigerator.
Step 2: facing the microwave from the sofa, I find the refrigerator in front of me, on my left.
The question asks me to face the microwave, so I keep that heading.
So I find the refrigerator at my front-left.
</think>

C
```
### i=89988 qid=q18aebbcf08c1a2e574e5038c-p1 dataset=d1
Q: I stand by the bag looking at the paper towel dispenser. Where is the door relative to me: front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. back-left', 'B. front-right', 'C. back-right', 'D. front-left']
Answer field: D
```
<think>
Step 1: find the bag, the paper towel dispenser and the door.
Step 2: facing the paper towel dispenser from the bag, I find the door in front of me, on my left.
The question has me facing the paper towel dispenser; I keep that heading.
So I find the door at my front-left.
</think>

D
```
### i=111300 qid=vsi590k_093617 dataset=d2
Q: If I am standing by the heater and facing the keyboard, is the whiteboard to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. back-right', 'B. back-left', 'C. front-left', 'D. front-right']
Answer field: C
```
<think>
Seen: heater in frame 8; keyboard in frame 21; whiteboard in frame 30.
Standing at the heater facing the keyboard, I find the whiteboard in front of me, on my left.
The question has me facing toward the keyboard; no turn applies.
So I find the whiteboard at my front-left.
</think>

C
```
### i=114555 qid=vsi590k_095722_away dataset=d2
Q: If I am standing by the sofa and turned away from the tv, is the cutting board to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. back-left', 'B. front-right', 'C. front-left', 'D. back-right']
Answer field: D
```
<think>
Seen: sofa in frame 21; tv in frame 32; cutting board in frame 14.
If I stood at the sofa facing the tv, the cutting board would be in front of me, on my left.
The question has me face away from the tv. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the cutting board at my back-right.
</think>

D
```
### i=120375 qid=vsi590k_014784_away dataset=d1
Q: If I am standing by the window and facing away from the lamp, is the desk to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. back-left', 'B. front-right', 'C. back-right', 'D. front-left']
Answer field: C
```
<think>
Seen: window in frame 10; lamp in frame 6; desk in frame 12.
If I stood at the window facing the lamp, the desk would be in front of me, on my left.
The question has me face away from the lamp. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the desk at my back-right.
</think>

C
```

## object_rel_direction_hard [away_opp, ReVSI wording] (2182 rows in store)
### i=197021 qid=vsi590k_100634_away_opp dataset=d2
Q: If I am standing by the whiteboard and facing in the opposite direction of the telephone, is the power strip to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. front-right', 'B. back-left', 'C. back-right', 'D. front-left']
Answer field: C
```
<think>
Seen: whiteboard in frame 22; telephone in frame 24; power strip in frame 15.
If I stood at the whiteboard facing the telephone, the power strip would be in front of me, on my left.
The question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the power strip at my back-right.
</think>

C
```
### i=197043 qid=vsi590k_236851_away_opp dataset=d3
Q: If I am standing by the bathtub and facing in the opposite direction of the stool, is the bed to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. back-right', 'B. front-right', 'C. front-left', 'D. back-left']
Answer field: D
```
<think>
Seen: bathtub in frame 27; stool in frame 31; bed in frame 32.
If I stood at the bathtub facing the stool, the bed would be in front of me, on my right.
The question has me facing in the opposite direction of the stool. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bed at my back-left.
</think>

D
```
### i=198557 qid=vsi590k_095056_away_opp dataset=d2
Q: If I am standing by the trash can and facing in the opposite direction of the basket, is the table to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. front-left', 'B. back-left', 'C. front-right', 'D. back-right']
Answer field: D
```
<think>
Seen: trash can in frame 9; basket in frame 31; table in frame 19.
If I stood at the trash can facing the basket, the table would be in front of me, on my left.
The question has me facing in the opposite direction of the basket. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the table at my back-right.
</think>

D
```
### i=200830 qid=vsi590k_095313_away_opp dataset=d2
Q: If I am standing by the bookshelf and facing in the opposite direction of the heater, is the table lamp to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. back-right', 'B. back-left', 'C. front-right', 'D. front-left']
Answer field: B
```
<think>
Seen: bookshelf in frame 32; heater in frame 6; table lamp in frame 9.
If I stood at the bookshelf facing the heater, the table lamp would be in front of me, on my right.
The question has me facing in the opposite direction of the heater. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the table lamp at my back-left.
</think>

B
```
### i=201195 qid=vsi590k_104785_away_opp dataset=d2
Q: If I am standing by the heater and facing in the opposite direction of the bookshelf, is the door to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Options: ['A. front-left', 'B. front-right', 'C. back-left', 'D. back-right']
Answer field: D
```
<think>
Seen: heater in frame 20; bookshelf in frame 25; door in frame 5.
If I stood at the heater facing the bookshelf, the door would be in front of me, on my left.
The question has me facing in the opposite direction of the bookshelf. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the door at my back-right.
</think>

D
```

## object_rel_direction_medium (26459 rows in store)
### i=34510 qid=q51c8317e134214fb58848b48 dataset=d1
Q: I'm positioned at the sofa, looking toward the tv; is the trash bin placed to my left, right, or behind me? 'Behind' suggests turning at least 135 degrees to see it.
Options: ['A. back', 'B. left', 'C. right']
Answer field: B
```
<think>
Step 1: find the sofa, the tv and the trash bin.
Step 2: I stand at the sofa facing the tv; I find the trash bin ahead of me, slightly to my left.
The question asks me to face the tv, so I keep that heading.
So I find the trash bin to my left.
</think>

B
```
### i=76161 qid=qbb198b417f401102955cfa62-p1 dataset=d2
Q: I stand by the blanket looking at the rack. Where is the cup relative to me: left, right, or behind me? 'Behind' means I'd have to turn at least 135 degrees.
Options: ['A. back', 'B. left', 'C. right']
Answer field: C
```
<think>
Step 1: locate the blanket, the rack and the cup.
Step 2: I find the cup out to my right when I stand at the blanket facing the rack.
The question has me facing toward the rack; no turn applies.
So I find the cup to my right.
</think>

C
```
### i=76565 qid=q888fbe1370042ff12045b7c9-p1 dataset=d3
Q: If I am standing beside the sofa and facing the stove, which direction describes the stool relative to me: left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. back', 'B. left', 'C. right']
Answer field: C
```
<think>
Step 1: find the sofa and the stove, then the stool.
Step 2: facing the stove from the sofa, I find the stool ahead of me, slightly to my right.
The question asks me to face the stove, so I keep that heading.
So I find the stool to my right.
</think>

C
```
### i=116271 qid=vsi590k_129958_away dataset=d2
Q: If I am standing by the bed and with my back to the power strip, is the trash can to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. back', 'B. left', 'C. right']
Answer field: A
```
<think>
Seen: bed in frame 20; power strip in frame 12; trash can in frame 13.
If I stood at the bed facing the power strip, the trash can would be ahead of me, slightly to my left.
The question has me face away from the power strip. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the trash can at my back.
</think>

A
```
### i=123145 qid=vsi590k_242626_away dataset=d3
Q: If I am standing by the dishwasher and facing away from the sofa, is the stove to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. back', 'B. left', 'C. right']
Answer field: B
```
<think>
Seen: dishwasher in frame 15; sofa in frame 27; stove in frame 10.
If I stood at the dishwasher facing the sofa, the stove would be out to my right.
The question has me face away from the sofa. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the stove to my left.
</think>

B
```

## object_rel_direction_medium [away_opp, ReVSI wording] (2665 rows in store)
### i=197403 qid=vsi590k_117770_away_opp dataset=d2
Q: If I am standing by the monitor and facing in the opposite direction of the heater, is the kettle to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. left', 'B. back', 'C. right']
Answer field: A
```
<think>
Seen: monitor in frame 7; heater in frame 16; kettle in frame 24.
If I stood at the monitor facing the heater, the kettle would be out to my right.
The question has me facing in the opposite direction of the heater. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the kettle to my left.
</think>

A
```
### i=197770 qid=vsi590k_133251_away_opp dataset=d2
Q: If I am standing by the keyboard and facing in the opposite direction of the telephone, is the printer to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. right', 'B. left', 'C. back']
Answer field: A
```
<think>
Seen: keyboard in frame 6; telephone in frame 26; printer in frame 21.
If I stood at the keyboard facing the telephone, the printer would be out to my left.
The question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the printer to my right.
</think>

A
```
### i=199126 qid=vsi590k_132742_away_opp dataset=d2
Q: If I am standing by the sofa and facing in the opposite direction of the table, is the tv to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. left', 'B. back', 'C. right']
Answer field: C
```
<think>
Seen: sofa in frame 30; table in frame 16; tv in frame 18.
If I stood at the sofa facing the table, the tv would be out to my left.
The question has me facing in the opposite direction of the table. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the tv to my right.
</think>

C
```
### i=200739 qid=vsi590k_118432_away_opp dataset=d2
Q: If I am standing by the heater and facing in the opposite direction of the computer tower, is the stapler to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. back', 'B. right', 'C. left']
Answer field: B
```
<think>
Seen: heater in frame 24; computer tower in frame 8; stapler in frame 27.
If I stood at the heater facing the computer tower, the stapler would be out to my left.
The question has me facing in the opposite direction of the computer tower. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the stapler to my right.
</think>

B
```
### i=202057 qid=vsi590k_241733_away_opp dataset=d3
Q: If I am standing by the stove and facing in the opposite direction of the dishwasher, is the refrigerator to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Options: ['A. left', 'B. right', 'C. back']
Answer field: C
```
<think>
Seen: stove in frame 9; dishwasher in frame 11; refrigerator in frame 11.
If I stood at the stove facing the dishwasher, the refrigerator would be ahead of me, slightly to my left.
The question has me facing in the opposite direction of the dishwasher. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the position of the refrigerator at my back.
</think>

C
```

## object_rel_distance (20665 rows in store)
### i=13263 qid=q66cc898c8d2448eb5bfa19af dataset=d2
Q: Measuring from the closest point of each object, which of these objects (blanket, book, plant saucer, shoe rack) is the closest to the arched ceiling?
Options: ['A. plant saucer', 'B. blanket', 'C. book', 'D. shoe rack']
Answer field: A
```
<think>
Step 1: find the arched ceiling, first seen in frame 10.
Step 2: the candidates ordered nearest to farthest from the arched ceiling are: plant saucer, then blanket, then book, then shoe rack.
The question asks me to choose the closest, which is the plant saucer.
</think>

A
```
### i=31710 qid=q37200329cb58150d0b08329f dataset=d3
Q: Measuring from the closest point of each object, which of these objects (chair, dishwasher, stove, table) is the closest to the oven?
Options: ['A. table', 'B. chair', 'C. dishwasher', 'D. stove']
Answer field: D
```
<think>
Step 1: find the oven, first seen in frame 26.
Step 2: order the candidates from nearest to farthest from the oven: stove, then table, then dishwasher, then chair.
The question asks me to choose the closest, which is the stove.
</think>

D
```
### i=66094 qid=q48fc90d78d9f8f150c6468e2-p1 dataset=d3
Q: Using closest-point distances to the tv, select the nearest object from chair, oven, sofa, stove.
Options: ['A. stove', 'B. sofa', 'C. oven', 'D. chair']
Answer field: B
```
<think>
Step 1: find the tv, first seen in frame 26.
Step 2: the candidates ordered nearest to farthest from the tv are: sofa, then oven, then stove, then chair.
The question asks me to choose the closest, which is the sofa.
</think>

B
```
### i=143985 qid=qd45641f433bdcd951e4200ae-p1 dataset=d1
Q: Among bag, chair, desk, door, which object has the smallest distance to the backpack? Use the nearest points of each object.
Options: ['A. bag', 'B. chair', 'C. door', 'D. desk']
Answer field: D
```
<think>
Step 1: find the backpack, first seen in frame 2.
Step 2: from nearest to farthest from the backpack, the order is: desk, then bag, then chair, then door.
The question asks for the closest: the desk.
</think>

D
```
### i=146899 qid=q94c8cd8833b748c7a5c88c37-p1 dataset=d3
Q: Compare the shortest gaps from the sink to these objects: chair, sofa, table, tv. Which object is nearest?
Options: ['A. tv', 'B. sofa', 'C. table', 'D. chair']
Answer field: D
```
<think>
Step 1: the first appearance of the sink is in frame 13.
Step 2: the nearest-to-farthest order from the sink is: chair, then table, then sofa, then tv.
The question asks for the closest object, the chair.
</think>

D
```

## object_size_estimation (9778 rows in store)
### i=48291 qid=q54415abee79342c1307aa139 dataset=d2
Q: What is the length of the longest edge of the blind, in centimeters?
Answer field: 194
```
<think>
Step 1: find the blind.
Step 2: the question asks for an estimate of the longest edge, in centimeters, from the frames.
</think>

194
```
### i=77116 qid=q13cc6f5a96c421df974258ec-p1 dataset=d2
Q: How long is the longest side of the windowsill? State its length in centimeters.
Answer field: 317
```
<think>
Step 1: find the windowsill, first seen in frame 1.
Step 2: the question asks for the longest edge in centimeters; I estimate it from the frames.
</think>

317
```
### i=96299 qid=q5fc4b8ce3ca2700fbb24b07d-p1 dataset=d2
Q: Measure the folder along its longest dimension and give that length in centimeters.
Answer field: 78
```
<think>
Step 1: find the folder.
Step 2: the question asks for the longest edge, in centimeters. I estimate it from the frames.
</think>

78
```
### i=100049 qid=q95b58e31b7f5db74624d26e8-p1 dataset=d2
Q: Of the length, width, and height of the storage cabinet, what is the largest measurement in centimeters?
Answer field: 264
```
<think>
Step 1: find the storage cabinet, first seen in frame 5.
Step 2: the question asks for the longest edge in centimeters; I estimate it from the frames.
</think>

264
```
### i=100651 qid=q8931dcbc8c1b88dd2e797acd-p1 dataset=d2
Q: How long is the longest side of the towel radiator? State its length in centimeters.
Answer field: 145
```
<think>
Step 1: find the towel radiator, first seen in frame 11.
Step 2: the question asks for the longest edge, in centimeters. I estimate it from the frames.
</think>

145
```

## room_size_estimation [traced room] (431 rows in store)
### i=195478 qid=a0_room_vsi590k_058638 dataset=d1
Q: What is the size of this room (in square meters)?  If multiple rooms are shown, estimate the size of the combined space.
Answer field: 7.94
```
<think>
The question asks for the combined floor area in square meters.
Seen: door first seen in frame 9; doorframe first seen in frame 2; shelf first seen in frame 5.
Of these, the doorframe and the shelf are farthest apart, with the door off to the side.
</think>

7.94
```
### i=195567 qid=a0_room_vsi590k_059171 dataset=d1
Q: What is the size of this room (in square meters)?  If multiple rooms are shown, estimate the size of the combined space.
Answer field: 15.19
```
<think>
The question asks for the combined floor area in square meters.
Seen: table in frame 1; radiator in frame 8; tv in frame 8.
Of these, the table and the radiator are farthest apart, with the tv off to the side.
</think>

15.19
```
### i=195660 qid=a0_room_room_scannetppv2_d110b8f8b0_s0 dataset=d2
Q: What is the size of this room (in square meters)?  If multiple rooms are shown, estimate the size of the combined space.
Answer field: 11.61
```
<think>
The question asks for the combined floor area in square meters.
Seen: curtain frame first seen in frame 8; loft first seen in frame 5; wardrobe first seen in frame 9.
Of these, the curtain frame and the loft are farthest apart, with the wardrobe between them.
</think>

11.61
```
### i=195667 qid=a0_room_room_scannet_scene0395_02_s0 dataset=d1
Q: What is the size of this room (in square meters)?  If multiple rooms are shown, estimate the size of the combined space.
Answer field: 18.95
```
<think>
The question asks for the combined floor area in square meters.
Seen: bookshelf first seen in frame 1; door first seen in frame 1; board first seen in frame 1.
The bookshelf and the board are the farthest apart among these landmarks, with the door between them.
</think>

18.95
```
### i=195893 qid=a2_room_ft2_room_scannetppv2_2e5c249de3_s0 dataset=d2
Q: What is the size of this room (in square feet)?  If multiple rooms are shown, estimate the size of the combined space.
Answer field: 173.49
```
<think>
The question asks for the combined floor area in square feet.
Seen: curtain first seen in frame 1; bed first seen in frame 1; doorframe first seen in frame 7.
Of these, the curtain and the doorframe are farthest apart, with the bed between them.
</think>

173.49
```

## route_planning (8894 rows in store)
### i=101879 qid=q022f8c0790670e9f6ba1e02e dataset=d3
Q: You are a robot beginning at the cabinet facing the sink. You want to navigate to the toilet. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): 1. [please fill in] 2. Go forward until the toilet. You have reached the final destination.
Options: ['A. Turn Right', 'B. Turn Back', 'C. Turn Left']
Answer field: C
```
<think>
Step 1: I stand at the cabinet facing the sink. I find the toilet to my left: turn left.
The turns are: left.
</think>

C
```
### i=149045 qid=q4a07fdc923c99f88d340fce5 dataset=d2
Q: You are a robot beginning at the rug and facing the shopping bag. You want to navigate to the clipboard. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): 1. [please fill in] 2. Go forward until the office chair 3. [please fill in] 4. Go forward until the desk 5. [please fill in] 6. Go forward until the clipboard. You have reached the final destination.
Options: ['A. Turn Back, Turn Right, Turn Right', 'B. Turn Right, Turn Right, Turn Left', 'C. Turn Right, Turn Left, Turn Left', 'D. Turn Left, Turn Right, Turn Right']
Answer field: D
```
<think>
Step 1: I stand at the rug facing the shopping bag. I find the office chair to my left: turn left.
Step 2: I go forward to the office chair and keep that heading. I find the desk to my right: turn right.
Step 3: I go forward to the desk and keep that heading. I find the clipboard to my right: turn right.
The turns are: left, right, right.
</think>

D
```
### i=150170 qid=q8efc09ef4f63b3dda5eca5ca dataset=d3
Q: You are a robot beginning at the sink and facing the oven. You want to navigate to the refrigerator. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): 1. [please fill in] 2. Go forward until the dishwasher 3. [please fill in] 4. Go forward until the refrigerator. You have reached the final destination.
Options: ['A. Turn Back, Turn Left', 'B. Turn Left, Turn Right', 'C. Turn Right, Turn Left', 'D. Turn Left, Turn Left']
Answer field: C
```
<think>
Step 1: I stand at the sink facing the oven. I find the dishwasher to my right: turn right.
Step 2: I go forward to the dishwasher and keep that heading. I find the refrigerator to my left: turn left.
The turns are: right, left.
</think>

C
```
### i=150368 qid=q9b2c0a7326bab48195aa91f9 dataset=d1
Q: You are a robot beginning at the stove and facing the picture. You want to navigate to the water pitcher. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): 1. [please fill in] 2. Go forward until the trash bin(s) 3. [please fill in] 4. Go forward until the kitchen cabinets 5. [please fill in] 6. Go forward until the water pitcher. You have reached the final destination.
Options: ['A. Turn Right, Turn Left, Turn Right', 'B. Turn Back, Turn Left, Turn Left', 'C. Turn Back, Turn Right, Turn Right', 'D. Turn Back, Turn Left, Turn Right']
Answer field: C
```
<think>
Step 1: I stand at the stove facing the picture. I find the trash bin(s) behind me: turn back.
Step 2: I go forward to the trash bin(s) and keep that heading. I find the kitchen cabinets to my right: turn right.
Step 3: I go forward to the kitchen cabinets and keep that heading. I find the water pitcher to my right: turn right.
The turns are: back, right, right.
</think>

C
```
### i=150594 qid=qa86bfef1c621a3cf07641510 dataset=d2
Q: You are a robot beginning at the bag facing the clothes. You want to navigate to the coat. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn right.'): 1. [please fill in] 2. Go forward until the box 3. [please fill in] 4. Go forward until the bed 5. [please fill in] 6. Go forward until the coat. You have reached the final destination.
Options: ['A. Turn Back, Turn Left, Turn Left', 'B. Turn Left, Turn Left, Turn Left', 'C. Turn Right, Turn Left, Turn Right', 'D. Turn Right, Turn Right, Turn Right']
Answer field: D
```
<think>
Step 1: I stand at the bag facing the clothes. I find the box to my right: turn right.
Step 2: I go forward to the box and keep that heading. I find the bed to my right: turn right.
Step 3: I go forward to the bed and keep that heading. I find the coat to my right: turn right.
The turns are: right, right, right.
</think>

D
```


## Routing families (displacement, direction, rotation, absolute distance, feet units)
Five bound routing traces per family come from the loader audit of the parallel proof 171356 (kit p_9dd2fbb7, queued on general behind 171253); this part is appended when it lands. Routing stream admitted by 170956: 47,898 rows = 47,151 routing + 747 unit rows (683 feet drawn at cell 1.00; 64 inch rows stored, not drawn).
