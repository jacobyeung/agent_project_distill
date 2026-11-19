Primary threshold 0.5; visible valid operand-frames; percentages sum to 100 within rounding. Rows count distinct row IDs among records assigned to each group, including GT-absent records; area groups can overlap in rows. Full threshold sensitivity, IoU distributions, and candidate availability appear in SPLITS.json.

Datasets

| Group | Rows | Visible frames | No proposal % | Selected track absent % | Wrong instance % | Wrong class % | Partial % | Merged % | Other % | Correct % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| arkitscenes | 344 | 4133 | 15.0 | 23.3 | 0.0 | 0.6 | 6.9 | 2.1 | 6.9 | 45.1 |
| scannet | 72 | 1236 | 8.2 | 17.3 | 0.0 | 1.7 | 2.4 | 0.4 | 9.7 | 60.3 |
| scannetpp | 621 | 8424 | 29.4 | 14.5 | 0.0 | 3.4 | 1.5 | 3.5 | 6.3 | 41.4 |

Native GT frame share

| Group | Rows | Visible frames | No proposal % | Selected track absent % | Wrong instance % | Wrong class % | Partial % | Merged % | Other % | Correct % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| <0.5% | 1037 | 3253 | 54.5 | 21.0 | 0.0 | 5.3 | 0.2 | 2.6 | 7.0 | 9.3 |
| 0.5-1% | 657 | 1277 | 25.4 | 17.5 | 0.0 | 3.5 | 0.9 | 4.9 | 14.2 | 33.6 |
| 1-5% | 963 | 3978 | 17.9 | 15.2 | 0.0 | 1.8 | 2.8 | 4.1 | 10.0 | 48.3 |
| 5-20% | 845 | 3571 | 8.7 | 17.1 | 0.0 | 1.1 | 5.5 | 2.0 | 3.3 | 62.3 |
| >20% | 521 | 1714 | 4.6 | 15.8 | 0.0 | 0.3 | 7.0 | 0.4 | 0.8 | 71.1 |

Top 30 GT classes by distinct training rows

| Group | Rows | Visible frames | No proposal % | Selected track absent % | Wrong instance % | Wrong class % | Partial % | Merged % | Other % | Correct % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| door | 133 | 1111 | 4.9 | 14.9 | 0.0 | 0.4 | 2.9 | 1.4 | 4.6 | 71.1 |
| table | 125 | 1021 | 10.1 | 29.9 | 0.0 | 0.8 | 4.4 | 4.8 | 3.2 | 46.8 |
| tv | 122 | 561 | 7.0 | 11.6 | 0.0 | 0.9 | 0.7 | 2.7 | 8.0 | 69.2 |
| bed | 118 | 1085 | 16.2 | 26.9 | 0.0 | 9.3 | 1.6 | 7.5 | 17.3 | 21.2 |
| refrigerator | 117 | 770 | 21.0 | 18.6 | 0.0 | 0.1 | 1.4 | 0.1 | 2.6 | 56.1 |
| trash can | 98 | 562 | 25.3 | 16.0 | 0.0 | 3.2 | 0.0 | 1.8 | 15.1 | 38.6 |
| heater | 84 | 729 | 93.1 | 2.1 | 0.0 | 2.1 | 0.0 | 0.0 | 0.0 | 2.7 |
| toilet | 76 | 526 | 15.6 | 4.9 | 0.0 | 0.0 | 3.8 | 4.0 | 6.7 | 65.0 |
| stool | 71 | 284 | 23.6 | 16.5 | 0.0 | 1.4 | 5.3 | 2.8 | 6.0 | 44.4 |
| stove | 68 | 347 | 11.0 | 26.2 | 0.0 | 1.2 | 6.3 | 9.8 | 7.5 | 38.0 |
| chair | 67 | 420 | 11.4 | 20.2 | 0.0 | 1.0 | 5.7 | 0.0 | 15.0 | 46.7 |
| sofa | 64 | 431 | 20.4 | 17.2 | 0.0 | 0.9 | 3.9 | 3.2 | 1.4 | 52.9 |
| fireplace | 48 | 302 | 27.8 | 27.5 | 0.0 | 0.0 | 21.2 | 0.0 | 3.3 | 20.2 |
| telephone | 44 | 281 | 38.1 | 4.3 | 0.0 | 0.0 | 0.0 | 2.8 | 6.4 | 48.4 |
| laptop | 43 | 273 | 34.1 | 1.8 | 0.0 | 0.7 | 1.1 | 3.7 | 12.8 | 45.8 |
| bathtub | 41 | 409 | 14.2 | 14.4 | 0.0 | 0.0 | 10.5 | 0.0 | 3.4 | 57.5 |
| dishwasher | 41 | 184 | 30.4 | 23.9 | 0.0 | 0.0 | 7.1 | 1.6 | 10.9 | 26.1 |
| bookshelf | 39 | 357 | 30.8 | 15.7 | 0.0 | 0.0 | 5.6 | 7.6 | 7.8 | 32.5 |
| monitor | 37 | 237 | 5.5 | 8.0 | 0.0 | 0.4 | 3.8 | 3.0 | 0.8 | 78.5 |
| whiteboard | 37 | 317 | 12.9 | 9.8 | 0.0 | 3.2 | 6.0 | 0.9 | 6.9 | 60.3 |
| blanket | 36 | 317 | 23.3 | 23.0 | 0.0 | 0.0 | 0.6 | 0.0 | 1.9 | 51.1 |
| microwave | 32 | 147 | 42.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.5 | 49.7 |
| cup | 30 | 171 | 12.3 | 24.0 | 0.0 | 14.6 | 0.0 | 5.3 | 0.0 | 43.9 |
| kettle | 28 | 105 | 46.7 | 23.8 | 0.0 | 5.7 | 0.0 | 0.0 | 0.0 | 23.8 |
| keyboard | 27 | 129 | 18.6 | 24.8 | 0.0 | 0.8 | 0.0 | 0.0 | 2.3 | 53.5 |
| washer | 26 | 175 | 26.9 | 7.4 | 0.0 | 0.0 | 14.9 | 0.0 | 3.4 | 47.4 |
| power strip | 23 | 117 | 26.5 | 45.3 | 0.0 | 13.7 | 0.0 | 0.9 | 8.5 | 5.1 |
| basket | 22 | 89 | 46.1 | 9.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 44.9 |
| clock | 22 | 45 | 0.0 | 20.0 | 0.0 | 8.9 | 0.0 | 0.0 | 0.0 | 71.1 |
| table lamp | 21 | 133 | 19.5 | 15.8 | 0.0 | 0.0 | 0.0 | 12.8 | 0.8 | 51.1 |

