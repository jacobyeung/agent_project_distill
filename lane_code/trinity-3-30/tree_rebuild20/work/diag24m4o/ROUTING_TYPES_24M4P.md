The supplied 173680 evidence does not determine the full per-type verdict. The final CPU publisher counts the actual N routing database; it never estimates its type counts from a source-name histogram.

| Type | N rows implied by supplied evidence | Expected rows/step | P quota | Percent off |
| --- | ---: | ---: | ---: | ---: |
| camera_displacement | 10035–14020 (unmeasured) | 14.9008–20.8181 | 18.25 | unmeasured |
| camera_movement_direction | 8275–12260 (unmeasured) | 12.2874–18.2047 | 15.88 | unmeasured |
| camera_rotation | 5158–9143 (unmeasured) | 7.6590–13.5763 | 12.53 | unmeasured |
| absolute_distance | 10945 | 16.252059 | 16.34 | -0.5382% |
| units | 718 | 1.066147 | 1.00 | +6.6147% |

N has 43,101 rows: 31,438 camera rows, 10,945 absolute-distance rows, and 718 units rows. The 3,985 missing camera rows have no full type breakdown in the supplied artifacts. Units pass both the ±10% relative test and the minimum of 0.90 rows/step; absolute distance also passes. Source counts alone imply neither PASS nor FAIL for all five types. TYPE_EVIDENCE_173680.json gives both a passing and a failing hypothetical camera split consistent with those totals; these are bounds, not measurements.

The units classifier follows r1_population.family: a routing ground_record.unit or a0_units_ QID selects units before the distance type. A recovery marker selects recovery and causes the five-type table to fail as an extra type. Unknown types and an empty database also fail. Every known type must be within 10% inclusively; zero-unit rows fail. The CPU helper writes routing_types.json even when P validation or sample publication is unavailable. No config delta is built.
