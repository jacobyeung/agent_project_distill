# Forty direction rows for manual parser validation

These are source text checks, not visual ground-truth checks. Full source hashes are in SOURCE_CENSUS.json.

## 1. q93384187bd2dd01b5b9ba774-p1_sb_rowD7f_a
Source: twins[3]; cell: direction; row SHA256: `16eba936af105377d0bc8e8836d9aa453c4df4207f3e81303c6510c4f2c5cddc`.
Question: If I am standing by the bicycle and facing away from the corded telephone, is the plank on my left or on my right?
Forward trace: Step 2: facing the corded telephone from the bicycle, I find the plank to my right.
Options: ["A. right", "B. left"]; selected answer: B.
Parsed: away / easy / lateral / left.

## 2. qfa46dc8d30ec2775c59ec14d_sb_rowD7f_a
Source: twins[0]; cell: direction; row SHA256: `b69ab7a12981bbdc42657064174cc7d8b7d448fe0373683996bf1a17c059eea0`.
Question: If I am standing by the wall speaker and facing away from the hand sanitizer dispenser, is the blackboard frame to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: facing the hand sanitizer dispenser from the wall speaker, I find the blackboard frame in front of me, on my right.
Options: ["A. front-right", "B. back-left", "C. front-left", "D. back-right"]; selected answer: B.
Parsed: away / hard / front / back-left.

## 3. q7ba148d2e4e7668784be0eb5-p1_sb_rowD7f_a
Source: twins[2]; cell: direction; row SHA256: `63b0959cddd3f1e9e98456d1c48e9d217376389fe4ee65504badbadabe11fe75`.
Question: If I am standing beside the belt and facing away from the hand truck, which direction describes the rolling whiteboards relative to me: front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: I find the rolling whiteboards behind me, on my right when I stand at the belt facing the hand truck.
Options: ["A. back-left", "B. back-right", "C. front-left", "D. front-right"]; selected answer: C.
Parsed: away / hard / behind / front-left.

## 4. q6c94f467ad0f40744de90e93
Source: store_v7[6]; cell: direction; row SHA256: `fdcd6938098c7b4040ea6ee25de39c468720e75f16acc3587d8c37979f0926d7`.
Question: If I am standing by the bottle and facing the bucket, is the stair to the left or the right of the bucket?
Forward trace: Step 2: I stand at the bottle facing the bucket; I find the stair to my right.
Options: ["A. right", "B. left"]; selected answer: A.
Parsed: toward / easy / lateral / right.

## 5. q631ec0c8d2907796dc382c99
Source: store_v7[0]; cell: direction; row SHA256: `c060335be9911f0d22ec08ce65a847a86a2d437e4e348b53d7808d87773e78ed`.
Question: If I am standing by the backpack and facing the file cabinet, is the books to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: facing the file cabinet from the backpack, I find the books behind me, on my left.
Options: ["A. back-left", "B. front-right", "C. back-right", "D. front-left"]; selected answer: A.
Parsed: toward / hard / behind / back-left.

## 6. q91148cb33247df4c97f60d6f
Source: store_v7[8]; cell: direction; row SHA256: `21f4ad0232c23f33f92c8dbfbe5d6c28d2138af13528c48aa0198f02fde1e28d`.
Question: If I am standing by the sink and facing the bathtub, is the toilet to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: I stand at the sink facing the bathtub; I find the toilet in front of me, on my right.
Options: ["A. front-right", "B. back-right", "C. front-left", "D. back-left"]; selected answer: A.
Parsed: toward / hard / front / front-right.

## 7. qfcf51efa7468aa2f24a026ed
Source: store_v7[5]; cell: direction; row SHA256: `d4d2880dd02477e00c2ad542d92d448ce82b50b2b2c5d91512cdfb7c73b6f7cd`.
Question: If I am standing by the coat hanger and facing the napkin dispenser, is the wall clock to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: Step 2: facing the napkin dispenser from the coat hanger, I find the wall clock behind me.
Options: ["A. back", "B. right", "C. left"]; selected answer: A.
Parsed: toward / medium / behind / back.

## 8. q1f0f6ef132355bf0d7be73b9
Source: store_v7[13]; cell: direction; row SHA256: `fb621b8176bc87d2aa03082e984bad533b939796da31302366b1a9120200a45f`.
Question: If I am standing by the binding machine and facing the paper stack, is the paper to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: Step 2: I find the paper ahead of me, slightly to my right when I stand at the binding machine facing the paper stack.
Options: ["A. left", "B. right", "C. back"]; selected answer: B.
Parsed: toward / medium / front / right.

## 9. vsi590k_041016_away
Source: store_v7[106497]; cell: facing_pairs; row SHA256: `aa5a94e7752f5e2ff416b93d72b94a10f7183f8ff4fe16745eda3d5810c38e08`.
Question: If I am standing by the refrigerator and with my back to the table, is the door to my left or to my right?
Forward trace: If I stood at the refrigerator facing the table, the door would be to my right.
Options: ["A. right", "B. left"]; selected answer: B.
Parsed: away / easy / lateral / left.

## 10. vsi590k_105564_away
Source: store_v7[106503]; cell: facing_pairs; row SHA256: `9716a0408d6cbba0eac32349853a1a707cd47b08f915a4d08ebc0e75edf1058a`.
Question: If I am standing by the chair and turned away from the bed, is the door to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: If I stood at the chair facing the bed, the door would be in front of me, on my left.
Options: ["A. front-right", "B. front-left", "C. back-right", "D. back-left"]; selected answer: C.
Parsed: away / hard / front / back-right.

## 11. vsi590k_094356_away
Source: store_v7[106507]; cell: facing_pairs; row SHA256: `84d8c84dcd1499873a7784d843ed3d8f991ef80232484f6e227009bd3f5c8034`.
Question: If I am standing by the toilet and turned away from the cutting board, is the laptop to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: If I stood at the toilet facing the cutting board, the laptop would be behind me, on my right.
Options: ["A. front-left", "B. back-right", "C. back-left", "D. front-right"]; selected answer: A.
Parsed: away / hard / behind / front-left.

## 12. vsi590k_118618_away
Source: store_v7[106495]; cell: facing_pairs; row SHA256: `87fddfafb9461ed13ddb22fa52d1cb13cfc9549c9a2cda996b64f5b5c97c1624`.
Question: If I am standing by the sofa and turned away from the cutting board, is the printer to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: If I stood at the sofa facing the cutting board, the printer would be ahead of me, slightly to my left.
Options: ["A. left", "B. right", "C. back"]; selected answer: C.
Parsed: away / medium / front / back.

## 13. vsi590k_117899_away
Source: store_v7[106493]; cell: facing_pairs; row SHA256: `e2107536d5dc4de01e6eab43ec93b79b4129e621160107440e4d5157a7ce84a9`.
Question: If I am standing by the heater and turned away from the door, is the toilet to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: If I stood at the heater facing the door, the toilet would be out to my left.
Options: ["A. right", "B. back", "C. left"]; selected answer: A.
Parsed: away / medium / lateral / right.

## 14. vsi590k_041016
Source: store_v7[106496]; cell: facing_pairs; row SHA256: `a16e6fdb2bf62d396a1511f53fe98ca90b871bac5ce50c26a5fe543afea60596`.
Question: If I am standing by the refrigerator and facing the table, is the door to the left or the right of the table?
Forward trace: Standing at the refrigerator facing the table, I find the door to my right.
Options: ["A. right", "B. left"]; selected answer: A.
Parsed: toward / easy / lateral / right.

## 15. vsi590k_094356
Source: store_v7[106506]; cell: facing_pairs; row SHA256: `3407389f6b1b0ce49374309d54eb4a03ac61520de8961523617ac05b859f4e18`.
Question: If I am standing by the toilet and facing the cutting board, is the laptop to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Standing at the toilet facing the cutting board, I find the laptop behind me, on my right.
Options: ["A. front-left", "B. back-right", "C. back-left", "D. front-right"]; selected answer: B.
Parsed: toward / hard / behind / back-right.

## 16. vsi590k_105564
Source: store_v7[106502]; cell: facing_pairs; row SHA256: `3db37776d19a42ce289cb1b972f47e0a24f13b2a9aa9d79e97a7c4e5253ddda8`.
Question: If I am standing by the chair and facing the bed, is the door to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Standing at the chair facing the bed, I find the door in front of me, on my left.
Options: ["A. front-right", "B. front-left", "C. back-right", "D. back-left"]; selected answer: B.
Parsed: toward / hard / front / front-left.

## 17. vsi590k_122144
Source: store_v7[106568]; cell: facing_pairs; row SHA256: `ca93ce81b813c13c751b68423e32f90ca8181a846b48184fd18c8522d5f66f95`.
Question: If I am standing by the printer and facing the door, is the laptop to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: Standing at the printer facing the door, I find the laptop behind me, on my right.
Options: ["A. back", "B. left", "C. right"]; selected answer: A.
Parsed: toward / medium / behind / back.

## 18. vsi590k_117899
Source: store_v7[106492]; cell: facing_pairs; row SHA256: `6d185e44b87a4cb2232abc16e718e3ec9b8bbea9cd4ab1f9ece633439704a4c3`.
Question: If I am standing by the heater and facing the door, is the toilet to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: Standing at the heater facing the door, I find the toilet out to my left.
Options: ["A. right", "B. back", "C. left"]; selected answer: C.
Parsed: toward / medium / lateral / left.

## 19. qd70b1a8939227f1174f19118
Source: store_v7[32]; cell: direction; row SHA256: `e4dad6239efff867c471e0e4610271b95897eb5526f82618292947ff7744d7f3`.
Question: Standing by the sofa, directed toward the door, does the slippers lie front-left, front-right, back-left, or back-right from my viewpoint?
Forward trace: Step 2: facing the door from the sofa, I find the slippers in front of me, on my left.
Options: ["A. front-left", "B. back-left", "C. back-right", "D. front-right"]; selected answer: A.
Parsed: toward / hard / front / front-left.

## 20. q77789a11e904febcf5273927
Source: store_v7[33]; cell: direction; row SHA256: `98c56fa91e53d3fb60f4447ee9eeeea5998e573009f0d17b10ce7bf69e535acf`.
Question: If I'm at the chair, oriented toward the blanket, which quadrant is the table in: front-left, front-right, back-left, or back-right?
Forward trace: Step 2: I find the table in front of me, on my left when I stand at the chair facing the blanket.
Options: ["A. back-right", "B. front-left", "C. front-right", "D. back-left"]; selected answer: B.
Parsed: toward / hard / front / front-left.

## 21. q0147648b8e033adf6fe3a45c
Source: store_v7[523]; cell: direction; row SHA256: `63a6194472449b1288c1ad1930a02945e23c0e4702e13db1b93f42f760476f88`.
Question: At the file folder, with my gaze fixed on the trash can, is the laptop positioned front-left, front-right, back-left, or back-right relative to me?
Forward trace: Step 2: I find the laptop in front of me, on my left when I stand at the file folder facing the trash can.
Options: ["A. back-right", "B. front-right", "C. front-left", "D. back-left"]; selected answer: C.
Parsed: toward / hard / front / front-left.

## 22. q455e5e034f26be831a2f0e6b
Source: store_v7[88]; cell: direction; row SHA256: `55c91f5fc2432d22f51e19d8f302a3ab15d793c0c3810e75afd9ca3a5bf98189`.
Question: If I position myself at the blanket, aiming toward the refrigerator, is the heater to my left, right, or behind me? Behind signifies at least a 135-degree rotation is required.
Forward trace: Step 2: standing at the blanket and facing the refrigerator, I find the heater ahead of me, slightly to my right.
Options: ["A. right", "B. back", "C. left"]; selected answer: A.
Parsed: toward / medium / front / right.

## 23. qea4ecb8c66f373153fba21a5
Source: store_v7[306]; cell: direction; row SHA256: `bffe4da794416d96bd3e2d0ccc269db5124ce7815889331c9426006bb2da6342`.
Question: When standing next to the bed and gazing at the bookshelf, would the window be on my left, right, or behind? Behind indicates needing to turn 135 degrees or more to face it.
Forward trace: Step 2: standing at the bed and facing the bookshelf, I find the window ahead of me, slightly to my left.
Options: ["A. right", "B. left", "C. back"]; selected answer: B.
Parsed: toward / medium / front / left.

## 24. q27182815af3b008a14c996bb
Source: store_v7[416]; cell: direction; row SHA256: `bb42827bd5a0fcc695e23dc06bbb71cec54fa49e4ffc61e5e0701816ce35614d`.
Question: If I am near the refrigerator, turned toward the cushion, is the blanket found on my left, right, or rear? To my rear means rotating at least 135 degrees.
Forward trace: Step 2: I find the blanket ahead of me, slightly to my right when I stand at the refrigerator facing the cushion.
Options: ["A. back", "B. left", "C. right"]; selected answer: C.
Parsed: toward / medium / front / right.

## 25. q243d839034d7d50cee9c00c0
Source: store_v7[226]; cell: direction; row SHA256: `8895c5f695468909444bfea7c688b9c44c19aa05b50bf02998f25528e678707f`.
Question: Standing near the microwave, directing my view towards the slippers, is the trash can located left, right, or behind? Behind means I would turn 135 degrees or more to face it.
Forward trace: Step 2: I find the trash can behind me when I stand at the microwave facing the slippers.
Options: ["A. right", "B. left", "C. back"]; selected answer: C.
Parsed: toward / medium / behind / back.

## 26. q55ef80e5e1b9c43cae2c618f
Source: store_v7[268]; cell: direction; row SHA256: `7c2504bb5f261b91c202d6a6584cefface3aea2fc4d382710c1febad626332df`.
Question: Standing adjacent to the door and viewing the table lamp, is the bookshelf on the left side or the right side?
Forward trace: Step 2: facing the table lamp from the door, I find the bookshelf to my right.
Options: ["A. right", "B. left"]; selected answer: A.
Parsed: toward / easy / lateral / right.

## 27. qfe51ef38252e3bc475788a28
Source: store_v7[437]; cell: direction; row SHA256: `b51b1b7c2bc4333710fcd43b7bdb0305afea678aab9e595dc26b81e9aeb73d91`.
Question: With the tv next to me and the heater ahead, is the door positioned on the left or right of the heater?
Forward trace: Step 2: I find the door to my right when I stand at the tv facing the heater.
Options: ["A. right", "B. left"]; selected answer: A.
Parsed: toward / easy / lateral / right.

## 28. vsi590k_116616_away_opp
Source: store_v7[195902]; cell: facing_pairs; row SHA256: `3aac1357ce819fdcc29b4d26f59be7d1afea649af8dc413a52f2c51b508023ca`.
Question: If I am standing by the whiteboard and facing in the opposite direction of the cup, is the file folder to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: If I stood at the whiteboard facing the cup, the file folder would be ahead of me, slightly to my left.
Options: ["A. right", "B. left", "C. back"]; selected answer: C.
Parsed: away / medium / front / back.

## 29. vsi590k_248000_away
Source: store_v7[106519]; cell: facing_pairs; row SHA256: `c537c9d867d1dde166fd21e82f71961cf135a4e5f6e725c820adf63d3259196f`.
Question: If I am standing by the stool and facing away from the stove, is the sofa to my left or to my right?
Forward trace: If I stood at the stool facing the stove, the sofa would be to my left.
Options: ["A. right", "B. left"]; selected answer: A.
Parsed: away / easy / lateral / right.

## 30. vsi590k_092653_away
Source: store_v7[106513]; cell: facing_pairs; row SHA256: `9de346beb5d1f9b9fc87497d5bbc85182a5d001274edc45f8582a4551cbc44e2`.
Question: If I am standing by the bookshelf and facing away from the whiteboard, is the tv to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: If I stood at the bookshelf facing the whiteboard, the tv would be in front of me, on my right.
Options: ["A. front-left", "B. back-right", "C. front-right", "D. back-left"]; selected answer: D.
Parsed: away / hard / front / back-left.

## 31. vsi590k_107953_away
Source: store_v7[106521]; cell: facing_pairs; row SHA256: `222274ad2b3033cdd7544408835f26f7ee87831b961173a38970e7426eb0c83b`.
Question: If I am standing by the door and facing away from the tv, is the whiteboard to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: If I stood at the door facing the tv, the whiteboard would be behind me, on my left.
Options: ["A. front-right", "B. back-right", "C. back-left", "D. front-left"]; selected answer: A.
Parsed: away / hard / behind / front-right.

## 32. vsi590k_020716_away
Source: store_v7[106505]; cell: facing_pairs; row SHA256: `74656c36d4c7a300b5e5fcbb16254ee96b4c1c20e70a7c15f344174fa5c743bd`.
Question: If I am standing by the door and turned away from the lamp, is the tv to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.
Forward trace: If I stood at the door facing the lamp, the tv would be out to my right.
Options: ["A. left", "B. right", "C. back"]; selected answer: A.
Parsed: away / medium / lateral / left.

## 33. q5d0e4c524c4837c0f27d065b
Source: store_v7[11]; cell: direction; row SHA256: `454772f25b0e65915e2b3f2f2ceb58cbd1316eb24bc97761adccea621d674c18`.
Question: If I am standing by the washer and facing the toilet, is the shelf to the left or the right of the toilet?
Forward trace: Step 2: I find the shelf to my left when I stand at the washer facing the toilet.
Options: ["A. left", "B. right"]; selected answer: A.
Parsed: toward / easy / lateral / left.

## 34. q0737771aa94a93d985b7bce4
Source: store_v7[21]; cell: direction; row SHA256: `4464bccf7655079cbbc1fb32d2849674abd0b8f91725dc058fe8e4745d7270b1`.
Question: If I am standing by the backpack and facing the pet bed, is the pet feeding plates to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: I find the pet feeding plates behind me, on my right when I stand at the backpack facing the pet bed.
Options: ["A. back-right", "B. front-right", "C. front-left", "D. back-left"]; selected answer: A.
Parsed: toward / hard / behind / back-right.

## 35. qe02848cba9df354303b30ac6
Source: store_v7[25]; cell: direction; row SHA256: `3d647500babd556a7140ca2dada694f64d93ce166c4a94596df9890d55a7ddc4`.
Question: If I am standing by the toilet and facing the chair, is the sink to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: I stand at the toilet facing the chair; I find the sink in front of me, on my left.
Options: ["A. back-right", "B. front-left", "C. back-left", "D. front-right"]; selected answer: B.
Parsed: toward / hard / front / front-left.

## 36. q590298085ce6fa70720b910b
Source: store_v7[42]; cell: direction; row SHA256: `20fd4130e51fb2f207493c0e0c004010313e660eacbbecb7ee1e6c4d64717e2b`.
Question: Facing the microwave from the sofa, would the plant be placed left, right, or behind me? 'Behind' means I'd have to turn at least 135 degrees.
Forward trace: Step 2: facing the microwave from the sofa, I find the plant out to my left.
Options: ["A. right", "B. back", "C. left"]; selected answer: C.
Parsed: toward / medium / lateral / left.

## 37. q6a6f052578307dec8b318565-p1_sb_rowD7f_a
Source: twins[4]; cell: direction; row SHA256: `24dbba6354917b2fbd9f512807234795312e73da291d97d55e0e0c5de6958da4`.
Question: From a position beside the beverage carton, face away from the hanging calendar. Is the poster to your left or right?
Forward trace: Step 2: standing at the beverage carton and facing the hanging calendar, I find the poster to my left.
Options: ["A. left", "B. right"]; selected answer: B.
Parsed: away / easy / lateral / right.

## 38. q72d2cf27095d11f7ed52ffee-p1_sb_rowD7f_a
Source: twins[7]; cell: direction; row SHA256: `3c2444f0600d3f8557d5278a6d19c87b0795b302437e8c15213d9c0d8ab5fd59`.
Question: From beside the bag, I face away from the basket. Which direction describes the hand mixer relative to me: front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: standing at the bag and facing the basket, I find the hand mixer in front of me, on my left.
Options: ["A. front-left", "B. front-right", "C. back-right", "D. back-left"]; selected answer: C.
Parsed: away / hard / front / back-right.

## 39. q49dd87a214a72327963f7d1e-p1_sb_rowD7f_a
Source: twins[8]; cell: direction; row SHA256: `676bced960628d1262136c304a968c1c1a212f6e86743fd7bda178982f519086`.
Question: From beside the book, I face away from the flag. Which direction describes the record player relative to me: front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).
Forward trace: Step 2: I stand at the book facing the flag; I find the record player behind me, on my left.
Options: ["A. front-right", "B. back-right", "C. back-left", "D. front-left"]; selected answer: A.
Parsed: away / hard / behind / front-right.

## 40. vsi590k_251080_away
Source: store_v7[136991]; cell: facing_pairs; row SHA256: `01d5495926c6dd374478e7c48925726c69cb58f6dba64835ef27fc430d7c1dda`.
Question: If I am standing by the dishwasher and with my back to the stove, is the refrigerator to my left or to my right?
Forward trace: If I stood at the dishwasher facing the stove, the refrigerator would be to my left.
Options: ["A. right", "B. left"]; selected answer: A.
Parsed: away / easy / lateral / right.

