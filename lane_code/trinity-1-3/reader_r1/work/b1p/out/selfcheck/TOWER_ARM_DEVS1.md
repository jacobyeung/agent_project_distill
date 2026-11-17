# Step-544 own and tower pairing

Differences are own minus tower in percentage points. Intervals resample paired rooms 10,000 times with seed 20261115.
Missing items remain missing; incomplete types cannot establish the take-over bar.

| Rule | Type | Paired / expected | Paired own | Paired tower | Difference [95% interval] | Bar met |
|---|---|---:|---:|---:|---|---|
| null_argmax | camera_displacement | 150 / 150 | 47.2000 | 47.2000 | 0.0000 [0.0000, 0.0000] | None |
| null_argmax | camera_rotation | 150 / 150 | 42.7333 | 42.7333 | 0.0000 [0.0000, 0.0000] | None |
| null_argmax | camera_movement_direction | 150 / 150 | 75.3333 | 75.3333 | 0.0000 [0.0000, 0.0000] | None |
| null_argmax | object_abs_distance | 150 / 150 | 20.0000 | 20.0000 | 0.0000 [0.0000, 0.0000] | None |
| null_argmax | room_size_estimation | 36 / 36 | 13.8889 | 13.8889 | 0.0000 [0.0000, 0.0000] | None |

## Distance: null_argmax

150 reads; 33 capped (0.2200). MRA: 0.2000 on all units, 0.2977 on 43 metre questions, and 0.2448 on 87 reads without a failed ground.
No ground call has a status other than selected; includes reads with no ground calls.

| Status in any call | Reads | Share |
|---|---:|---:|
| error: malformed_v313_call | 1 | 0.0067 |
| not seen | 63 | 0.4200 |
| returned | 86 | 0.5733 |
| selected | 138 | 0.9200 |
| unserved | 33 | 0.2200 |

Status shares can overlap within a read. Capped calls remain unserved.

| Ground diagnostic stage | Calls |
|---|---:|
| diagnostics missing | 368 |
| candidates_argmax | object_abs_distance | 150 / 150 | 20.0000 | 20.0000 | 0.0000 [0.0000, 0.0000] | None |

## Distance: candidates_argmax

150 reads; 33 capped (0.2200). MRA: 0.2000 on all units, 0.2977 on 43 metre questions, and 0.2448 on 87 reads without a failed ground.
No ground call has a status other than selected; includes reads with no ground calls.

| Status in any call | Reads | Share |
|---|---:|---:|
| error: malformed_v313_call | 1 | 0.0067 |
| not seen | 63 | 0.4200 |
| returned | 86 | 0.5733 |
| selected | 138 | 0.9200 |
| unserved | 33 | 0.2200 |

Status shares can overlap within a read. Capped calls remain unserved.

| Ground diagnostic stage | Calls |
|---|---:|
| diagnostics missing | 368 |

## Missing keys

null_argmax, camera_displacement: missing own []; missing tower [].
null_argmax, camera_rotation: missing own []; missing tower [].
null_argmax, camera_movement_direction: missing own []; missing tower [].
null_argmax, object_abs_distance: missing own []; missing tower [].
null_argmax, room_size_estimation: missing own []; missing tower [].
candidates_argmax, object_abs_distance: missing own []; missing tower [].

## Per-call errors

The following errors use the package scorer. Every call, including unserved and nonnumeric responses, is retained in `curve.json` under `per_call_errors`.

| Rule | Item | Call index | Status | Metre error | Degree error | Direction correct |
|---|---|---:|---|---:|---:|---|
| own | devs1cam-0020d0cefc26c693abeb6c4e5951cc07 | 0 | returned | 0.3100 | n/a | n/a |
| own | devs1cam-00729c5db90fc5d0c5281ed7ce889dca | 0 | returned | n/a | n/a | True |
| own | devs1cam-02240d9bcaf9703226aa03c98e9f2d6e | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-05ce2ad29e7353ab8b808abe3df89f0d | 0 | returned | n/a | n/a | True |
| own | devs1cam-05eff7f66869bc50118d2e0d84d927df | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-069c4a4fb2b94413b432b3abc2d66ac2 | 0 | returned | n/a | 12.0000 | n/a |
| own | devs1cam-07b1a63813a4733a042538e350e265eb | 0 | returned | 0.1500 | n/a | n/a |
| own | devs1cam-088f1e3c275fb323293f10b356d740a2 | 0 | returned | 0.2200 | n/a | n/a |
| own | devs1cam-0a369d6600f61cc6c3e15cb9e954e689 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-0ab1b7c5ac60d3d2550706a3cdce8b29 | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-0adb11f9bb13b47d9d937ab72f8e2eea | 0 | returned | 0.1400 | n/a | n/a |
| own | devs1cam-0baec18afce655dae16a404906102533 | 0 | returned | 0.0000 | n/a | n/a |
| own | devs1cam-0bbc754c75556e9403d471951304183b | 0 | returned | 0.2300 | n/a | n/a |
| own | devs1cam-0c0b001891172c79b9b8caa6fef84bda | 0 | returned | 0.2000 | n/a | n/a |
| own | devs1cam-0cdcb2a08007772ca78ae5d7a6c9b886 | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-0d0cf0791c32f428cfacf34bc5b66f6a | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-0d4180723a5d9942daa277d9466db301 | 0 | returned | n/a | n/a | True |
| own | devs1cam-0d591bfbb81d0bac9261869201786807 | 0 | returned | n/a | n/a | True |
| own | devs1cam-0e6c9965c28858ab6a0d70649e9f7801 | 0 | returned | n/a | n/a | True |
| own | devs1cam-0f41e5b96a3bf8f5c9d748d663448c88 | 0 | returned | n/a | n/a | True |
| own | devs1cam-0f558e8f2f579ecce0a2173b1505584d | 0 | returned | n/a | n/a | True |
| own | devs1cam-1054354c3c441728e37e87dc7bbd6a68 | 0 | returned | n/a | n/a | False |
| own | devs1cam-1142c5ca6feafd58d27489b2166b42ba | 0 | returned | 0.0700 | n/a | n/a |
| own | devs1cam-138cccbfe6d3bb26b10f50e1cae6a0d4 | 0 | returned | n/a | 0.0000 | n/a |
| own | devs1cam-13c1d6e42464ff095b5000e82d782009 | 0 | returned | n/a | 6.0000 | n/a |
| own | devs1cam-13e0fc3df819bbe48fd3e13644508b18 | 0 | returned | 0.1100 | n/a | n/a |
| own | devs1cam-14bd1afd2f3737fcb8c72811b82dbcd1 | 0 | returned | n/a | n/a | True |
| own | devs1cam-15f434c2d7e5cabf4baa6425706378c0 | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-164f3c63246cf1801e39bd68179b25c6 | 0 | returned | n/a | 19.0000 | n/a |
| own | devs1cam-16c216a1c82e3d8e6ac2410cb5a6356b | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-17e826c7e7031b84a5d88c7ce16623a6 | 0 | returned | 0.4600 | n/a | n/a |
| own | devs1cam-1976e69d628ad042a97c896d57221682 | 0 | returned | 0.6100 | n/a | n/a |
| own | devs1cam-198336f8bdf6985012b777f57d49cced | 0 | returned | n/a | 90.0000 | n/a |
| own | devs1cam-19baad91803f182449ea525bb1c95521 | 0 | returned | 0.1800 | n/a | n/a |
| own | devs1cam-1a0cee7f65e591a5590179ec2b8cdfa9 | 0 | returned | n/a | n/a | True |
| own | devs1cam-1a1863a10468af67b7244bdebd30b073 | 0 | returned | n/a | n/a | True |
| own | devs1cam-1a2a6eee4de7efd195338e9547b105c4 | 0 | returned | 2.2700 | n/a | n/a |
| own | devs1cam-1a33fc17ab1eb437d771e9f981ea8832 | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-1b61a955e284dbebb14768fdd95ebc9b | 0 | returned | n/a | n/a | True |
| own | devs1cam-1b7ba80e4a37097641e4c6abd2387e07 | 0 | returned | n/a | 90.0000 | n/a |
| own | devs1cam-1c4baf0dcb39c0575ae19014ac6fade7 | 0 | returned | n/a | n/a | True |
| own | devs1cam-1c639bff1680ba444816cdfe4a391af9 | 0 | returned | n/a | 11.0000 | n/a |
| own | devs1cam-1d60e77e9e48d47d63d61c2e735686a9 | 0 | returned | 2.4400 | n/a | n/a |
| own | devs1cam-1dcd9643f274d9b9cfa4c80b4ce59652 | 0 | returned | n/a | 50.0000 | n/a |
| own | devs1cam-1e32b030462621630cc2f907576af887 | 0 | returned | n/a | 43.0000 | n/a |
| own | devs1cam-1e82b04d17a1e723669d4385fef93ebe | 0 | returned | 6.0300 | n/a | n/a |
| own | devs1cam-1ed3c6004b63451bde7ffa3c6c12e2e4 | 0 | returned | n/a | 14.0000 | n/a |
| own | devs1cam-2145b0bdf8607a7d4c289b00ca7fb16a | 0 | returned | n/a | 22.0000 | n/a |
| own | devs1cam-227f221890b5efcf2a6517ff68226723 | 0 | returned | n/a | n/a | True |
| own | devs1cam-229e7bdf910b966f2218a59c4d1e1273 | 0 | returned | 0.7200 | n/a | n/a |
| own | devs1cam-23e4a31e0df1e0b06b7c9f43c1a5d641 | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-23f04fb2b67c5c545d592b39d8d52c97 | 0 | returned | n/a | n/a | True |
| own | devs1cam-247c686a26ebecb5097ee688577ec62a | 0 | returned | n/a | n/a | False |
| own | devs1cam-24fc408c05e4d666b6fb1e89d218f5d9 | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-252cc74fcb20a299b88bb5a7ceee5d60 | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-25a2d02602e3865726da5f94f1043f19 | 0 | returned | n/a | n/a | True |
| own | devs1cam-25b79a6f4a93cac75556e6f4dfcb243e | 0 | returned | n/a | n/a | False |
| own | devs1cam-25d51266f56ad4b02b7d8ed70c27ce52 | 0 | returned | n/a | 126.0000 | n/a |
| own | devs1cam-25d7016a7ea1bf023f76948fdd9deaeb | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-261616c5055d35a90c5d584eb897193c | 0 | returned | n/a | n/a | True |
| own | devs1cam-27bac7d0c462e80b3395e5923e3bdcd3 | 0 | returned | 0.0100 | n/a | n/a |
| own | devs1cam-27da9a85bf26dc4dbd9f9d0c6e40f59d | 0 | returned | n/a | n/a | False |
| own | devs1cam-28389a5db258677ec602acb20f27840e | 0 | returned | n/a | n/a | True |
| own | devs1cam-287a70b200cc988bdc196baddcfba2ee | 0 | returned | n/a | n/a | True |
| own | devs1cam-28efb0393e32b223347815cfe18adec4 | 0 | returned | n/a | 16.0000 | n/a |
| own | devs1cam-295b5a2706d771d9bea92573137194ce | 0 | returned | n/a | n/a | True |
| own | devs1cam-29773f44cdd54eeee982a0498d024951 | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-2a2cb97664b1c93f39fbb6153c07d305 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-2a80598ada0b258686ce5f8c24257ae6 | 0 | returned | n/a | n/a | True |
| own | devs1cam-2c3e51248e313ee107d8bf9a312a0212 | 0 | returned | n/a | 159.0000 | n/a |
| own | devs1cam-2c8c72894ccbffdc9d46321f66ec8090 | 0 | returned | n/a | 126.0000 | n/a |
| own | devs1cam-2caddcb84c0bc23b0d89ba3003bfba57 | 0 | returned | n/a | n/a | True |
| own | devs1cam-2cd565588214cafe7715bfa386c15341 | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-2d2f184399fce90f8ef087a67303096a | 0 | returned | 0.0400 | n/a | n/a |
| own | devs1cam-2d6247bfc8f1ff68196e8e0321a20c6d | 0 | returned | 1.8400 | n/a | n/a |
| own | devs1cam-2d770696a926df52f2f9e3414a53efd8 | 0 | returned | 1.1400 | n/a | n/a |
| own | devs1cam-2de4909ee3577f17c78c77a2e9e29317 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-2ea3d5c02118a891bfc300d2f2f28ca7 | 0 | returned | n/a | 11.0000 | n/a |
| own | devs1cam-2f4c478745e39b6f1e29fd1706ed5bf0 | 0 | returned | 0.8300 | n/a | n/a |
| own | devs1cam-2f6b04a35cb285aebf8a567c9422fd65 | 0 | returned | 0.0100 | n/a | n/a |
| own | devs1cam-2f76f5acd2a8a198a57edc57900b21a5 | 0 | returned | n/a | n/a | True |
| own | devs1cam-2fa02399c753a95355ec261aa49813ff | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-2fd5bd894c6b7ae7098f6e7f8a0c88d4 | 0 | returned | n/a | n/a | True |
| own | devs1cam-2fe8882e1b6e7b4bd3f9230e9add461c | 0 | returned | n/a | n/a | True |
| own | devs1cam-30f0f38919466d58f06d53f632cdd2a1 | 0 | returned | 0.2000 | n/a | n/a |
| own | devs1cam-311f577252a264592c0d796210ee8cb0 | 0 | returned | 0.1800 | n/a | n/a |
| own | devs1cam-31cffb00c5dba885767d5428b673bdfb | 0 | returned | n/a | n/a | True |
| own | devs1cam-31d9eac811eb11717a53fffe9583f9f0 | 0 | returned | 0.3500 | n/a | n/a |
| own | devs1cam-332f6cace3baf8c061dc536c7a4dd243 | 0 | returned | n/a | n/a | True |
| own | devs1cam-348a9e022f27ac67031f55b8b0167ba3 | 0 | returned | 0.1800 | n/a | n/a |
| own | devs1cam-35f6b028403fc915f5ee1839ac0fc7e8 | 0 | returned | 0.1400 | n/a | n/a |
| own | devs1cam-36625cf9ab3cf88b534b4385238f2f12 | 0 | returned | n/a | 29.0000 | n/a |
| own | devs1cam-369e6305542730f6ae91fb214dc1fbd1 | 0 | returned | n/a | n/a | False |
| own | devs1cam-389218694a6e46678a1f993e09e0bfec | 0 | returned | 0.9300 | n/a | n/a |
| own | devs1cam-38cae6cbe5a8ef1abb1ff04b2cd51dc5 | 0 | returned | n/a | n/a | False |
| own | devs1cam-3a9f05dfb4de4e999fcfa728533858e2 | 0 | returned | n/a | n/a | True |
| own | devs1cam-3b06cb0a2e8face562911a02f71d8623 | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-3b299b26636d3d0b30d139a507bbaa96 | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-3b3bd31478f32ba1744edd3c3dbea8aa | 0 | returned | n/a | n/a | True |
| own | devs1cam-3c209557bfc86a182a9952f28e04221a | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-3d1603b2e5b652d907876bdb15597177 | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-3d52edf5468c4207061fa53bfbf09c1c | 0 | returned | 0.3000 | n/a | n/a |
| own | devs1cam-3db00ce69e697a9d3abeac27819a3ae6 | 0 | returned | 0.2400 | n/a | n/a |
| own | devs1cam-3e82dd97532a1b9786af2d973c1c39f5 | 0 | returned | n/a | n/a | True |
| own | devs1cam-3ea4d987de4dbedecb40ca902d836b1f | 0 | returned | n/a | n/a | True |
| own | devs1cam-3f22bf92384123d71d26d8c6811ceb35 | 0 | returned | n/a | 12.0000 | n/a |
| own | devs1cam-3f4559da4d4b5f856fcce3cc817c55dc | 0 | returned | n/a | 18.0000 | n/a |
| own | devs1cam-3fa79d1a487810e1b48b4c30ddda88a5 | 0 | returned | 2.9600 | n/a | n/a |
| own | devs1cam-40263b40dfc3078be2ba9eb3258bf439 | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-4162d0dbfce5adfc5875d80199370621 | 0 | returned | 0.7500 | n/a | n/a |
| own | devs1cam-41f0ee22c9b241d8d745406680121021 | 0 | returned | n/a | n/a | True |
| own | devs1cam-42142c541ad2b875c1539f5e85e69feb | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-44076714b5ef1e416bb5e9f7140d2a09 | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-44476730608f5c7d6a8a8340713399df | 0 | returned | n/a | n/a | True |
| own | devs1cam-453f94505fe0f14d25cb80c5088e6f72 | 0 | returned | n/a | 0.0000 | n/a |
| own | devs1cam-45ed5c9e944f8f16079231feb6c2d941 | 0 | returned | 0.8300 | n/a | n/a |
| own | devs1cam-48807cbe2a627252c8d48966af2ac778 | 0 | returned | n/a | n/a | True |
| own | devs1cam-49dbcdf686b199381d65e13d07b1e14e | 0 | returned | 0.1300 | n/a | n/a |
| own | devs1cam-4a315b8a07d782753f8625a1dc0439ae | 0 | returned | n/a | 12.0000 | n/a |
| own | devs1cam-4a3ee8096e8a2d087746a7e9bb45bc7d | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-4aaef73ef8f7374b3318805e5788836a | 0 | returned | n/a | n/a | True |
| own | devs1cam-4b4e285c9b22b922af7ed6684d129445 | 0 | returned | n/a | 11.0000 | n/a |
| own | devs1cam-4c8b8d552a6c0ed8f7c575d9fe34b0f7 | 0 | returned | n/a | n/a | False |
| own | devs1cam-4d34ad1ab67f1406fb84bf183d091ef7 | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-4db02514fa675dbd1ed5cbcfb84f1130 | 0 | returned | n/a | n/a | False |
| own | devs1cam-4e15e17068eec1a23a601e9615dc2c77 | 0 | returned | n/a | 14.0000 | n/a |
| own | devs1cam-4faed4682687658d4cce9053ce6ae9e6 | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-504a8f836ec9b59ff4a1b3722de9e280 | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-50b26c5a65f68c7184c6827117eb3145 | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-50d8b3491b4136fe011ab45a48ddc79d | 0 | returned | n/a | n/a | True |
| own | devs1cam-5243d62cb1b1e112d1c18b3bca988c57 | 0 | returned | n/a | 12.0000 | n/a |
| own | devs1cam-53d3069b9da4533486ef2527d1c5483f | 0 | returned | 0.5400 | n/a | n/a |
| own | devs1cam-53fb8eb60d82ce1054bc4bfe900bdd5c | 0 | returned | 0.3700 | n/a | n/a |
| own | devs1cam-54062ce87aa7bd7a3d1f520e657648b4 | 0 | returned | 0.7900 | n/a | n/a |
| own | devs1cam-542eb42026788cc63df9e5a0ed9aae46 | 0 | returned | 0.2800 | n/a | n/a |
| own | devs1cam-55215ec664298583c3cfb0e2873a86a0 | 0 | returned | n/a | n/a | True |
| own | devs1cam-55737eb70f6647fb31984bebad82c03f | 0 | returned | n/a | n/a | True |
| own | devs1cam-5603d546987bf298034c320fd4030fe0 | 0 | returned | n/a | n/a | False |
| own | devs1cam-5640abcbd1882f1be581ed84194b82a1 | 0 | returned | n/a | 27.0000 | n/a |
| own | devs1cam-56637b6125f18410bdfca24073fd453e | 0 | returned | n/a | n/a | True |
| own | devs1cam-578e23b84ba6a586db309e68eff43d9e | 0 | returned | 0.6800 | n/a | n/a |
| own | devs1cam-584ed12038aeaf7de02484f2d59de464 | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-58775077eff086d079ffdaf4a2a85443 | 0 | returned | n/a | n/a | True |
| own | devs1cam-58b41f71b4e5883894beae8dccb7e99e | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-5972b10244779f08bf3dde7bf43c3074 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-59ab36f70477becdd652ee11b3366880 | 0 | returned | n/a | n/a | True |
| own | devs1cam-5a35be901ad65075a70c92ebe3fea1db | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-5a3b79130e94e0a9727ae3ec32d04ce8 | 0 | returned | 0.0800 | n/a | n/a |
| own | devs1cam-5b8fb5dd49158ebeb45c42704076caa5 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-5b98ada09a663b4e3ec06701022acee6 | 0 | returned | n/a | n/a | True |
| own | devs1cam-5ba10abff65a66ad9d955a50fc844d8c | 0 | returned | 0.5000 | n/a | n/a |
| own | devs1cam-5bd21da4b35e5360f27e75d6cdadf114 | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-5c4f40c19d29304493a4e340e2fbdb11 | 0 | returned | 3.2300 | n/a | n/a |
| own | devs1cam-5dc99fae7c27b2ad92d5788691ebc75f | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-5df62da4b1dd2e6e77486bb2cdf8d769 | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-5f9724339c1393d9cbdc605c301b0b26 | 0 | returned | n/a | n/a | False |
| own | devs1cam-60346f2b71cd2003c082cc86d8a56989 | 0 | returned | n/a | n/a | False |
| own | devs1cam-61abc3d389b77c34d7e311fbdbba54fa | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-63862a6912ad716a4e4fd35af9b591f9 | 0 | returned | 0.2000 | n/a | n/a |
| own | devs1cam-642f7803436e63d24fbe54a14b784cb5 | 0 | returned | 0.3700 | n/a | n/a |
| own | devs1cam-648c86f02e008d0d922da63705103589 | 0 | returned | 0.1000 | n/a | n/a |
| own | devs1cam-64b76ac73df298f7222625e1fdd2e222 | 0 | returned | n/a | n/a | True |
| own | devs1cam-6548f6320506db01af213699ff2d37cd | 0 | returned | n/a | 16.0000 | n/a |
| own | devs1cam-655b1f6a401470c178e86c28210edb22 | 0 | returned | n/a | n/a | True |
| own | devs1cam-662b57eea66bab52aa22d0c26a468735 | 0 | returned | 0.3300 | n/a | n/a |
| own | devs1cam-67088ff4bd269377c9afbe466856c732 | 0 | returned | 0.6000 | n/a | n/a |
| own | devs1cam-6746124474529d17b5c54c12a6f11bba | 0 | returned | n/a | 27.0000 | n/a |
| own | devs1cam-675db7e44fe82f9f9992ea3065e1a44f | 0 | returned | n/a | n/a | True |
| own | devs1cam-67f88213f397025d9200d63060fd70bf | 0 | returned | 0.4000 | n/a | n/a |
| own | devs1cam-67fb535eff3949310860344b8d417f5c | 0 | returned | n/a | 0.0000 | n/a |
| own | devs1cam-683a58e40f41330cd8faab0a1ba43314 | 0 | returned | n/a | n/a | True |
| own | devs1cam-6b16d62bb25ecc085fc34bf292e5a8f4 | 0 | returned | n/a | 6.0000 | n/a |
| own | devs1cam-6b828505f5f98c36f314bfacca685227 | 0 | returned | n/a | 13.0000 | n/a |
| own | devs1cam-6bd803a39f1f3b9b0f22b07f2906bd8a | 0 | returned | n/a | 0.0000 | n/a |
| own | devs1cam-6c2df6f4b136eaf1d44ef60046c31e04 | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-6c7aa5901a2b980ee21e95fff59f4296 | 0 | returned | n/a | 17.0000 | n/a |
| own | devs1cam-6d17e8458230e869232ce05dea93ff52 | 0 | returned | n/a | n/a | True |
| own | devs1cam-6db650f1c078b92c5a9ac29d3b1755b9 | 0 | returned | n/a | n/a | True |
| own | devs1cam-6e2f23250f0779a47f0347d7494c9207 | 0 | returned | n/a | n/a | True |
| own | devs1cam-6e76bb165adcd84edb46017714a037d5 | 0 | returned | n/a | 10.0000 | n/a |
| own | devs1cam-70b09cedb470e097dab042ba3d1dc86a | 0 | returned | n/a | n/a | True |
| own | devs1cam-715bf3e476665c3a94cd862f3204c1e6 | 0 | returned | n/a | n/a | False |
| own | devs1cam-7193e21f1a9eeaec75015548a004359c | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-72122469350c4004d5c1cce4394722af | 0 | returned | 0.1800 | n/a | n/a |
| own | devs1cam-722dd024e09eee0569da63edd89933fd | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-73693cd3f25013c7da3bf6b681fc6e05 | 0 | returned | n/a | n/a | True |
| own | devs1cam-7443c515b1e413fba39cc56a95d39d9d | 0 | returned | n/a | n/a | True |
| own | devs1cam-74c691e368949b8aff63b2c299f5e942 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-752c972e1103bed700d1279c626b7621 | 0 | returned | n/a | n/a | True |
| own | devs1cam-754534997c26e60a298a7e9b3c14f9c1 | 0 | returned | 0.2300 | n/a | n/a |
| own | devs1cam-7604ce99934dabc0732e2db012fd3368 | 0 | returned | n/a | n/a | True |
| own | devs1cam-76a1b5c5f08da424b5aae4b83b7bdecc | 0 | returned | n/a | n/a | False |
| own | devs1cam-76ac56c75f3c0612917bbcc8193c5339 | 0 | returned | n/a | n/a | True |
| own | devs1cam-7882ba6c97c8fe2bca5b6c5a7859ae36 | 0 | returned | n/a | n/a | False |
| own | devs1cam-78ba8145f465ba79adecb27f98f1c30e | 0 | returned | n/a | 158.0000 | n/a |
| own | devs1cam-79b7b96a0b66bba534f8e06655fefe13 | 0 | returned | n/a | n/a | True |
| own | devs1cam-79eb89f229322d338df859f4691cb570 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-7aee247756391afad52f2faf1ca75d68 | 0 | returned | 0.2700 | n/a | n/a |
| own | devs1cam-7b08cbabe7f9cc91e2b634fcf4610d92 | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-7d06df8bee5bd530275ee62b8af089ca | 0 | returned | 1.8600 | n/a | n/a |
| own | devs1cam-7f07649a2d141fe6a25250b34684f48a | 0 | returned | n/a | n/a | False |
| own | devs1cam-7f258b080002196edab46a1629700ee6 | 0 | returned | n/a | n/a | True |
| own | devs1cam-803a7700708aa95fe7c980788f127009 | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-808b952b36da29869b042c89222ae4a2 | 0 | returned | n/a | n/a | True |
| own | devs1cam-81a416f5577ee7e64931331ee6750357 | 0 | returned | n/a | n/a | True |
| own | devs1cam-82a124293066cf01de27789b77e5f14b | 0 | returned | n/a | n/a | True |
| own | devs1cam-83376579376807594d1593c8cc8d31cb | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-836877f1f5add3cc5e175256967ba7b0 | 0 | returned | 0.3200 | n/a | n/a |
| own | devs1cam-839fd8c5c222121513aadda01f2d6fdf | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-86480cf65f2e27b317973b8c0995db69 | 0 | returned | 0.6400 | n/a | n/a |
| own | devs1cam-866e98051dedeb27cf7a85fecc6d0a32 | 0 | returned | n/a | n/a | True |
| own | devs1cam-8698caaa9bc45e7b762ed3b06bd47d45 | 0 | returned | 2.5900 | n/a | n/a |
| own | devs1cam-87133eab18a146643bf0823c7a56fac7 | 0 | returned | n/a | 0.0000 | n/a |
| own | devs1cam-877888c6735f1dca76c43a86f44fdeb5 | 0 | returned | 0.0000 | n/a | n/a |
| own | devs1cam-88349b7b0fdd2ae5a317a78c9550e623 | 0 | returned | n/a | n/a | True |
| own | devs1cam-88905f96578b8cadfc92ea93883406b8 | 0 | returned | n/a | n/a | True |
| own | devs1cam-896d7dcb29a66ee249548d14a1ad2841 | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-899c9025299cf495fd3d0ca818be1fb7 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-89c5d2617b98a34e3302dd594c411a7f | 0 | returned | n/a | 99.0000 | n/a |
| own | devs1cam-89edf130515f36979b854b48d33a14c6 | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-8a1a8eedbf21529f89091896157a9057 | 0 | returned | n/a | 10.0000 | n/a |
| own | devs1cam-8a500999c75d8a1d9a4f4fcb634b7a97 | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-8a979b3abff030d4a45889283b52c26e | 0 | returned | 0.2600 | n/a | n/a |
| own | devs1cam-8ae5a8537ccbc40da4a1269c70ad77cc | 0 | returned | 0.7800 | n/a | n/a |
| own | devs1cam-8b5fb9cf2e866f24465310d36b052dd9 | 0 | returned | 0.1100 | n/a | n/a |
| own | devs1cam-8bc385e109ce53b6b828c4da3d0f8b44 | 0 | returned | 0.2900 | n/a | n/a |
| own | devs1cam-8d14e744f2d40c6cfc8e5f75b3036a10 | 0 | returned | n/a | n/a | True |
| own | devs1cam-8d2cb8065776ea262e1fb5aad990f894 | 0 | returned | n/a | n/a | False |
| own | devs1cam-8d91efa63427b4f81a306eb2996d5126 | 0 | returned | n/a | 15.0000 | n/a |
| own | devs1cam-8db8694dd3b4430f5ad37380ce39afed | 0 | returned | 0.5000 | n/a | n/a |
| own | devs1cam-8dede8264b43be4f9f76a97b23d18b30 | 0 | returned | 0.4600 | n/a | n/a |
| own | devs1cam-8e028611da6bce81d51ab169d47cb65c | 0 | returned | n/a | n/a | False |
| own | devs1cam-8e055c12febdfa30413dca6695fd8d1d | 0 | returned | 0.0900 | n/a | n/a |
| own | devs1cam-8e333863432f4c41ffdef8d842e977d7 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-8f077d15a9fdf6662a13eaba1630dadf | 0 | returned | 0.1400 | n/a | n/a |
| own | devs1cam-8f0ea0e0500274e8f5a60aa02c3dd496 | 0 | returned | n/a | 6.0000 | n/a |
| own | devs1cam-8f44d7b34e2d8851d196827f07fbafe1 | 0 | returned | 0.2000 | n/a | n/a |
| own | devs1cam-8f70bd517ed5842308a80e7f87cd0e55 | 0 | returned | n/a | 28.0000 | n/a |
| own | devs1cam-8f71fc95b94aaab9d94531279ac76859 | 0 | returned | n/a | n/a | False |
| own | devs1cam-8fbc98f7b2d368f156a7d6c76691dcfe | 0 | returned | 0.6900 | n/a | n/a |
| own | devs1cam-90c5871835bc55d15c21223041175ee8 | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-90cb36e22bff724116fb8461a7c00f12 | 0 | returned | n/a | n/a | True |
| own | devs1cam-9130fc1cb6d80cd810105090d0d59d6d | 0 | returned | n/a | 21.0000 | n/a |
| own | devs1cam-915e8acafcc568f1b7e1780d3c93bf3c | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-9277f3e7669b809af590bc9ed02ea652 | 0 | returned | n/a | 31.0000 | n/a |
| own | devs1cam-92efe2a3d563d6b53f8cd9650717afc3 | 0 | returned | n/a | n/a | True |
| own | devs1cam-942bceec79ef54ad20361ca882815728 | 0 | returned | n/a | n/a | False |
| own | devs1cam-9483a565716d53e6a31e555cd9e30d56 | 0 | returned | n/a | n/a | False |
| own | devs1cam-9578f4adc786b5c30c669d2d3d0c62c3 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-9601384c89c2e4ded9eb6990e85e7264 | 0 | returned | n/a | n/a | True |
| own | devs1cam-96dee7cb2c5327d13ac81ccfcd57893f | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-9797e3726c7d48572d8387e9a3f962d1 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-97f274f7f0bd32bf78617f293b8cb48c | 0 | returned | 0.2500 | n/a | n/a |
| own | devs1cam-983fddb8247c02b3514fd6441dbd3f83 | 0 | returned | n/a | n/a | True |
| own | devs1cam-98614fb5fa4dd5824d01b2ab23272e57 | 0 | returned | 0.2000 | n/a | n/a |
| own | devs1cam-98f2007812e37ec2e25b8438c785d12d | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-994081a40cb48cd70def7d6b287f057b | 0 | returned | 0.3700 | n/a | n/a |
| own | devs1cam-99e244ce603d96012829f0ea549bd620 | 0 | returned | n/a | n/a | False |
| own | devs1cam-99ed25e0197022edda2c4fa4364a72fd | 0 | returned | n/a | 16.0000 | n/a |
| own | devs1cam-9a01d0e6ce1042faa18a1102ae3c6e47 | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-9a8db608ee976f7e0e36134398cb85f5 | 0 | returned | n/a | 47.0000 | n/a |
| own | devs1cam-9bf8cf0a716ea3739829502dfbb622e3 | 0 | returned | n/a | n/a | False |
| own | devs1cam-9c8aa16bc3b251e715bf8e1f0a342d3c | 0 | returned | n/a | 43.0000 | n/a |
| own | devs1cam-9dac19f69a1b6bf75e5e445adb6882bf | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-9e1614f93d7fa3db779b02f3a7bae138 | 0 | returned | 0.0700 | n/a | n/a |
| own | devs1cam-a022bdd0062041f4998af564f26e2658 | 0 | returned | 0.4800 | n/a | n/a |
| own | devs1cam-a08dbb43caecc161222571b94b872637 | 0 | returned | 0.0100 | n/a | n/a |
| own | devs1cam-a10b71d7b53e916fe720fcff88336188 | 0 | returned | n/a | 24.0000 | n/a |
| own | devs1cam-a128d5e1f4fc12687b094f2f3ac91c77 | 0 | returned | 0.0700 | n/a | n/a |
| own | devs1cam-a1544413e4257cabdfd2926fdb1fad9b | 0 | returned | n/a | 0.0000 | n/a |
| own | devs1cam-a15a5901d91b07cc930c9e63063047d6 | 0 | returned | 0.0900 | n/a | n/a |
| own | devs1cam-a17deabef59ec32bfe7813f347d1a308 | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-a21dcc11af700ec9bb93ef1a71b5111c | 0 | returned | n/a | n/a | True |
| own | devs1cam-a38aed53757373f4a0e905af32a1741c | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-a3ad5639a615a77b2076c44c717e66db | 0 | returned | 0.3700 | n/a | n/a |
| own | devs1cam-a4cfd20ab9eafeb380aea46db14905bb | 0 | returned | 0.1900 | n/a | n/a |
| own | devs1cam-a50984da46e25527d043c1dc766ed2c6 | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-a581bbf0fbb9921793ec8240d0be05ec | 0 | returned | n/a | n/a | False |
| own | devs1cam-a5a3052d28bf12a3f318770f86240d18 | 0 | returned | n/a | n/a | False |
| own | devs1cam-a6d2d6e14e58b0e148285184e6863ae6 | 0 | returned | n/a | n/a | True |
| own | devs1cam-a6e71784fc1347d454ef4ecc0c6d552e | 0 | returned | n/a | 18.0000 | n/a |
| own | devs1cam-a7b0535f9cb3ed3d9188f14ed5098b3e | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-a7f6edf87afda6c66b9a7670dfd81fae | 0 | returned | 2.8300 | n/a | n/a |
| own | devs1cam-a8279221abbed044f088f87619dae21a | 0 | returned | n/a | n/a | False |
| own | devs1cam-a8fd6af8498a492331057d060923265e | 0 | returned | n/a | n/a | True |
| own | devs1cam-a925b6df0a21afb65b31df518a977f29 | 0 | returned | n/a | n/a | True |
| own | devs1cam-aa4801358eaaac23def499d7a066409a | 0 | returned | n/a | n/a | True |
| own | devs1cam-aa6402ccf7186ad8cf004ba57a2b8941 | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-aad4281c9228c5bc6a95d66e895a875f | 0 | returned | n/a | n/a | True |
| own | devs1cam-ac1cb26f09606e41818c376f03366a0f | 0 | returned | n/a | n/a | True |
| own | devs1cam-ac602d365aeacdf8a179a8f70d9156af | 0 | returned | n/a | 118.0000 | n/a |
| own | devs1cam-ae9942a32cf70b6bc62a81dc0ad56e27 | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-af59a069d7fb19829009f25797beb8c5 | 0 | returned | n/a | n/a | True |
| own | devs1cam-af66a215b0599f56af4bbc4f68f7aae9 | 0 | returned | n/a | n/a | False |
| own | devs1cam-af9e2c6598e4e3944755997d465fc8b9 | 0 | returned | n/a | n/a | True |
| own | devs1cam-b04b4afb81c8062ee3609f1d1e4283f6 | 0 | returned | 0.2800 | n/a | n/a |
| own | devs1cam-b10e322ca231fa7d49daaccb14a6a665 | 0 | returned | n/a | 13.0000 | n/a |
| own | devs1cam-b4ad41ef3a5a10d99b546fa01e68584c | 0 | returned | n/a | 16.0000 | n/a |
| own | devs1cam-b6078b1b9d92f479af60834f947ecba8 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-b6e5cfa5d9307989012d53f63d0e305c | 0 | returned | n/a | n/a | False |
| own | devs1cam-b7308a02db220b9af980441da794dab8 | 0 | returned | 0.0000 | n/a | n/a |
| own | devs1cam-b8a55a66c62e190d02c9968212f55e2a | 0 | returned | 0.0500 | n/a | n/a |
| own | devs1cam-ba129771ad9baaa801f45fca42f880bb | 0 | returned | n/a | n/a | False |
| own | devs1cam-ba394adb360a86fed821893368e4cd2a | 0 | returned | n/a | 14.0000 | n/a |
| own | devs1cam-ba4560899e77e3d6f3f4ef27d20acf3d | 0 | returned | n/a | n/a | True |
| own | devs1cam-bbbddf93cb397bd48f24a0448e6e4225 | 0 | returned | n/a | 30.0000 | n/a |
| own | devs1cam-bcb5ad45947af16e5f28d5fb11829252 | 0 | returned | 0.8400 | n/a | n/a |
| own | devs1cam-bcebf4406284f42f489c41fde2b8492a | 0 | returned | 0.3100 | n/a | n/a |
| own | devs1cam-bcf12b2b29a3f76524d2acac38f02dd1 | 0 | returned | 0.0500 | n/a | n/a |
| own | devs1cam-bcf65905224204490afeb430b3337ec9 | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-bd00f72b51c8224819d9dada1f8eff9c | 0 | returned | n/a | n/a | True |
| own | devs1cam-bd57333c31970bf4d95adf75850578cc | 0 | returned | n/a | n/a | True |
| own | devs1cam-bd699ff6855744603df5f827438c8574 | 0 | returned | 0.0600 | n/a | n/a |
| own | devs1cam-bd84646412253bf82c56b1d3592480c8 | 0 | returned | 0.0500 | n/a | n/a |
| own | devs1cam-bd999ce1a3ae47d5142d31260572f81d | 0 | returned | 0.1900 | n/a | n/a |
| own | devs1cam-bda1eceab340255c9c67d42c196b4076 | 0 | returned | n/a | n/a | True |
| own | devs1cam-bdf1c5b5f7ee6f3b810b36fccd2a145a | 0 | returned | n/a | 16.0000 | n/a |
| own | devs1cam-be04857120531d0a040f49624d6115ff | 0 | returned | 0.2200 | n/a | n/a |
| own | devs1cam-be2a8b7bef757f07626b031fa0e3a02c | 0 | returned | n/a | 59.0000 | n/a |
| own | devs1cam-be83a9feec4e630a532ff2330331b6e8 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-be90bb00bc0b2b91577a66c49c42d3a3 | 0 | returned | 0.0200 | n/a | n/a |
| own | devs1cam-be91c3a8f6ff92085d42f5b9e09fbb90 | 0 | returned | n/a | 27.0000 | n/a |
| own | devs1cam-bf82c2868bf1894ce38228169a29e265 | 0 | returned | n/a | n/a | False |
| own | devs1cam-bfa2caee438ea33ca07f51b380966266 | 0 | returned | n/a | n/a | True |
| own | devs1cam-c02304abe5f819346c1cfe2679a33ec3 | 0 | returned | 0.0000 | n/a | n/a |
| own | devs1cam-c03882737ec55c4ba239bfe8a4a95278 | 0 | returned | n/a | n/a | True |
| own | devs1cam-c0644be078f1db2cafd487bfa5a7b088 | 0 | returned | n/a | 28.0000 | n/a |
| own | devs1cam-c091a064bdedc2c3e9d92e889414e87e | 0 | returned | 0.1400 | n/a | n/a |
| own | devs1cam-c0d6bf6233776e576b54167dc3b56d50 | 0 | returned | 0.0900 | n/a | n/a |
| own | devs1cam-c0e184986fa119c320bc18c2a5f53f60 | 0 | returned | 0.2700 | n/a | n/a |
| own | devs1cam-c14129ee262a91322510c7ee032de73f | 0 | returned | 0.0200 | n/a | n/a |
| own | devs1cam-c1752a9c772503e6b52b66d507f4b710 | 0 | returned | n/a | n/a | True |
| own | devs1cam-c17b484fd3023c3131badd6bbc0a828f | 0 | returned | 1.7300 | n/a | n/a |
| own | devs1cam-c2b87ae00c3ef9d9da947e3cb0198700 | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-c2ceb11cca4363c296e93d58a69e766b | 0 | returned | 0.9000 | n/a | n/a |
| own | devs1cam-c302a46ccf165208796597c2510f4647 | 0 | returned | n/a | 6.0000 | n/a |
| own | devs1cam-c488362d0fc8f14d7c48076137ede89d | 0 | returned | 0.1100 | n/a | n/a |
| own | devs1cam-c54e0849a9b9f57617f0142b9eb86e37 | 0 | returned | 0.6700 | n/a | n/a |
| own | devs1cam-c5a0a17b179942f374329af010828248 | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-c7411f83c967792a369a613a0e71511b | 0 | returned | n/a | n/a | True |
| own | devs1cam-c76d6ddb4a5ff5c2f30a83312ecbcb04 | 0 | returned | 2.8600 | n/a | n/a |
| own | devs1cam-c79e5c0edd19a9a8035e1fd969f6f76f | 0 | returned | n/a | 85.0000 | n/a |
| own | devs1cam-c7aab39b4f06c2219e4632690dc7e393 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-c7d09a143d8c4ee2fdbcc59021bd2966 | 0 | returned | 0.4600 | n/a | n/a |
| own | devs1cam-c85cb7657c0dec4e6d4f51df247d985b | 0 | returned | n/a | n/a | True |
| own | devs1cam-ca64af6a5b4ea0363cb456202ae2e0f4 | 0 | returned | n/a | 19.0000 | n/a |
| own | devs1cam-ca8a0fc19426e77e2e7cf760981d30be | 0 | returned | n/a | n/a | False |
| own | devs1cam-caf201fee4a2125022f292aba9e095e9 | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-cb5bfe5b6afe21cc05ee8e06282dee85 | 0 | returned | n/a | n/a | True |
| own | devs1cam-cbd5f4f015b2707411ded4fcff760b6d | 0 | returned | 0.1300 | n/a | n/a |
| own | devs1cam-ccb86e47081baeb174c08933507d44fb | 0 | returned | n/a | n/a | True |
| own | devs1cam-ccc9f6278b17c1f708090d91ae274443 | 0 | returned | n/a | 12.0000 | n/a |
| own | devs1cam-cce660785a67b4dca971187eab6f4b18 | 0 | returned | n/a | 14.0000 | n/a |
| own | devs1cam-cd1a6c238bd3746ed63aa88735ca1895 | 0 | returned | 0.0700 | n/a | n/a |
| own | devs1cam-cdb99fe782379f91617eb469aa3f3a4a | 0 | returned | n/a | 68.0000 | n/a |
| own | devs1cam-ce5446131af04c8eb1ca90e9e5f8f214 | 0 | returned | n/a | n/a | True |
| own | devs1cam-cf7a8adb59908e74396b0305caf22413 | 0 | returned | 0.3200 | n/a | n/a |
| own | devs1cam-cf9d3b7294f89a136f222539ba3fcc15 | 0 | returned | 0.2500 | n/a | n/a |
| own | devs1cam-d035183ef78c43cf01beca9637368c2b | 0 | returned | n/a | 6.0000 | n/a |
| own | devs1cam-d037c8d92af32b28ed26504704f4b33e | 0 | returned | n/a | n/a | True |
| own | devs1cam-d0b6bbe0d485f3f2852954fa8439cedb | 0 | returned | 0.0700 | n/a | n/a |
| own | devs1cam-d0b8b9bf6b6de8790f0709bafb42c2b2 | 0 | returned | n/a | n/a | True |
| own | devs1cam-d0f62f1ec0cd67b34be909bc51db97f5 | 0 | returned | n/a | n/a | True |
| own | devs1cam-d287ebc02c4771de8f876c98e1b7e943 | 0 | returned | 0.4400 | n/a | n/a |
| own | devs1cam-d29d99c3728e911fcf2d237ac6f3113e | 0 | returned | n/a | n/a | True |
| own | devs1cam-d32079e013ae11d12b8be4f23fb5338d | 0 | returned | n/a | n/a | True |
| own | devs1cam-d475f752e4f7ccf449345cfd8c5d4440 | 0 | returned | n/a | n/a | True |
| own | devs1cam-d4cf651b885608710d311ad0b7758073 | 0 | returned | n/a | 10.0000 | n/a |
| own | devs1cam-d4d8c67ba13a53bd6cb7305e78745d3c | 0 | returned | n/a | 13.0000 | n/a |
| own | devs1cam-d57c2366f6f5c0ca64b2a22da074e197 | 0 | returned | n/a | 8.0000 | n/a |
| own | devs1cam-d61cbbbcbd424e472b55b899d5718e05 | 0 | returned | 0.0400 | n/a | n/a |
| own | devs1cam-d635240eed1b2d1cf522a83aa43c05bf | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-d66246db6d6ba5e4bbed4ede2f23a74b | 0 | returned | n/a | n/a | True |
| own | devs1cam-d6c3ef6e54b2dffe79d5bfd3f5b7cc57 | 0 | returned | n/a | n/a | True |
| own | devs1cam-d77b61105f335c59d7bd989a6bc77faf | 0 | returned | 0.1100 | n/a | n/a |
| own | devs1cam-d7a9e07bd64f8c2b232d81a29efa8a6b | 0 | returned | 3.7100 | n/a | n/a |
| own | devs1cam-d7d4eb0b26a31f804d5dc4dd6094fbe3 | 0 | returned | n/a | 32.0000 | n/a |
| own | devs1cam-d83525f8e677da756548de53980eb813 | 0 | returned | 1.2900 | n/a | n/a |
| own | devs1cam-d8429ebaf1ea0993d6e9ace70be838fd | 0 | returned | n/a | n/a | True |
| own | devs1cam-d8ba81eeeddadf155e8fc2638bf6bb3a | 0 | returned | 0.3100 | n/a | n/a |
| own | devs1cam-d8dc34d4d85be6038b2d39b3634e4f24 | 0 | returned | n/a | 1.0000 | n/a |
| own | devs1cam-d9daa469f216857cc67fa0530e8c59c3 | 0 | returned | 0.3700 | n/a | n/a |
| own | devs1cam-d9f6ae3d729e9a4e8f9b97b2af31c886 | 0 | returned | 0.7600 | n/a | n/a |
| own | devs1cam-da1309eaed7df2d6a30c2e624c2d5383 | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-da88cc894e4c2c65e71c88fed6771996 | 0 | returned | n/a | 2.0000 | n/a |
| own | devs1cam-dab03f358476674236311cd3b829a165 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-dbf4361fe48a8f8ace48b072266c8b4a | 0 | returned | n/a | n/a | False |
| own | devs1cam-dcfbbe69be4976aa9ecfb01d3e1080dd | 0 | returned | 7.3800 | n/a | n/a |
| own | devs1cam-dd019294f91678c9fd3e25379ce46e90 | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-dd869b302fe111dbab9d483ff02e3055 | 0 | returned | n/a | n/a | True |
| own | devs1cam-dde36abd8d32ffefeaca1fd2415cd604 | 0 | returned | n/a | n/a | True |
| own | devs1cam-de9ca21f755fe6cafd89f1ce84afbe37 | 0 | returned | 0.0000 | n/a | n/a |
| own | devs1cam-dfd2a8c8eb0a21e58167b86cd8e5ba6a | 0 | returned | n/a | n/a | True |
| own | devs1cam-e1acae6d43db0cd60bea9f785550a87b | 0 | returned | 0.0500 | n/a | n/a |
| own | devs1cam-e2d492243567a18de496c869a59cd6ac | 0 | returned | 0.0200 | n/a | n/a |
| own | devs1cam-e2f99f9b04a4a94201fc44bee78e176c | 0 | returned | 0.2400 | n/a | n/a |
| own | devs1cam-e6d8b6e07437be2b74ef1e73758fea22 | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-e6f5d3735e2244d40cd2dc7c7d49d453 | 0 | returned | n/a | 21.0000 | n/a |
| own | devs1cam-e6fac49a6443a6005fecc3b0375abb7e | 0 | returned | 0.7300 | n/a | n/a |
| own | devs1cam-e7196b6467f78124d993bb8999122eb4 | 0 | returned | n/a | 39.0000 | n/a |
| own | devs1cam-e768057b0752ef4fde738baf13a0e68d | 0 | returned | 0.1600 | n/a | n/a |
| own | devs1cam-e802fa5b7b2918a44efb44fc77a1ac6a | 0 | returned | n/a | 11.0000 | n/a |
| own | devs1cam-e882b7a8629fa59bc04033b7c50688ef | 0 | returned | n/a | n/a | True |
| own | devs1cam-e9606e946eecd710a9e6bbfeae0e998b | 0 | returned | n/a | n/a | True |
| own | devs1cam-ea07ae4210e3abdee120f9305aba7b46 | 0 | returned | 1.6400 | n/a | n/a |
| own | devs1cam-ead1b4fb5b95c572595cc95c9a6e0989 | 0 | returned | 5.0100 | n/a | n/a |
| own | devs1cam-eae874a60413349d42a8dd93f3336205 | 0 | returned | 0.0200 | n/a | n/a |
| own | devs1cam-eb07a132caaeb7be8b0910119cb386bc | 0 | returned | 0.3500 | n/a | n/a |
| own | devs1cam-eb07e274e83b0f461a684eb0ffd13b5b | 0 | returned | n/a | n/a | True |
| own | devs1cam-eb0f179e32e0587081d84f8ea3150c5b | 0 | returned | 0.0100 | n/a | n/a |
| own | devs1cam-eb34518c1a090ab0e9cdd6c48c707ace | 0 | returned | n/a | n/a | True |
| own | devs1cam-ec6c00e232c56dc8415132f6c24afb7b | 0 | returned | n/a | n/a | True |
| own | devs1cam-ecb9db6f1302b6413b9e6ca015c38be4 | 0 | returned | 0.4400 | n/a | n/a |
| own | devs1cam-ed6b77db243a54d1381c3dd00bdca8da | 0 | returned | n/a | 3.0000 | n/a |
| own | devs1cam-ed73545308ead79f95c7a9bb74d497da | 0 | returned | n/a | n/a | True |
| own | devs1cam-ed84c61dbde5ab68aeab5a005a791a9e | 0 | returned | n/a | 14.0000 | n/a |
| own | devs1cam-edac661ee29d27f72c954830838ec6e3 | 0 | returned | n/a | n/a | False |
| own | devs1cam-edca804cd923f7acd0bcb078605dcd07 | 0 | returned | 0.1200 | n/a | n/a |
| own | devs1cam-edfc5278137c4b51a9ba99a7b87ed25d | 0 | returned | n/a | 7.0000 | n/a |
| own | devs1cam-ee19c17d529a785abf6218ee9fb48be5 | 0 | returned | n/a | n/a | False |
| own | devs1cam-ee982c1184f51e77828bf37cc21b8b48 | 0 | returned | 0.4400 | n/a | n/a |
| own | devs1cam-eec45efdcef279db3166cce92751ad4d | 0 | returned | n/a | 19.0000 | n/a |
| own | devs1cam-ef0396683f20d945e6898535e381ad21 | 0 | returned | n/a | 40.0000 | n/a |
| own | devs1cam-efec944324efe0b3eb395fb1367e4e66 | 0 | returned | 0.1300 | n/a | n/a |
| own | devs1cam-f0595ffa3a586b8d8a5b2c0b2dca14e9 | 0 | returned | n/a | n/a | False |
| own | devs1cam-f07715e99a6cc7726d3e26a85bfd645e | 0 | returned | n/a | n/a | True |
| own | devs1cam-f1347e043f5205a845097b758b9abff2 | 0 | returned | 1.0800 | n/a | n/a |
| own | devs1cam-f18f720d2784ed810397fb2361d3c679 | 0 | returned | n/a | n/a | True |
| own | devs1cam-f1a2ba15c47cc6fdb336d2c63be79da0 | 0 | returned | n/a | 9.0000 | n/a |
| own | devs1cam-f2bfd0d329f9fa309be7773930e66c55 | 0 | returned | 0.0800 | n/a | n/a |
| own | devs1cam-f2e015f3b14dc875780f4c647d173695 | 0 | returned | 0.3600 | n/a | n/a |
| own | devs1cam-f326e38622edbe6109879dc0784f965f | 0 | returned | 0.1400 | n/a | n/a |
| own | devs1cam-f33cc892a4ba2bcfec746800b01a4e9a | 0 | returned | 0.3000 | n/a | n/a |
| own | devs1cam-f36d481f33de9f69054a5b08a5b25c24 | 0 | returned | 0.2400 | n/a | n/a |
| own | devs1cam-f4417b403fffaabe50bac4af4c77976c | 0 | returned | n/a | n/a | True |
| own | devs1cam-f472c425b295f1620576f307364be5ab | 0 | returned | n/a | 13.0000 | n/a |
| own | devs1cam-f478a182c77d9392d78cc110d970b5d6 | 0 | returned | 2.7400 | n/a | n/a |
| own | devs1cam-f5316bf5ff16257d9587548f1c67ec83 | 0 | returned | n/a | n/a | True |
| own | devs1cam-f845406344eee35d8e87003a3737fd89 | 0 | returned | n/a | 12.0000 | n/a |
| own | devs1cam-f866ae99d3db5c3590d990d6d621f6cc | 0 | returned | n/a | n/a | True |
| own | devs1cam-f9f52c52e877443c3053641748c4cdaf | 0 | returned | n/a | n/a | False |
| own | devs1cam-fa07df6af6ef47bc3b83baeaf44badb1 | 0 | returned | n/a | n/a | True |
| own | devs1cam-fa38ceae7d5be6c02b695fa308ffd1b1 | 0 | returned | n/a | n/a | False |
| own | devs1cam-faaa1fab79082817dacb8bb7b32c4519 | 0 | returned | n/a | n/a | True |
| own | devs1cam-fae38610f0ddd1c022d8079537d9bc25 | 0 | returned | n/a | 4.0000 | n/a |
| own | devs1cam-fcd098dd942c2ded6599bec14bccaf36 | 0 | returned | n/a | n/a | False |
| own | devs1cam-fd61e009146cb6d72ef89f6ac1269b42 | 0 | returned | n/a | 5.0000 | n/a |
| own | devs1cam-fe04c49911ec5a773f3e5975dd1df75a | 0 | returned | n/a | 36.0000 | n/a |
| own | devs1cam-fe35bce39404594f56ea20f44a491977 | 0 | returned | 2.4100 | n/a | n/a |
| own | devs1cam-ff3ba6316a032c274ffed6542abba64c | 0 | returned | 0.0400 | n/a | n/a |
| own | vsi590k_042574 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042574 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042574 | 2 | returned | 0.2500 | n/a | n/a |
| own | vsi590k_042581 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042581 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042581 | 2 | returned | 1.1088 | n/a | n/a |
| own | vsi590k_042584 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_042584 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042584 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042584 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_042584 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_042584 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_042588 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042588 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042588 | 2 | returned | 0.0800 | n/a | n/a |
| own | vsi590k_042597 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042597 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_042597 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042597 | 3 | selected | n/a | n/a | n/a |
| own | vsi590k_042597 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_042597 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_042604 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_042604 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042604 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042604 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_042604 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_042604 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_042608 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_042608 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042608 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042608 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_042608 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_042608 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_042612 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042612 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042612 | 2 | returned | 1.4846 | n/a | n/a |
| own | vsi590k_042613 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042613 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042613 | 2 | returned | 0.3200 | n/a | n/a |
| own | vsi590k_042627 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042627 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_042627 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042632 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042632 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042632 | 2 | returned | 0.0291 | n/a | n/a |
| own | vsi590k_042644 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_042644 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042644 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042644 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_042644 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_042644 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_042645 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042645 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042645 | 2 | returned | 0.1900 | n/a | n/a |
| own | vsi590k_042656 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042656 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042656 | 2 | returned | 0.1893 | n/a | n/a |
| own | vsi590k_042674 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042674 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042674 | 2 | returned | 0.1100 | n/a | n/a |
| own | vsi590k_042690 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042690 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042690 | 2 | returned | 0.0900 | n/a | n/a |
| own | vsi590k_042715 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_042715 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042715 | 2 | returned | 1.8900 | n/a | n/a |
| own | vsi590k_042717 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_042717 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_042717 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_042717 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_042717 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_042717 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_044593 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_044593 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_044593 | 2 | returned | 0.1400 | n/a | n/a |
| own | vsi590k_044597 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_044597 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_044597 | 2 | returned | 0.0600 | n/a | n/a |
| own | vsi590k_044622 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_044622 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_044622 | 2 | returned | 0.3900 | n/a | n/a |
| own | vsi590k_045538 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_045538 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_045538 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_045538 | 3 | selected | n/a | n/a | n/a |
| own | vsi590k_045538 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_045538 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_045546 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_045546 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_045546 | 2 | returned | 0.5906 | n/a | n/a |
| own | vsi590k_045786 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_045786 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_045786 | 2 | returned | 0.7925 | n/a | n/a |
| own | vsi590k_046210 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_046210 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_046210 | 2 | returned | 1.0400 | n/a | n/a |
| own | vsi590k_046212 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_046212 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_046212 | 2 | returned | 0.3800 | n/a | n/a |
| own | vsi590k_047592 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_047592 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_047592 | 2 | returned | 1.0721 | n/a | n/a |
| own | vsi590k_050188 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_050188 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_050188 | 2 | returned | 1.1269 | n/a | n/a |
| own | vsi590k_050630 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_050630 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_050630 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_155738 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_155738 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_155738 | 2 | returned | 0.4210 | n/a | n/a |
| own | vsi590k_155745 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_155745 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_155745 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_155745 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_155745 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_155745 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_161427 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161427 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161427 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161427 | 3 | selected | n/a | n/a | n/a |
| own | vsi590k_161427 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_161427 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_161567 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161567 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161567 | 2 | returned | 0.1750 | n/a | n/a |
| own | vsi590k_161571 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161571 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161571 | 2 | returned | 0.0502 | n/a | n/a |
| own | vsi590k_161734 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161734 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161734 | 2 | returned | 1.2293 | n/a | n/a |
| own | vsi590k_161796 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161796 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161796 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161799 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161799 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161799 | 2 | returned | 1.9400 | n/a | n/a |
| own | vsi590k_161806 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_161806 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161806 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161806 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_161806 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_161806 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_161807 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161807 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161807 | 2 | returned | 0.6195 | n/a | n/a |
| own | vsi590k_161821 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161821 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161821 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161825 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161825 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161825 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161826 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161826 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161826 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161827 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161827 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161827 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161828 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_161828 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161828 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161830 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_161830 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161830 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161832 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161832 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161832 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161834 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161834 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_161834 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161836 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_161836 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161836 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_161841 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_161841 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_161841 | 2 | returned | 0.6200 | n/a | n/a |
| own | vsi590k_163060 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163060 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163060 | 2 | returned | 0.9600 | n/a | n/a |
| own | vsi590k_163069 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163069 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163069 | 2 | returned | 1.9001 | n/a | n/a |
| own | vsi590k_163082 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163082 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163082 | 2 | returned | 2.4401 | n/a | n/a |
| own | vsi590k_163091 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163091 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163091 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163091 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163091 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_163091 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163095 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163095 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163095 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163095 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163095 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_163095 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163157 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163157 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163157 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163157 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163157 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_163157 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163169 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163169 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163169 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163169 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163169 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_163169 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163172 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163172 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163172 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163172 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163172 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_163172 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163271 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163271 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163271 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163271 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163271 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_163271 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163641 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163641 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163641 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163643 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163643 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163643 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163643 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163643 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_163643 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163648 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163648 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163648 | 2 | returned | 0.7156 | n/a | n/a |
| own | vsi590k_163659 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163659 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163659 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163659 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163659 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_163659 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163662 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163662 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163662 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163662 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163662 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_163662 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163777 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163777 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163777 | 2 | returned | 0.5200 | n/a | n/a |
| own | vsi590k_163778 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163778 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163778 | 2 | returned | 0.5000 | n/a | n/a |
| own | vsi590k_163785 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163785 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163785 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163788 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163788 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163788 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163793 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163793 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163793 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163796 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163796 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163796 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163797 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163797 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163797 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163797 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_163797 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_163797 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163799 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_163799 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163799 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163811 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163811 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163811 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163813 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163813 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163813 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163814 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163814 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_163814 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_163814 | 3 | error: malformed_v313_call | n/a | n/a | n/a |
| own | vsi590k_163814 | 4 | error: malformed_v313_call | n/a | n/a | n/a |
| own | vsi590k_163814 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_163815 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_163815 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_163815 | 2 | returned | 0.0858 | n/a | n/a |
| own | vsi590k_164325 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_164325 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164325 | 2 | returned | 0.8189 | n/a | n/a |
| own | vsi590k_164334 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_164334 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164334 | 2 | returned | 1.7000 | n/a | n/a |
| own | vsi590k_164335 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_164335 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164335 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_164335 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_164335 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_164335 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_164340 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_164340 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164340 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_164340 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_164340 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_164340 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_164348 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_164348 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164348 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_164348 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_164348 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_164348 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_164354 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_164354 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164354 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_164354 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_164354 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_164354 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_164784 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_164784 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164784 | 2 | returned | 0.4700 | n/a | n/a |
| own | vsi590k_164785 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_164785 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164785 | 2 | returned | 0.5100 | n/a | n/a |
| own | vsi590k_164801 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_164801 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164801 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_164801 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_164801 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_164801 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_164817 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_164817 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_164817 | 2 | returned | 0.3800 | n/a | n/a |
| own | vsi590k_164821 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_164821 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_164821 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_164821 | 3 | selected | n/a | n/a | n/a |
| own | vsi590k_164821 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_164821 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_165296 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165296 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_165296 | 2 | returned | 0.6000 | n/a | n/a |
| own | vsi590k_165307 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165307 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_165307 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_165318 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165318 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_165318 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_165323 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165323 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_165323 | 2 | returned | 0.0890 | n/a | n/a |
| own | vsi590k_165343 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165343 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_165343 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_165350 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165350 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_165350 | 2 | returned | 1.4950 | n/a | n/a |
| own | vsi590k_165357 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_165357 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_165357 | 2 | returned | 1.2100 | n/a | n/a |
| own | vsi590k_166609 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_166609 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_166609 | 2 | returned | 0.1923 | n/a | n/a |
| own | vsi590k_168046 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_168046 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_168046 | 2 | returned | 2.4527 | n/a | n/a |
| own | vsi590k_168055 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_168055 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_168055 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_168055 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_168055 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_168055 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_168067 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_168067 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_168067 | 2 | returned | 0.2505 | n/a | n/a |
| own | vsi590k_168070 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_168070 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_168070 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_169291 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_169291 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_169291 | 2 | returned | 1.7191 | n/a | n/a |
| own | vsi590k_169295 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_169295 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_169295 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_169442 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_169442 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_169442 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_169442 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_169442 | 4 | not seen | n/a | n/a | n/a |
| own | vsi590k_169442 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_169469 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_169469 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_169469 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_169469 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_169469 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_169469 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_251447 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251447 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251447 | 2 | returned | 1.1839 | n/a | n/a |
| own | vsi590k_251449 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251449 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251449 | 2 | returned | 0.2873 | n/a | n/a |
| own | vsi590k_251452 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251452 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251452 | 2 | returned | 1.1400 | n/a | n/a |
| own | vsi590k_251453 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251453 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251453 | 2 | returned | 1.2600 | n/a | n/a |
| own | vsi590k_251454 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251454 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251454 | 2 | returned | 1.6675 | n/a | n/a |
| own | vsi590k_251506 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251506 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251506 | 2 | returned | 0.5100 | n/a | n/a |
| own | vsi590k_251515 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251515 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251515 | 2 | returned | 0.4400 | n/a | n/a |
| own | vsi590k_251702 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251702 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251702 | 2 | returned | 0.0490 | n/a | n/a |
| own | vsi590k_251912 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251912 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251912 | 2 | returned | 0.5200 | n/a | n/a |
| own | vsi590k_251919 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251919 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251919 | 2 | returned | 0.4869 | n/a | n/a |
| own | vsi590k_251923 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251923 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251923 | 2 | returned | 1.1491 | n/a | n/a |
| own | vsi590k_251924 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251924 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251924 | 2 | returned | 1.1489 | n/a | n/a |
| own | vsi590k_251925 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251925 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251925 | 2 | returned | 0.5805 | n/a | n/a |
| own | vsi590k_251927 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251927 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251927 | 2 | returned | 0.0000 | n/a | n/a |
| own | vsi590k_251965 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251965 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_251965 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_251967 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_251967 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_251967 | 2 | returned | 1.2500 | n/a | n/a |
| own | vsi590k_252278 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252278 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252278 | 2 | returned | 0.2723 | n/a | n/a |
| own | vsi590k_252280 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_252280 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252280 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_252280 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_252280 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_252280 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_252282 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252282 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252282 | 2 | returned | 2.3062 | n/a | n/a |
| own | vsi590k_252283 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252283 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_252283 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_252491 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252491 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252491 | 2 | returned | 0.2304 | n/a | n/a |
| own | vsi590k_252493 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252493 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252493 | 2 | returned | 1.1427 | n/a | n/a |
| own | vsi590k_252496 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252496 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252496 | 2 | returned | 0.2798 | n/a | n/a |
| own | vsi590k_252497 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_252497 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252497 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_252497 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_252497 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_252497 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_252500 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_252500 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252500 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_252500 | 3 | not seen | n/a | n/a | n/a |
| own | vsi590k_252500 | 4 | selected | n/a | n/a | n/a |
| own | vsi590k_252500 | 5 | unserved | n/a | n/a | n/a |
| own | vsi590k_252505 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_252505 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_252505 | 2 | returned | 0.8800 | n/a | n/a |
| own | vsi590k_253035 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253035 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253035 | 2 | returned | 1.2543 | n/a | n/a |
| own | vsi590k_253038 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253038 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253038 | 2 | returned | 1.6200 | n/a | n/a |
| own | vsi590k_253039 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253039 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253039 | 2 | returned | 0.1810 | n/a | n/a |
| own | vsi590k_253040 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253040 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253040 | 2 | returned | 1.4600 | n/a | n/a |
| own | vsi590k_253042 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253042 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253042 | 2 | returned | 0.8400 | n/a | n/a |
| own | vsi590k_253230 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253230 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253230 | 2 | returned | 0.1500 | n/a | n/a |
| own | vsi590k_253354 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253354 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253354 | 2 | returned | 0.6910 | n/a | n/a |
| own | vsi590k_253363 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253363 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_253363 | 2 | returned | 0.0475 | n/a | n/a |
| own | vsi590k_253783 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253783 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_253783 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_253784 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_253784 | 1 | not seen | n/a | n/a | n/a |
| own | vsi590k_253784 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_254132 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_254132 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_254132 | 2 | returned | 0.6300 | n/a | n/a |
| own | vsi590k_254285 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_254285 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_254285 | 2 | returned | 0.1221 | n/a | n/a |
| own | vsi590k_254594 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_254594 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_254594 | 2 | returned | 0.4600 | n/a | n/a |
| own | vsi590k_254604 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_254604 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_254604 | 2 | returned | 0.0798 | n/a | n/a |
| own | vsi590k_255374 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_255374 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_255374 | 2 | returned | 0.4544 | n/a | n/a |
| own | vsi590k_255402 | 0 | not seen | n/a | n/a | n/a |
| own | vsi590k_255402 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_255402 | 2 | not seen | n/a | n/a | n/a |
| own | vsi590k_255407 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_255407 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_255407 | 2 | returned | 0.9900 | n/a | n/a |
| own | vsi590k_255863 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_255863 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_255863 | 2 | returned | 0.2600 | n/a | n/a |
| own | vsi590k_255865 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_255865 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_255865 | 2 | returned | 0.1492 | n/a | n/a |
| own | vsi590k_256028 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_256028 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_256028 | 2 | returned | 0.8100 | n/a | n/a |
| own | vsi590k_256516 | 0 | selected | n/a | n/a | n/a |
| own | vsi590k_256516 | 1 | selected | n/a | n/a | n/a |
| own | vsi590k_256516 | 2 | returned | 0.0389 | n/a | n/a |
| own | room_scene0155_00 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0155_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0155_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0166_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0166_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0261_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0261_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0320_00 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0320_00 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0320_01 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0320_01 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0320_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0320_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0380_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0380_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0401_00 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0401_00 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0475_00 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0475_00 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0475_01 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0475_01 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0475_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0475_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0515_00 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0515_00 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0515_01 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0515_01 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0515_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0515_02 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0587_00 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0587_00 | 1 | unserved | n/a | n/a | n/a |
| own | room_scene0587_01 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0587_02 | 0 | unserved | n/a | n/a | n/a |
| own | room_scene0587_02 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_058413 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_058413 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_058414 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_058415 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_058415 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_058460 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_058535 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_058535 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_058599 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_058599 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_058764 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059181 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059181 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_059182 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059182 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_059183 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059183 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_059475 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059475 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_059477 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059493 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059494 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059495 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059529 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059529 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_059530 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059530 | 1 | unserved | n/a | n/a | n/a |
| own | vsi590k_059531 | 0 | unserved | n/a | n/a | n/a |
| own | vsi590k_059531 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | devs1cam-0020d0cefc26c693abeb6c4e5951cc07 | 0 | returned | 0.3100 | n/a | n/a |
| null_argmax | devs1cam-00729c5db90fc5d0c5281ed7ce889dca | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-02240d9bcaf9703226aa03c98e9f2d6e | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-05ce2ad29e7353ab8b808abe3df89f0d | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-05eff7f66869bc50118d2e0d84d927df | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-069c4a4fb2b94413b432b3abc2d66ac2 | 0 | returned | n/a | 12.0000 | n/a |
| null_argmax | devs1cam-07b1a63813a4733a042538e350e265eb | 0 | returned | 0.1500 | n/a | n/a |
| null_argmax | devs1cam-088f1e3c275fb323293f10b356d740a2 | 0 | returned | 0.2200 | n/a | n/a |
| null_argmax | devs1cam-0a369d6600f61cc6c3e15cb9e954e689 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-0ab1b7c5ac60d3d2550706a3cdce8b29 | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-0adb11f9bb13b47d9d937ab72f8e2eea | 0 | returned | 0.1400 | n/a | n/a |
| null_argmax | devs1cam-0baec18afce655dae16a404906102533 | 0 | returned | 0.0000 | n/a | n/a |
| null_argmax | devs1cam-0bbc754c75556e9403d471951304183b | 0 | returned | 0.2300 | n/a | n/a |
| null_argmax | devs1cam-0c0b001891172c79b9b8caa6fef84bda | 0 | returned | 0.2000 | n/a | n/a |
| null_argmax | devs1cam-0cdcb2a08007772ca78ae5d7a6c9b886 | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-0d0cf0791c32f428cfacf34bc5b66f6a | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-0d4180723a5d9942daa277d9466db301 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-0d591bfbb81d0bac9261869201786807 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-0e6c9965c28858ab6a0d70649e9f7801 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-0f41e5b96a3bf8f5c9d748d663448c88 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-0f558e8f2f579ecce0a2173b1505584d | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-1054354c3c441728e37e87dc7bbd6a68 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-1142c5ca6feafd58d27489b2166b42ba | 0 | returned | 0.0700 | n/a | n/a |
| null_argmax | devs1cam-138cccbfe6d3bb26b10f50e1cae6a0d4 | 0 | returned | n/a | 0.0000 | n/a |
| null_argmax | devs1cam-13c1d6e42464ff095b5000e82d782009 | 0 | returned | n/a | 6.0000 | n/a |
| null_argmax | devs1cam-13e0fc3df819bbe48fd3e13644508b18 | 0 | returned | 0.1100 | n/a | n/a |
| null_argmax | devs1cam-14bd1afd2f3737fcb8c72811b82dbcd1 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-15f434c2d7e5cabf4baa6425706378c0 | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-164f3c63246cf1801e39bd68179b25c6 | 0 | returned | n/a | 19.0000 | n/a |
| null_argmax | devs1cam-16c216a1c82e3d8e6ac2410cb5a6356b | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-17e826c7e7031b84a5d88c7ce16623a6 | 0 | returned | 0.4600 | n/a | n/a |
| null_argmax | devs1cam-1976e69d628ad042a97c896d57221682 | 0 | returned | 0.6100 | n/a | n/a |
| null_argmax | devs1cam-198336f8bdf6985012b777f57d49cced | 0 | returned | n/a | 90.0000 | n/a |
| null_argmax | devs1cam-19baad91803f182449ea525bb1c95521 | 0 | returned | 0.1800 | n/a | n/a |
| null_argmax | devs1cam-1a0cee7f65e591a5590179ec2b8cdfa9 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-1a1863a10468af67b7244bdebd30b073 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-1a2a6eee4de7efd195338e9547b105c4 | 0 | returned | 2.2700 | n/a | n/a |
| null_argmax | devs1cam-1a33fc17ab1eb437d771e9f981ea8832 | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-1b61a955e284dbebb14768fdd95ebc9b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-1b7ba80e4a37097641e4c6abd2387e07 | 0 | returned | n/a | 90.0000 | n/a |
| null_argmax | devs1cam-1c4baf0dcb39c0575ae19014ac6fade7 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-1c639bff1680ba444816cdfe4a391af9 | 0 | returned | n/a | 11.0000 | n/a |
| null_argmax | devs1cam-1d60e77e9e48d47d63d61c2e735686a9 | 0 | returned | 2.4400 | n/a | n/a |
| null_argmax | devs1cam-1dcd9643f274d9b9cfa4c80b4ce59652 | 0 | returned | n/a | 50.0000 | n/a |
| null_argmax | devs1cam-1e32b030462621630cc2f907576af887 | 0 | returned | n/a | 43.0000 | n/a |
| null_argmax | devs1cam-1e82b04d17a1e723669d4385fef93ebe | 0 | returned | 6.0300 | n/a | n/a |
| null_argmax | devs1cam-1ed3c6004b63451bde7ffa3c6c12e2e4 | 0 | returned | n/a | 14.0000 | n/a |
| null_argmax | devs1cam-2145b0bdf8607a7d4c289b00ca7fb16a | 0 | returned | n/a | 22.0000 | n/a |
| null_argmax | devs1cam-227f221890b5efcf2a6517ff68226723 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-229e7bdf910b966f2218a59c4d1e1273 | 0 | returned | 0.7200 | n/a | n/a |
| null_argmax | devs1cam-23e4a31e0df1e0b06b7c9f43c1a5d641 | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-23f04fb2b67c5c545d592b39d8d52c97 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-247c686a26ebecb5097ee688577ec62a | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-24fc408c05e4d666b6fb1e89d218f5d9 | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-252cc74fcb20a299b88bb5a7ceee5d60 | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-25a2d02602e3865726da5f94f1043f19 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-25b79a6f4a93cac75556e6f4dfcb243e | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-25d51266f56ad4b02b7d8ed70c27ce52 | 0 | returned | n/a | 126.0000 | n/a |
| null_argmax | devs1cam-25d7016a7ea1bf023f76948fdd9deaeb | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-261616c5055d35a90c5d584eb897193c | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-27bac7d0c462e80b3395e5923e3bdcd3 | 0 | returned | 0.0100 | n/a | n/a |
| null_argmax | devs1cam-27da9a85bf26dc4dbd9f9d0c6e40f59d | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-28389a5db258677ec602acb20f27840e | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-287a70b200cc988bdc196baddcfba2ee | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-28efb0393e32b223347815cfe18adec4 | 0 | returned | n/a | 16.0000 | n/a |
| null_argmax | devs1cam-295b5a2706d771d9bea92573137194ce | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-29773f44cdd54eeee982a0498d024951 | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-2a2cb97664b1c93f39fbb6153c07d305 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-2a80598ada0b258686ce5f8c24257ae6 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-2c3e51248e313ee107d8bf9a312a0212 | 0 | returned | n/a | 159.0000 | n/a |
| null_argmax | devs1cam-2c8c72894ccbffdc9d46321f66ec8090 | 0 | returned | n/a | 126.0000 | n/a |
| null_argmax | devs1cam-2caddcb84c0bc23b0d89ba3003bfba57 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-2cd565588214cafe7715bfa386c15341 | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-2d2f184399fce90f8ef087a67303096a | 0 | returned | 0.0400 | n/a | n/a |
| null_argmax | devs1cam-2d6247bfc8f1ff68196e8e0321a20c6d | 0 | returned | 1.8400 | n/a | n/a |
| null_argmax | devs1cam-2d770696a926df52f2f9e3414a53efd8 | 0 | returned | 1.1400 | n/a | n/a |
| null_argmax | devs1cam-2de4909ee3577f17c78c77a2e9e29317 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-2ea3d5c02118a891bfc300d2f2f28ca7 | 0 | returned | n/a | 11.0000 | n/a |
| null_argmax | devs1cam-2f4c478745e39b6f1e29fd1706ed5bf0 | 0 | returned | 0.8300 | n/a | n/a |
| null_argmax | devs1cam-2f6b04a35cb285aebf8a567c9422fd65 | 0 | returned | 0.0100 | n/a | n/a |
| null_argmax | devs1cam-2f76f5acd2a8a198a57edc57900b21a5 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-2fa02399c753a95355ec261aa49813ff | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-2fd5bd894c6b7ae7098f6e7f8a0c88d4 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-2fe8882e1b6e7b4bd3f9230e9add461c | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-30f0f38919466d58f06d53f632cdd2a1 | 0 | returned | 0.2000 | n/a | n/a |
| null_argmax | devs1cam-311f577252a264592c0d796210ee8cb0 | 0 | returned | 0.1800 | n/a | n/a |
| null_argmax | devs1cam-31cffb00c5dba885767d5428b673bdfb | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-31d9eac811eb11717a53fffe9583f9f0 | 0 | returned | 0.3500 | n/a | n/a |
| null_argmax | devs1cam-332f6cace3baf8c061dc536c7a4dd243 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-348a9e022f27ac67031f55b8b0167ba3 | 0 | returned | 0.1800 | n/a | n/a |
| null_argmax | devs1cam-35f6b028403fc915f5ee1839ac0fc7e8 | 0 | returned | 0.1400 | n/a | n/a |
| null_argmax | devs1cam-36625cf9ab3cf88b534b4385238f2f12 | 0 | returned | n/a | 29.0000 | n/a |
| null_argmax | devs1cam-369e6305542730f6ae91fb214dc1fbd1 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-389218694a6e46678a1f993e09e0bfec | 0 | returned | 0.9300 | n/a | n/a |
| null_argmax | devs1cam-38cae6cbe5a8ef1abb1ff04b2cd51dc5 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-3a9f05dfb4de4e999fcfa728533858e2 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-3b06cb0a2e8face562911a02f71d8623 | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-3b299b26636d3d0b30d139a507bbaa96 | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-3b3bd31478f32ba1744edd3c3dbea8aa | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-3c209557bfc86a182a9952f28e04221a | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-3d1603b2e5b652d907876bdb15597177 | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-3d52edf5468c4207061fa53bfbf09c1c | 0 | returned | 0.3000 | n/a | n/a |
| null_argmax | devs1cam-3db00ce69e697a9d3abeac27819a3ae6 | 0 | returned | 0.2400 | n/a | n/a |
| null_argmax | devs1cam-3e82dd97532a1b9786af2d973c1c39f5 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-3ea4d987de4dbedecb40ca902d836b1f | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-3f22bf92384123d71d26d8c6811ceb35 | 0 | returned | n/a | 12.0000 | n/a |
| null_argmax | devs1cam-3f4559da4d4b5f856fcce3cc817c55dc | 0 | returned | n/a | 18.0000 | n/a |
| null_argmax | devs1cam-3fa79d1a487810e1b48b4c30ddda88a5 | 0 | returned | 2.9600 | n/a | n/a |
| null_argmax | devs1cam-40263b40dfc3078be2ba9eb3258bf439 | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-4162d0dbfce5adfc5875d80199370621 | 0 | returned | 0.7500 | n/a | n/a |
| null_argmax | devs1cam-41f0ee22c9b241d8d745406680121021 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-42142c541ad2b875c1539f5e85e69feb | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-44076714b5ef1e416bb5e9f7140d2a09 | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-44476730608f5c7d6a8a8340713399df | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-453f94505fe0f14d25cb80c5088e6f72 | 0 | returned | n/a | 0.0000 | n/a |
| null_argmax | devs1cam-45ed5c9e944f8f16079231feb6c2d941 | 0 | returned | 0.8300 | n/a | n/a |
| null_argmax | devs1cam-48807cbe2a627252c8d48966af2ac778 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-49dbcdf686b199381d65e13d07b1e14e | 0 | returned | 0.1300 | n/a | n/a |
| null_argmax | devs1cam-4a315b8a07d782753f8625a1dc0439ae | 0 | returned | n/a | 12.0000 | n/a |
| null_argmax | devs1cam-4a3ee8096e8a2d087746a7e9bb45bc7d | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-4aaef73ef8f7374b3318805e5788836a | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-4b4e285c9b22b922af7ed6684d129445 | 0 | returned | n/a | 11.0000 | n/a |
| null_argmax | devs1cam-4c8b8d552a6c0ed8f7c575d9fe34b0f7 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-4d34ad1ab67f1406fb84bf183d091ef7 | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-4db02514fa675dbd1ed5cbcfb84f1130 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-4e15e17068eec1a23a601e9615dc2c77 | 0 | returned | n/a | 14.0000 | n/a |
| null_argmax | devs1cam-4faed4682687658d4cce9053ce6ae9e6 | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-504a8f836ec9b59ff4a1b3722de9e280 | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-50b26c5a65f68c7184c6827117eb3145 | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-50d8b3491b4136fe011ab45a48ddc79d | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-5243d62cb1b1e112d1c18b3bca988c57 | 0 | returned | n/a | 12.0000 | n/a |
| null_argmax | devs1cam-53d3069b9da4533486ef2527d1c5483f | 0 | returned | 0.5400 | n/a | n/a |
| null_argmax | devs1cam-53fb8eb60d82ce1054bc4bfe900bdd5c | 0 | returned | 0.3700 | n/a | n/a |
| null_argmax | devs1cam-54062ce87aa7bd7a3d1f520e657648b4 | 0 | returned | 0.7900 | n/a | n/a |
| null_argmax | devs1cam-542eb42026788cc63df9e5a0ed9aae46 | 0 | returned | 0.2800 | n/a | n/a |
| null_argmax | devs1cam-55215ec664298583c3cfb0e2873a86a0 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-55737eb70f6647fb31984bebad82c03f | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-5603d546987bf298034c320fd4030fe0 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-5640abcbd1882f1be581ed84194b82a1 | 0 | returned | n/a | 27.0000 | n/a |
| null_argmax | devs1cam-56637b6125f18410bdfca24073fd453e | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-578e23b84ba6a586db309e68eff43d9e | 0 | returned | 0.6800 | n/a | n/a |
| null_argmax | devs1cam-584ed12038aeaf7de02484f2d59de464 | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-58775077eff086d079ffdaf4a2a85443 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-58b41f71b4e5883894beae8dccb7e99e | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-5972b10244779f08bf3dde7bf43c3074 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-59ab36f70477becdd652ee11b3366880 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-5a35be901ad65075a70c92ebe3fea1db | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-5a3b79130e94e0a9727ae3ec32d04ce8 | 0 | returned | 0.0800 | n/a | n/a |
| null_argmax | devs1cam-5b8fb5dd49158ebeb45c42704076caa5 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-5b98ada09a663b4e3ec06701022acee6 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-5ba10abff65a66ad9d955a50fc844d8c | 0 | returned | 0.5000 | n/a | n/a |
| null_argmax | devs1cam-5bd21da4b35e5360f27e75d6cdadf114 | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-5c4f40c19d29304493a4e340e2fbdb11 | 0 | returned | 3.2300 | n/a | n/a |
| null_argmax | devs1cam-5dc99fae7c27b2ad92d5788691ebc75f | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-5df62da4b1dd2e6e77486bb2cdf8d769 | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-5f9724339c1393d9cbdc605c301b0b26 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-60346f2b71cd2003c082cc86d8a56989 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-61abc3d389b77c34d7e311fbdbba54fa | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-63862a6912ad716a4e4fd35af9b591f9 | 0 | returned | 0.2000 | n/a | n/a |
| null_argmax | devs1cam-642f7803436e63d24fbe54a14b784cb5 | 0 | returned | 0.3700 | n/a | n/a |
| null_argmax | devs1cam-648c86f02e008d0d922da63705103589 | 0 | returned | 0.1000 | n/a | n/a |
| null_argmax | devs1cam-64b76ac73df298f7222625e1fdd2e222 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-6548f6320506db01af213699ff2d37cd | 0 | returned | n/a | 16.0000 | n/a |
| null_argmax | devs1cam-655b1f6a401470c178e86c28210edb22 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-662b57eea66bab52aa22d0c26a468735 | 0 | returned | 0.3300 | n/a | n/a |
| null_argmax | devs1cam-67088ff4bd269377c9afbe466856c732 | 0 | returned | 0.6000 | n/a | n/a |
| null_argmax | devs1cam-6746124474529d17b5c54c12a6f11bba | 0 | returned | n/a | 27.0000 | n/a |
| null_argmax | devs1cam-675db7e44fe82f9f9992ea3065e1a44f | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-67f88213f397025d9200d63060fd70bf | 0 | returned | 0.4000 | n/a | n/a |
| null_argmax | devs1cam-67fb535eff3949310860344b8d417f5c | 0 | returned | n/a | 0.0000 | n/a |
| null_argmax | devs1cam-683a58e40f41330cd8faab0a1ba43314 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-6b16d62bb25ecc085fc34bf292e5a8f4 | 0 | returned | n/a | 6.0000 | n/a |
| null_argmax | devs1cam-6b828505f5f98c36f314bfacca685227 | 0 | returned | n/a | 13.0000 | n/a |
| null_argmax | devs1cam-6bd803a39f1f3b9b0f22b07f2906bd8a | 0 | returned | n/a | 0.0000 | n/a |
| null_argmax | devs1cam-6c2df6f4b136eaf1d44ef60046c31e04 | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-6c7aa5901a2b980ee21e95fff59f4296 | 0 | returned | n/a | 17.0000 | n/a |
| null_argmax | devs1cam-6d17e8458230e869232ce05dea93ff52 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-6db650f1c078b92c5a9ac29d3b1755b9 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-6e2f23250f0779a47f0347d7494c9207 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-6e76bb165adcd84edb46017714a037d5 | 0 | returned | n/a | 10.0000 | n/a |
| null_argmax | devs1cam-70b09cedb470e097dab042ba3d1dc86a | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-715bf3e476665c3a94cd862f3204c1e6 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-7193e21f1a9eeaec75015548a004359c | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-72122469350c4004d5c1cce4394722af | 0 | returned | 0.1800 | n/a | n/a |
| null_argmax | devs1cam-722dd024e09eee0569da63edd89933fd | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-73693cd3f25013c7da3bf6b681fc6e05 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-7443c515b1e413fba39cc56a95d39d9d | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-74c691e368949b8aff63b2c299f5e942 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-752c972e1103bed700d1279c626b7621 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-754534997c26e60a298a7e9b3c14f9c1 | 0 | returned | 0.2300 | n/a | n/a |
| null_argmax | devs1cam-7604ce99934dabc0732e2db012fd3368 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-76a1b5c5f08da424b5aae4b83b7bdecc | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-76ac56c75f3c0612917bbcc8193c5339 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-7882ba6c97c8fe2bca5b6c5a7859ae36 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-78ba8145f465ba79adecb27f98f1c30e | 0 | returned | n/a | 158.0000 | n/a |
| null_argmax | devs1cam-79b7b96a0b66bba534f8e06655fefe13 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-79eb89f229322d338df859f4691cb570 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-7aee247756391afad52f2faf1ca75d68 | 0 | returned | 0.2700 | n/a | n/a |
| null_argmax | devs1cam-7b08cbabe7f9cc91e2b634fcf4610d92 | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-7d06df8bee5bd530275ee62b8af089ca | 0 | returned | 1.8600 | n/a | n/a |
| null_argmax | devs1cam-7f07649a2d141fe6a25250b34684f48a | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-7f258b080002196edab46a1629700ee6 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-803a7700708aa95fe7c980788f127009 | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-808b952b36da29869b042c89222ae4a2 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-81a416f5577ee7e64931331ee6750357 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-82a124293066cf01de27789b77e5f14b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-83376579376807594d1593c8cc8d31cb | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-836877f1f5add3cc5e175256967ba7b0 | 0 | returned | 0.3200 | n/a | n/a |
| null_argmax | devs1cam-839fd8c5c222121513aadda01f2d6fdf | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-86480cf65f2e27b317973b8c0995db69 | 0 | returned | 0.6400 | n/a | n/a |
| null_argmax | devs1cam-866e98051dedeb27cf7a85fecc6d0a32 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-8698caaa9bc45e7b762ed3b06bd47d45 | 0 | returned | 2.5900 | n/a | n/a |
| null_argmax | devs1cam-87133eab18a146643bf0823c7a56fac7 | 0 | returned | n/a | 0.0000 | n/a |
| null_argmax | devs1cam-877888c6735f1dca76c43a86f44fdeb5 | 0 | returned | 0.0000 | n/a | n/a |
| null_argmax | devs1cam-88349b7b0fdd2ae5a317a78c9550e623 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-88905f96578b8cadfc92ea93883406b8 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-896d7dcb29a66ee249548d14a1ad2841 | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-899c9025299cf495fd3d0ca818be1fb7 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-89c5d2617b98a34e3302dd594c411a7f | 0 | returned | n/a | 99.0000 | n/a |
| null_argmax | devs1cam-89edf130515f36979b854b48d33a14c6 | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-8a1a8eedbf21529f89091896157a9057 | 0 | returned | n/a | 10.0000 | n/a |
| null_argmax | devs1cam-8a500999c75d8a1d9a4f4fcb634b7a97 | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-8a979b3abff030d4a45889283b52c26e | 0 | returned | 0.2600 | n/a | n/a |
| null_argmax | devs1cam-8ae5a8537ccbc40da4a1269c70ad77cc | 0 | returned | 0.7800 | n/a | n/a |
| null_argmax | devs1cam-8b5fb9cf2e866f24465310d36b052dd9 | 0 | returned | 0.1100 | n/a | n/a |
| null_argmax | devs1cam-8bc385e109ce53b6b828c4da3d0f8b44 | 0 | returned | 0.2900 | n/a | n/a |
| null_argmax | devs1cam-8d14e744f2d40c6cfc8e5f75b3036a10 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-8d2cb8065776ea262e1fb5aad990f894 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-8d91efa63427b4f81a306eb2996d5126 | 0 | returned | n/a | 15.0000 | n/a |
| null_argmax | devs1cam-8db8694dd3b4430f5ad37380ce39afed | 0 | returned | 0.5000 | n/a | n/a |
| null_argmax | devs1cam-8dede8264b43be4f9f76a97b23d18b30 | 0 | returned | 0.4600 | n/a | n/a |
| null_argmax | devs1cam-8e028611da6bce81d51ab169d47cb65c | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-8e055c12febdfa30413dca6695fd8d1d | 0 | returned | 0.0900 | n/a | n/a |
| null_argmax | devs1cam-8e333863432f4c41ffdef8d842e977d7 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-8f077d15a9fdf6662a13eaba1630dadf | 0 | returned | 0.1400 | n/a | n/a |
| null_argmax | devs1cam-8f0ea0e0500274e8f5a60aa02c3dd496 | 0 | returned | n/a | 6.0000 | n/a |
| null_argmax | devs1cam-8f44d7b34e2d8851d196827f07fbafe1 | 0 | returned | 0.2000 | n/a | n/a |
| null_argmax | devs1cam-8f70bd517ed5842308a80e7f87cd0e55 | 0 | returned | n/a | 28.0000 | n/a |
| null_argmax | devs1cam-8f71fc95b94aaab9d94531279ac76859 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-8fbc98f7b2d368f156a7d6c76691dcfe | 0 | returned | 0.6900 | n/a | n/a |
| null_argmax | devs1cam-90c5871835bc55d15c21223041175ee8 | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-90cb36e22bff724116fb8461a7c00f12 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-9130fc1cb6d80cd810105090d0d59d6d | 0 | returned | n/a | 21.0000 | n/a |
| null_argmax | devs1cam-915e8acafcc568f1b7e1780d3c93bf3c | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-9277f3e7669b809af590bc9ed02ea652 | 0 | returned | n/a | 31.0000 | n/a |
| null_argmax | devs1cam-92efe2a3d563d6b53f8cd9650717afc3 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-942bceec79ef54ad20361ca882815728 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-9483a565716d53e6a31e555cd9e30d56 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-9578f4adc786b5c30c669d2d3d0c62c3 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-9601384c89c2e4ded9eb6990e85e7264 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-96dee7cb2c5327d13ac81ccfcd57893f | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-9797e3726c7d48572d8387e9a3f962d1 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-97f274f7f0bd32bf78617f293b8cb48c | 0 | returned | 0.2500 | n/a | n/a |
| null_argmax | devs1cam-983fddb8247c02b3514fd6441dbd3f83 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-98614fb5fa4dd5824d01b2ab23272e57 | 0 | returned | 0.2000 | n/a | n/a |
| null_argmax | devs1cam-98f2007812e37ec2e25b8438c785d12d | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-994081a40cb48cd70def7d6b287f057b | 0 | returned | 0.3700 | n/a | n/a |
| null_argmax | devs1cam-99e244ce603d96012829f0ea549bd620 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-99ed25e0197022edda2c4fa4364a72fd | 0 | returned | n/a | 16.0000 | n/a |
| null_argmax | devs1cam-9a01d0e6ce1042faa18a1102ae3c6e47 | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-9a8db608ee976f7e0e36134398cb85f5 | 0 | returned | n/a | 47.0000 | n/a |
| null_argmax | devs1cam-9bf8cf0a716ea3739829502dfbb622e3 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-9c8aa16bc3b251e715bf8e1f0a342d3c | 0 | returned | n/a | 43.0000 | n/a |
| null_argmax | devs1cam-9dac19f69a1b6bf75e5e445adb6882bf | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-9e1614f93d7fa3db779b02f3a7bae138 | 0 | returned | 0.0700 | n/a | n/a |
| null_argmax | devs1cam-a022bdd0062041f4998af564f26e2658 | 0 | returned | 0.4800 | n/a | n/a |
| null_argmax | devs1cam-a08dbb43caecc161222571b94b872637 | 0 | returned | 0.0100 | n/a | n/a |
| null_argmax | devs1cam-a10b71d7b53e916fe720fcff88336188 | 0 | returned | n/a | 24.0000 | n/a |
| null_argmax | devs1cam-a128d5e1f4fc12687b094f2f3ac91c77 | 0 | returned | 0.0700 | n/a | n/a |
| null_argmax | devs1cam-a1544413e4257cabdfd2926fdb1fad9b | 0 | returned | n/a | 0.0000 | n/a |
| null_argmax | devs1cam-a15a5901d91b07cc930c9e63063047d6 | 0 | returned | 0.0900 | n/a | n/a |
| null_argmax | devs1cam-a17deabef59ec32bfe7813f347d1a308 | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-a21dcc11af700ec9bb93ef1a71b5111c | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-a38aed53757373f4a0e905af32a1741c | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-a3ad5639a615a77b2076c44c717e66db | 0 | returned | 0.3700 | n/a | n/a |
| null_argmax | devs1cam-a4cfd20ab9eafeb380aea46db14905bb | 0 | returned | 0.1900 | n/a | n/a |
| null_argmax | devs1cam-a50984da46e25527d043c1dc766ed2c6 | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-a581bbf0fbb9921793ec8240d0be05ec | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-a5a3052d28bf12a3f318770f86240d18 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-a6d2d6e14e58b0e148285184e6863ae6 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-a6e71784fc1347d454ef4ecc0c6d552e | 0 | returned | n/a | 18.0000 | n/a |
| null_argmax | devs1cam-a7b0535f9cb3ed3d9188f14ed5098b3e | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-a7f6edf87afda6c66b9a7670dfd81fae | 0 | returned | 2.8300 | n/a | n/a |
| null_argmax | devs1cam-a8279221abbed044f088f87619dae21a | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-a8fd6af8498a492331057d060923265e | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-a925b6df0a21afb65b31df518a977f29 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-aa4801358eaaac23def499d7a066409a | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-aa6402ccf7186ad8cf004ba57a2b8941 | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-aad4281c9228c5bc6a95d66e895a875f | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ac1cb26f09606e41818c376f03366a0f | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ac602d365aeacdf8a179a8f70d9156af | 0 | returned | n/a | 118.0000 | n/a |
| null_argmax | devs1cam-ae9942a32cf70b6bc62a81dc0ad56e27 | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-af59a069d7fb19829009f25797beb8c5 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-af66a215b0599f56af4bbc4f68f7aae9 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-af9e2c6598e4e3944755997d465fc8b9 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-b04b4afb81c8062ee3609f1d1e4283f6 | 0 | returned | 0.2800 | n/a | n/a |
| null_argmax | devs1cam-b10e322ca231fa7d49daaccb14a6a665 | 0 | returned | n/a | 13.0000 | n/a |
| null_argmax | devs1cam-b4ad41ef3a5a10d99b546fa01e68584c | 0 | returned | n/a | 16.0000 | n/a |
| null_argmax | devs1cam-b6078b1b9d92f479af60834f947ecba8 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-b6e5cfa5d9307989012d53f63d0e305c | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-b7308a02db220b9af980441da794dab8 | 0 | returned | 0.0000 | n/a | n/a |
| null_argmax | devs1cam-b8a55a66c62e190d02c9968212f55e2a | 0 | returned | 0.0500 | n/a | n/a |
| null_argmax | devs1cam-ba129771ad9baaa801f45fca42f880bb | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-ba394adb360a86fed821893368e4cd2a | 0 | returned | n/a | 14.0000 | n/a |
| null_argmax | devs1cam-ba4560899e77e3d6f3f4ef27d20acf3d | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-bbbddf93cb397bd48f24a0448e6e4225 | 0 | returned | n/a | 30.0000 | n/a |
| null_argmax | devs1cam-bcb5ad45947af16e5f28d5fb11829252 | 0 | returned | 0.8400 | n/a | n/a |
| null_argmax | devs1cam-bcebf4406284f42f489c41fde2b8492a | 0 | returned | 0.3100 | n/a | n/a |
| null_argmax | devs1cam-bcf12b2b29a3f76524d2acac38f02dd1 | 0 | returned | 0.0500 | n/a | n/a |
| null_argmax | devs1cam-bcf65905224204490afeb430b3337ec9 | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-bd00f72b51c8224819d9dada1f8eff9c | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-bd57333c31970bf4d95adf75850578cc | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-bd699ff6855744603df5f827438c8574 | 0 | returned | 0.0600 | n/a | n/a |
| null_argmax | devs1cam-bd84646412253bf82c56b1d3592480c8 | 0 | returned | 0.0500 | n/a | n/a |
| null_argmax | devs1cam-bd999ce1a3ae47d5142d31260572f81d | 0 | returned | 0.1900 | n/a | n/a |
| null_argmax | devs1cam-bda1eceab340255c9c67d42c196b4076 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-bdf1c5b5f7ee6f3b810b36fccd2a145a | 0 | returned | n/a | 16.0000 | n/a |
| null_argmax | devs1cam-be04857120531d0a040f49624d6115ff | 0 | returned | 0.2200 | n/a | n/a |
| null_argmax | devs1cam-be2a8b7bef757f07626b031fa0e3a02c | 0 | returned | n/a | 59.0000 | n/a |
| null_argmax | devs1cam-be83a9feec4e630a532ff2330331b6e8 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-be90bb00bc0b2b91577a66c49c42d3a3 | 0 | returned | 0.0200 | n/a | n/a |
| null_argmax | devs1cam-be91c3a8f6ff92085d42f5b9e09fbb90 | 0 | returned | n/a | 27.0000 | n/a |
| null_argmax | devs1cam-bf82c2868bf1894ce38228169a29e265 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-bfa2caee438ea33ca07f51b380966266 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-c02304abe5f819346c1cfe2679a33ec3 | 0 | returned | 0.0000 | n/a | n/a |
| null_argmax | devs1cam-c03882737ec55c4ba239bfe8a4a95278 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-c0644be078f1db2cafd487bfa5a7b088 | 0 | returned | n/a | 28.0000 | n/a |
| null_argmax | devs1cam-c091a064bdedc2c3e9d92e889414e87e | 0 | returned | 0.1400 | n/a | n/a |
| null_argmax | devs1cam-c0d6bf6233776e576b54167dc3b56d50 | 0 | returned | 0.0900 | n/a | n/a |
| null_argmax | devs1cam-c0e184986fa119c320bc18c2a5f53f60 | 0 | returned | 0.2700 | n/a | n/a |
| null_argmax | devs1cam-c14129ee262a91322510c7ee032de73f | 0 | returned | 0.0200 | n/a | n/a |
| null_argmax | devs1cam-c1752a9c772503e6b52b66d507f4b710 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-c17b484fd3023c3131badd6bbc0a828f | 0 | returned | 1.7300 | n/a | n/a |
| null_argmax | devs1cam-c2b87ae00c3ef9d9da947e3cb0198700 | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-c2ceb11cca4363c296e93d58a69e766b | 0 | returned | 0.9000 | n/a | n/a |
| null_argmax | devs1cam-c302a46ccf165208796597c2510f4647 | 0 | returned | n/a | 6.0000 | n/a |
| null_argmax | devs1cam-c488362d0fc8f14d7c48076137ede89d | 0 | returned | 0.1100 | n/a | n/a |
| null_argmax | devs1cam-c54e0849a9b9f57617f0142b9eb86e37 | 0 | returned | 0.6700 | n/a | n/a |
| null_argmax | devs1cam-c5a0a17b179942f374329af010828248 | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-c7411f83c967792a369a613a0e71511b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-c76d6ddb4a5ff5c2f30a83312ecbcb04 | 0 | returned | 2.8600 | n/a | n/a |
| null_argmax | devs1cam-c79e5c0edd19a9a8035e1fd969f6f76f | 0 | returned | n/a | 85.0000 | n/a |
| null_argmax | devs1cam-c7aab39b4f06c2219e4632690dc7e393 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-c7d09a143d8c4ee2fdbcc59021bd2966 | 0 | returned | 0.4600 | n/a | n/a |
| null_argmax | devs1cam-c85cb7657c0dec4e6d4f51df247d985b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ca64af6a5b4ea0363cb456202ae2e0f4 | 0 | returned | n/a | 19.0000 | n/a |
| null_argmax | devs1cam-ca8a0fc19426e77e2e7cf760981d30be | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-caf201fee4a2125022f292aba9e095e9 | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-cb5bfe5b6afe21cc05ee8e06282dee85 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-cbd5f4f015b2707411ded4fcff760b6d | 0 | returned | 0.1300 | n/a | n/a |
| null_argmax | devs1cam-ccb86e47081baeb174c08933507d44fb | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ccc9f6278b17c1f708090d91ae274443 | 0 | returned | n/a | 12.0000 | n/a |
| null_argmax | devs1cam-cce660785a67b4dca971187eab6f4b18 | 0 | returned | n/a | 14.0000 | n/a |
| null_argmax | devs1cam-cd1a6c238bd3746ed63aa88735ca1895 | 0 | returned | 0.0700 | n/a | n/a |
| null_argmax | devs1cam-cdb99fe782379f91617eb469aa3f3a4a | 0 | returned | n/a | 68.0000 | n/a |
| null_argmax | devs1cam-ce5446131af04c8eb1ca90e9e5f8f214 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-cf7a8adb59908e74396b0305caf22413 | 0 | returned | 0.3200 | n/a | n/a |
| null_argmax | devs1cam-cf9d3b7294f89a136f222539ba3fcc15 | 0 | returned | 0.2500 | n/a | n/a |
| null_argmax | devs1cam-d035183ef78c43cf01beca9637368c2b | 0 | returned | n/a | 6.0000 | n/a |
| null_argmax | devs1cam-d037c8d92af32b28ed26504704f4b33e | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d0b6bbe0d485f3f2852954fa8439cedb | 0 | returned | 0.0700 | n/a | n/a |
| null_argmax | devs1cam-d0b8b9bf6b6de8790f0709bafb42c2b2 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d0f62f1ec0cd67b34be909bc51db97f5 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d287ebc02c4771de8f876c98e1b7e943 | 0 | returned | 0.4400 | n/a | n/a |
| null_argmax | devs1cam-d29d99c3728e911fcf2d237ac6f3113e | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d32079e013ae11d12b8be4f23fb5338d | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d475f752e4f7ccf449345cfd8c5d4440 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d4cf651b885608710d311ad0b7758073 | 0 | returned | n/a | 10.0000 | n/a |
| null_argmax | devs1cam-d4d8c67ba13a53bd6cb7305e78745d3c | 0 | returned | n/a | 13.0000 | n/a |
| null_argmax | devs1cam-d57c2366f6f5c0ca64b2a22da074e197 | 0 | returned | n/a | 8.0000 | n/a |
| null_argmax | devs1cam-d61cbbbcbd424e472b55b899d5718e05 | 0 | returned | 0.0400 | n/a | n/a |
| null_argmax | devs1cam-d635240eed1b2d1cf522a83aa43c05bf | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-d66246db6d6ba5e4bbed4ede2f23a74b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d6c3ef6e54b2dffe79d5bfd3f5b7cc57 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d77b61105f335c59d7bd989a6bc77faf | 0 | returned | 0.1100 | n/a | n/a |
| null_argmax | devs1cam-d7a9e07bd64f8c2b232d81a29efa8a6b | 0 | returned | 3.7100 | n/a | n/a |
| null_argmax | devs1cam-d7d4eb0b26a31f804d5dc4dd6094fbe3 | 0 | returned | n/a | 32.0000 | n/a |
| null_argmax | devs1cam-d83525f8e677da756548de53980eb813 | 0 | returned | 1.2900 | n/a | n/a |
| null_argmax | devs1cam-d8429ebaf1ea0993d6e9ace70be838fd | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-d8ba81eeeddadf155e8fc2638bf6bb3a | 0 | returned | 0.3100 | n/a | n/a |
| null_argmax | devs1cam-d8dc34d4d85be6038b2d39b3634e4f24 | 0 | returned | n/a | 1.0000 | n/a |
| null_argmax | devs1cam-d9daa469f216857cc67fa0530e8c59c3 | 0 | returned | 0.3700 | n/a | n/a |
| null_argmax | devs1cam-d9f6ae3d729e9a4e8f9b97b2af31c886 | 0 | returned | 0.7600 | n/a | n/a |
| null_argmax | devs1cam-da1309eaed7df2d6a30c2e624c2d5383 | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-da88cc894e4c2c65e71c88fed6771996 | 0 | returned | n/a | 2.0000 | n/a |
| null_argmax | devs1cam-dab03f358476674236311cd3b829a165 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-dbf4361fe48a8f8ace48b072266c8b4a | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-dcfbbe69be4976aa9ecfb01d3e1080dd | 0 | returned | 7.3800 | n/a | n/a |
| null_argmax | devs1cam-dd019294f91678c9fd3e25379ce46e90 | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-dd869b302fe111dbab9d483ff02e3055 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-dde36abd8d32ffefeaca1fd2415cd604 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-de9ca21f755fe6cafd89f1ce84afbe37 | 0 | returned | 0.0000 | n/a | n/a |
| null_argmax | devs1cam-dfd2a8c8eb0a21e58167b86cd8e5ba6a | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-e1acae6d43db0cd60bea9f785550a87b | 0 | returned | 0.0500 | n/a | n/a |
| null_argmax | devs1cam-e2d492243567a18de496c869a59cd6ac | 0 | returned | 0.0200 | n/a | n/a |
| null_argmax | devs1cam-e2f99f9b04a4a94201fc44bee78e176c | 0 | returned | 0.2400 | n/a | n/a |
| null_argmax | devs1cam-e6d8b6e07437be2b74ef1e73758fea22 | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-e6f5d3735e2244d40cd2dc7c7d49d453 | 0 | returned | n/a | 21.0000 | n/a |
| null_argmax | devs1cam-e6fac49a6443a6005fecc3b0375abb7e | 0 | returned | 0.7300 | n/a | n/a |
| null_argmax | devs1cam-e7196b6467f78124d993bb8999122eb4 | 0 | returned | n/a | 39.0000 | n/a |
| null_argmax | devs1cam-e768057b0752ef4fde738baf13a0e68d | 0 | returned | 0.1600 | n/a | n/a |
| null_argmax | devs1cam-e802fa5b7b2918a44efb44fc77a1ac6a | 0 | returned | n/a | 11.0000 | n/a |
| null_argmax | devs1cam-e882b7a8629fa59bc04033b7c50688ef | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-e9606e946eecd710a9e6bbfeae0e998b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ea07ae4210e3abdee120f9305aba7b46 | 0 | returned | 1.6400 | n/a | n/a |
| null_argmax | devs1cam-ead1b4fb5b95c572595cc95c9a6e0989 | 0 | returned | 5.0100 | n/a | n/a |
| null_argmax | devs1cam-eae874a60413349d42a8dd93f3336205 | 0 | returned | 0.0200 | n/a | n/a |
| null_argmax | devs1cam-eb07a132caaeb7be8b0910119cb386bc | 0 | returned | 0.3500 | n/a | n/a |
| null_argmax | devs1cam-eb07e274e83b0f461a684eb0ffd13b5b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-eb0f179e32e0587081d84f8ea3150c5b | 0 | returned | 0.0100 | n/a | n/a |
| null_argmax | devs1cam-eb34518c1a090ab0e9cdd6c48c707ace | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ec6c00e232c56dc8415132f6c24afb7b | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ecb9db6f1302b6413b9e6ca015c38be4 | 0 | returned | 0.4400 | n/a | n/a |
| null_argmax | devs1cam-ed6b77db243a54d1381c3dd00bdca8da | 0 | returned | n/a | 3.0000 | n/a |
| null_argmax | devs1cam-ed73545308ead79f95c7a9bb74d497da | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-ed84c61dbde5ab68aeab5a005a791a9e | 0 | returned | n/a | 14.0000 | n/a |
| null_argmax | devs1cam-edac661ee29d27f72c954830838ec6e3 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-edca804cd923f7acd0bcb078605dcd07 | 0 | returned | 0.1200 | n/a | n/a |
| null_argmax | devs1cam-edfc5278137c4b51a9ba99a7b87ed25d | 0 | returned | n/a | 7.0000 | n/a |
| null_argmax | devs1cam-ee19c17d529a785abf6218ee9fb48be5 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-ee982c1184f51e77828bf37cc21b8b48 | 0 | returned | 0.4400 | n/a | n/a |
| null_argmax | devs1cam-eec45efdcef279db3166cce92751ad4d | 0 | returned | n/a | 19.0000 | n/a |
| null_argmax | devs1cam-ef0396683f20d945e6898535e381ad21 | 0 | returned | n/a | 40.0000 | n/a |
| null_argmax | devs1cam-efec944324efe0b3eb395fb1367e4e66 | 0 | returned | 0.1300 | n/a | n/a |
| null_argmax | devs1cam-f0595ffa3a586b8d8a5b2c0b2dca14e9 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-f07715e99a6cc7726d3e26a85bfd645e | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-f1347e043f5205a845097b758b9abff2 | 0 | returned | 1.0800 | n/a | n/a |
| null_argmax | devs1cam-f18f720d2784ed810397fb2361d3c679 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-f1a2ba15c47cc6fdb336d2c63be79da0 | 0 | returned | n/a | 9.0000 | n/a |
| null_argmax | devs1cam-f2bfd0d329f9fa309be7773930e66c55 | 0 | returned | 0.0800 | n/a | n/a |
| null_argmax | devs1cam-f2e015f3b14dc875780f4c647d173695 | 0 | returned | 0.3600 | n/a | n/a |
| null_argmax | devs1cam-f326e38622edbe6109879dc0784f965f | 0 | returned | 0.1400 | n/a | n/a |
| null_argmax | devs1cam-f33cc892a4ba2bcfec746800b01a4e9a | 0 | returned | 0.3000 | n/a | n/a |
| null_argmax | devs1cam-f36d481f33de9f69054a5b08a5b25c24 | 0 | returned | 0.2400 | n/a | n/a |
| null_argmax | devs1cam-f4417b403fffaabe50bac4af4c77976c | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-f472c425b295f1620576f307364be5ab | 0 | returned | n/a | 13.0000 | n/a |
| null_argmax | devs1cam-f478a182c77d9392d78cc110d970b5d6 | 0 | returned | 2.7400 | n/a | n/a |
| null_argmax | devs1cam-f5316bf5ff16257d9587548f1c67ec83 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-f845406344eee35d8e87003a3737fd89 | 0 | returned | n/a | 12.0000 | n/a |
| null_argmax | devs1cam-f866ae99d3db5c3590d990d6d621f6cc | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-f9f52c52e877443c3053641748c4cdaf | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-fa07df6af6ef47bc3b83baeaf44badb1 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-fa38ceae7d5be6c02b695fa308ffd1b1 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-faaa1fab79082817dacb8bb7b32c4519 | 0 | returned | n/a | n/a | True |
| null_argmax | devs1cam-fae38610f0ddd1c022d8079537d9bc25 | 0 | returned | n/a | 4.0000 | n/a |
| null_argmax | devs1cam-fcd098dd942c2ded6599bec14bccaf36 | 0 | returned | n/a | n/a | False |
| null_argmax | devs1cam-fd61e009146cb6d72ef89f6ac1269b42 | 0 | returned | n/a | 5.0000 | n/a |
| null_argmax | devs1cam-fe04c49911ec5a773f3e5975dd1df75a | 0 | returned | n/a | 36.0000 | n/a |
| null_argmax | devs1cam-fe35bce39404594f56ea20f44a491977 | 0 | returned | 2.4100 | n/a | n/a |
| null_argmax | devs1cam-ff3ba6316a032c274ffed6542abba64c | 0 | returned | 0.0400 | n/a | n/a |
| null_argmax | vsi590k_042574 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042574 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042574 | 2 | returned | 0.2500 | n/a | n/a |
| null_argmax | vsi590k_042581 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042581 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042581 | 2 | returned | 1.1088 | n/a | n/a |
| null_argmax | vsi590k_042584 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042584 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042584 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042584 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042584 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042584 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_042588 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042588 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042588 | 2 | returned | 0.0800 | n/a | n/a |
| null_argmax | vsi590k_042597 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042597 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042597 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042597 | 3 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042597 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042597 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_042604 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042604 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042604 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042604 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042604 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042604 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_042608 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042608 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042608 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042608 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042608 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042608 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_042612 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042612 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042612 | 2 | returned | 1.4846 | n/a | n/a |
| null_argmax | vsi590k_042613 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042613 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042613 | 2 | returned | 0.3200 | n/a | n/a |
| null_argmax | vsi590k_042627 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042627 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042627 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042632 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042632 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042632 | 2 | returned | 0.0291 | n/a | n/a |
| null_argmax | vsi590k_042644 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042644 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042644 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042644 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042644 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042644 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_042645 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042645 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042645 | 2 | returned | 0.1900 | n/a | n/a |
| null_argmax | vsi590k_042656 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042656 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042656 | 2 | returned | 0.1893 | n/a | n/a |
| null_argmax | vsi590k_042674 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042674 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042674 | 2 | returned | 0.1100 | n/a | n/a |
| null_argmax | vsi590k_042690 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042690 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042690 | 2 | returned | 0.0900 | n/a | n/a |
| null_argmax | vsi590k_042715 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042715 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042715 | 2 | returned | 1.8900 | n/a | n/a |
| null_argmax | vsi590k_042717 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042717 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042717 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042717 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_042717 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_042717 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_044593 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_044593 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_044593 | 2 | returned | 0.1400 | n/a | n/a |
| null_argmax | vsi590k_044597 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_044597 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_044597 | 2 | returned | 0.0600 | n/a | n/a |
| null_argmax | vsi590k_044622 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_044622 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_044622 | 2 | returned | 0.3900 | n/a | n/a |
| null_argmax | vsi590k_045538 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_045538 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_045538 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_045538 | 3 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_045538 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_045538 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_045546 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_045546 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_045546 | 2 | returned | 0.5906 | n/a | n/a |
| null_argmax | vsi590k_045786 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_045786 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_045786 | 2 | returned | 0.7925 | n/a | n/a |
| null_argmax | vsi590k_046210 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_046210 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_046210 | 2 | returned | 1.0400 | n/a | n/a |
| null_argmax | vsi590k_046212 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_046212 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_046212 | 2 | returned | 0.3800 | n/a | n/a |
| null_argmax | vsi590k_047592 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_047592 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_047592 | 2 | returned | 1.0721 | n/a | n/a |
| null_argmax | vsi590k_050188 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_050188 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_050188 | 2 | returned | 1.1269 | n/a | n/a |
| null_argmax | vsi590k_050630 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_050630 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_050630 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_155738 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_155738 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_155738 | 2 | returned | 0.4210 | n/a | n/a |
| null_argmax | vsi590k_155745 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_155745 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_155745 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_155745 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_155745 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_155745 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_161427 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161427 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161427 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161427 | 3 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161427 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161427 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_161567 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161567 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161567 | 2 | returned | 0.1750 | n/a | n/a |
| null_argmax | vsi590k_161571 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161571 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161571 | 2 | returned | 0.0502 | n/a | n/a |
| null_argmax | vsi590k_161734 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161734 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161734 | 2 | returned | 1.2293 | n/a | n/a |
| null_argmax | vsi590k_161796 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161796 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161796 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161799 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161799 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161799 | 2 | returned | 1.9400 | n/a | n/a |
| null_argmax | vsi590k_161806 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161806 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161806 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161806 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161806 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161806 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_161807 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161807 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161807 | 2 | returned | 0.6195 | n/a | n/a |
| null_argmax | vsi590k_161821 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161821 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161821 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161825 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161825 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161825 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161826 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161826 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161826 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161827 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161827 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161827 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161828 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161828 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161828 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161830 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161830 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161830 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161832 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161832 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161832 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161834 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161834 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161834 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161836 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161836 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161836 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_161841 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161841 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_161841 | 2 | returned | 0.6200 | n/a | n/a |
| null_argmax | vsi590k_163060 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163060 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163060 | 2 | returned | 0.9600 | n/a | n/a |
| null_argmax | vsi590k_163069 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163069 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163069 | 2 | returned | 1.9001 | n/a | n/a |
| null_argmax | vsi590k_163082 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163082 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163082 | 2 | returned | 2.4401 | n/a | n/a |
| null_argmax | vsi590k_163091 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163091 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163091 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163091 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163091 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163091 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163095 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163095 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163095 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163095 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163095 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163095 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163157 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163157 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163157 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163157 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163157 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163157 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163169 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163169 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163169 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163169 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163169 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163169 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163172 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163172 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163172 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163172 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163172 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163172 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163271 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163271 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163271 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163271 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163271 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163271 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163641 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163641 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163641 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163643 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163643 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163643 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163643 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163643 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163643 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163648 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163648 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163648 | 2 | returned | 0.7156 | n/a | n/a |
| null_argmax | vsi590k_163659 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163659 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163659 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163659 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163659 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163659 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163662 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163662 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163662 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163662 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163662 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163662 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163777 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163777 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163777 | 2 | returned | 0.5200 | n/a | n/a |
| null_argmax | vsi590k_163778 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163778 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163778 | 2 | returned | 0.5000 | n/a | n/a |
| null_argmax | vsi590k_163785 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163785 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163785 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163788 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163788 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163788 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163793 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163793 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163793 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163796 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163796 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163796 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163797 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163797 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163797 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163797 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163797 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163797 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163799 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163799 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163799 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163811 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163811 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163811 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163813 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163813 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163813 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163814 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163814 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163814 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_163814 | 3 | error: malformed_v313_call | n/a | n/a | n/a |
| null_argmax | vsi590k_163814 | 4 | error: malformed_v313_call | n/a | n/a | n/a |
| null_argmax | vsi590k_163814 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_163815 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163815 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_163815 | 2 | returned | 0.0858 | n/a | n/a |
| null_argmax | vsi590k_164325 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164325 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164325 | 2 | returned | 0.8189 | n/a | n/a |
| null_argmax | vsi590k_164334 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164334 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164334 | 2 | returned | 1.7000 | n/a | n/a |
| null_argmax | vsi590k_164335 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164335 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164335 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164335 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164335 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164335 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_164340 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164340 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164340 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164340 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164340 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164340 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_164348 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164348 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164348 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164348 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164348 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164348 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_164354 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164354 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164354 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164354 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164354 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164354 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_164784 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164784 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164784 | 2 | returned | 0.4700 | n/a | n/a |
| null_argmax | vsi590k_164785 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164785 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164785 | 2 | returned | 0.5100 | n/a | n/a |
| null_argmax | vsi590k_164801 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164801 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164801 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164801 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164801 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164801 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_164817 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164817 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164817 | 2 | returned | 0.3800 | n/a | n/a |
| null_argmax | vsi590k_164821 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164821 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164821 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164821 | 3 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_164821 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_164821 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_165296 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165296 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165296 | 2 | returned | 0.6000 | n/a | n/a |
| null_argmax | vsi590k_165307 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165307 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_165307 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_165318 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165318 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_165318 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_165323 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165323 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165323 | 2 | returned | 0.0890 | n/a | n/a |
| null_argmax | vsi590k_165343 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165343 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_165343 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_165350 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165350 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165350 | 2 | returned | 1.4950 | n/a | n/a |
| null_argmax | vsi590k_165357 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165357 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_165357 | 2 | returned | 1.2100 | n/a | n/a |
| null_argmax | vsi590k_166609 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_166609 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_166609 | 2 | returned | 0.1923 | n/a | n/a |
| null_argmax | vsi590k_168046 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168046 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168046 | 2 | returned | 2.4527 | n/a | n/a |
| null_argmax | vsi590k_168055 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_168055 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168055 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_168055 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_168055 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168055 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_168067 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168067 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168067 | 2 | returned | 0.2505 | n/a | n/a |
| null_argmax | vsi590k_168070 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_168070 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_168070 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169291 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_169291 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_169291 | 2 | returned | 1.7191 | n/a | n/a |
| null_argmax | vsi590k_169295 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169295 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_169295 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169442 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169442 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169442 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169442 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169442 | 4 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169442 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_169469 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169469 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_169469 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169469 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_169469 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_169469 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_251447 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251447 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251447 | 2 | returned | 1.1839 | n/a | n/a |
| null_argmax | vsi590k_251449 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251449 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251449 | 2 | returned | 0.2873 | n/a | n/a |
| null_argmax | vsi590k_251452 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251452 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251452 | 2 | returned | 1.1400 | n/a | n/a |
| null_argmax | vsi590k_251453 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251453 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251453 | 2 | returned | 1.2600 | n/a | n/a |
| null_argmax | vsi590k_251454 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251454 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251454 | 2 | returned | 1.6675 | n/a | n/a |
| null_argmax | vsi590k_251506 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251506 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251506 | 2 | returned | 0.5100 | n/a | n/a |
| null_argmax | vsi590k_251515 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251515 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251515 | 2 | returned | 0.4400 | n/a | n/a |
| null_argmax | vsi590k_251702 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251702 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251702 | 2 | returned | 0.0490 | n/a | n/a |
| null_argmax | vsi590k_251912 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251912 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251912 | 2 | returned | 0.5200 | n/a | n/a |
| null_argmax | vsi590k_251919 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251919 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251919 | 2 | returned | 0.4869 | n/a | n/a |
| null_argmax | vsi590k_251923 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251923 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251923 | 2 | returned | 1.1491 | n/a | n/a |
| null_argmax | vsi590k_251924 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251924 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251924 | 2 | returned | 1.1489 | n/a | n/a |
| null_argmax | vsi590k_251925 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251925 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251925 | 2 | returned | 0.5805 | n/a | n/a |
| null_argmax | vsi590k_251927 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251927 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251927 | 2 | returned | 0.0000 | n/a | n/a |
| null_argmax | vsi590k_251965 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251965 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_251965 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_251967 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251967 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_251967 | 2 | returned | 1.2500 | n/a | n/a |
| null_argmax | vsi590k_252278 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252278 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252278 | 2 | returned | 0.2723 | n/a | n/a |
| null_argmax | vsi590k_252280 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252280 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252280 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252280 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252280 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252280 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_252282 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252282 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252282 | 2 | returned | 2.3062 | n/a | n/a |
| null_argmax | vsi590k_252283 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252283 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252283 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252491 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252491 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252491 | 2 | returned | 0.2304 | n/a | n/a |
| null_argmax | vsi590k_252493 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252493 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252493 | 2 | returned | 1.1427 | n/a | n/a |
| null_argmax | vsi590k_252496 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252496 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252496 | 2 | returned | 0.2798 | n/a | n/a |
| null_argmax | vsi590k_252497 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252497 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252497 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252497 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252497 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252497 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_252500 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252500 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252500 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252500 | 3 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_252500 | 4 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252500 | 5 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_252505 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252505 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_252505 | 2 | returned | 0.8800 | n/a | n/a |
| null_argmax | vsi590k_253035 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253035 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253035 | 2 | returned | 1.2543 | n/a | n/a |
| null_argmax | vsi590k_253038 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253038 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253038 | 2 | returned | 1.6200 | n/a | n/a |
| null_argmax | vsi590k_253039 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253039 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253039 | 2 | returned | 0.1810 | n/a | n/a |
| null_argmax | vsi590k_253040 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253040 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253040 | 2 | returned | 1.4600 | n/a | n/a |
| null_argmax | vsi590k_253042 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253042 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253042 | 2 | returned | 0.8400 | n/a | n/a |
| null_argmax | vsi590k_253230 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253230 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253230 | 2 | returned | 0.1500 | n/a | n/a |
| null_argmax | vsi590k_253354 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253354 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253354 | 2 | returned | 0.6910 | n/a | n/a |
| null_argmax | vsi590k_253363 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253363 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253363 | 2 | returned | 0.0475 | n/a | n/a |
| null_argmax | vsi590k_253783 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253783 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_253783 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_253784 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_253784 | 1 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_253784 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_254132 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254132 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254132 | 2 | returned | 0.6300 | n/a | n/a |
| null_argmax | vsi590k_254285 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254285 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254285 | 2 | returned | 0.1221 | n/a | n/a |
| null_argmax | vsi590k_254594 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254594 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254594 | 2 | returned | 0.4600 | n/a | n/a |
| null_argmax | vsi590k_254604 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254604 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_254604 | 2 | returned | 0.0798 | n/a | n/a |
| null_argmax | vsi590k_255374 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255374 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255374 | 2 | returned | 0.4544 | n/a | n/a |
| null_argmax | vsi590k_255402 | 0 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_255402 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255402 | 2 | not seen | n/a | n/a | n/a |
| null_argmax | vsi590k_255407 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255407 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255407 | 2 | returned | 0.9900 | n/a | n/a |
| null_argmax | vsi590k_255863 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255863 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255863 | 2 | returned | 0.2600 | n/a | n/a |
| null_argmax | vsi590k_255865 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255865 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_255865 | 2 | returned | 0.1492 | n/a | n/a |
| null_argmax | vsi590k_256028 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_256028 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_256028 | 2 | returned | 0.8100 | n/a | n/a |
| null_argmax | vsi590k_256516 | 0 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_256516 | 1 | selected | n/a | n/a | n/a |
| null_argmax | vsi590k_256516 | 2 | returned | 0.0389 | n/a | n/a |
| null_argmax | room_scene0155_00 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0155_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0155_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0166_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0166_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0261_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0261_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0320_00 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0320_00 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0320_01 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0320_01 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0320_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0320_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0380_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0380_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0401_00 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0401_00 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0475_00 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0475_00 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0475_01 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0475_01 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0475_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0475_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0515_00 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0515_00 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0515_01 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0515_01 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0515_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0515_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0587_00 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0587_00 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0587_01 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0587_02 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | room_scene0587_02 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058413 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058413 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058414 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058415 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058415 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058460 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058535 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058535 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058599 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058599 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_058764 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059181 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059181 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059182 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059182 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059183 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059183 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059475 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059475 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059477 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059493 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059494 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059495 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059529 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059529 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059530 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059530 | 1 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059531 | 0 | unserved | n/a | n/a | n/a |
| null_argmax | vsi590k_059531 | 1 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042574 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042574 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042574 | 2 | returned | 0.2500 | n/a | n/a |
| candidates_argmax | vsi590k_042581 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042581 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042581 | 2 | returned | 1.1088 | n/a | n/a |
| candidates_argmax | vsi590k_042584 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042584 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042584 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042584 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042584 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042584 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042588 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042588 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042588 | 2 | returned | 0.0800 | n/a | n/a |
| candidates_argmax | vsi590k_042597 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042597 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042597 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042597 | 3 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042597 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042597 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042604 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042604 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042604 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042604 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042604 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042604 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042608 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042608 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042608 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042608 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042608 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042608 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042612 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042612 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042612 | 2 | returned | 1.4846 | n/a | n/a |
| candidates_argmax | vsi590k_042613 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042613 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042613 | 2 | returned | 0.3200 | n/a | n/a |
| candidates_argmax | vsi590k_042627 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042627 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042627 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042632 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042632 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042632 | 2 | returned | 0.0291 | n/a | n/a |
| candidates_argmax | vsi590k_042644 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042644 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042644 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042644 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042644 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042644 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042645 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042645 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042645 | 2 | returned | 0.1900 | n/a | n/a |
| candidates_argmax | vsi590k_042656 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042656 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042656 | 2 | returned | 0.1893 | n/a | n/a |
| candidates_argmax | vsi590k_042674 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042674 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042674 | 2 | returned | 0.1100 | n/a | n/a |
| candidates_argmax | vsi590k_042690 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042690 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042690 | 2 | returned | 0.0900 | n/a | n/a |
| candidates_argmax | vsi590k_042715 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042715 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042715 | 2 | returned | 1.8900 | n/a | n/a |
| candidates_argmax | vsi590k_042717 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042717 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042717 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042717 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042717 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_042717 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044593 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044593 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044593 | 2 | returned | 0.1400 | n/a | n/a |
| candidates_argmax | vsi590k_044597 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044597 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044597 | 2 | returned | 0.0600 | n/a | n/a |
| candidates_argmax | vsi590k_044622 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044622 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_044622 | 2 | returned | 0.3900 | n/a | n/a |
| candidates_argmax | vsi590k_045538 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045538 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045538 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045538 | 3 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045538 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045538 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045546 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045546 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045546 | 2 | returned | 0.5906 | n/a | n/a |
| candidates_argmax | vsi590k_045786 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045786 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_045786 | 2 | returned | 0.7925 | n/a | n/a |
| candidates_argmax | vsi590k_046210 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_046210 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_046210 | 2 | returned | 1.0400 | n/a | n/a |
| candidates_argmax | vsi590k_046212 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_046212 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_046212 | 2 | returned | 0.3800 | n/a | n/a |
| candidates_argmax | vsi590k_047592 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_047592 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_047592 | 2 | returned | 1.0721 | n/a | n/a |
| candidates_argmax | vsi590k_050188 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_050188 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_050188 | 2 | returned | 1.1269 | n/a | n/a |
| candidates_argmax | vsi590k_050630 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_050630 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_050630 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155738 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155738 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155738 | 2 | returned | 0.4210 | n/a | n/a |
| candidates_argmax | vsi590k_155745 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155745 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155745 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155745 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155745 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_155745 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161427 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161427 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161427 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161427 | 3 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161427 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161427 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161567 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161567 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161567 | 2 | returned | 0.1750 | n/a | n/a |
| candidates_argmax | vsi590k_161571 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161571 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161571 | 2 | returned | 0.0502 | n/a | n/a |
| candidates_argmax | vsi590k_161734 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161734 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161734 | 2 | returned | 1.2293 | n/a | n/a |
| candidates_argmax | vsi590k_161796 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161796 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161796 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161799 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161799 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161799 | 2 | returned | 1.9400 | n/a | n/a |
| candidates_argmax | vsi590k_161806 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161806 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161806 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161806 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161806 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161806 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161807 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161807 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161807 | 2 | returned | 0.6195 | n/a | n/a |
| candidates_argmax | vsi590k_161821 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161821 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161821 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161825 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161825 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161825 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161826 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161826 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161826 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161827 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161827 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161827 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161828 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161828 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161828 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161830 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161830 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161830 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161832 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161832 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161832 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161834 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161834 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161834 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161836 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161836 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161836 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161841 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161841 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_161841 | 2 | returned | 0.6200 | n/a | n/a |
| candidates_argmax | vsi590k_163060 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163060 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163060 | 2 | returned | 0.9600 | n/a | n/a |
| candidates_argmax | vsi590k_163069 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163069 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163069 | 2 | returned | 1.9001 | n/a | n/a |
| candidates_argmax | vsi590k_163082 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163082 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163082 | 2 | returned | 2.4401 | n/a | n/a |
| candidates_argmax | vsi590k_163091 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163091 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163091 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163091 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163091 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163091 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163095 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163095 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163095 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163095 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163095 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163095 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163157 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163157 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163157 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163157 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163157 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163157 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163169 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163169 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163169 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163169 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163169 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163169 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163172 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163172 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163172 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163172 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163172 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163172 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163271 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163271 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163271 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163271 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163271 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163271 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163641 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163641 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163641 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163643 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163643 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163643 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163643 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163643 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163643 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163648 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163648 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163648 | 2 | returned | 0.7156 | n/a | n/a |
| candidates_argmax | vsi590k_163659 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163659 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163659 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163659 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163659 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163659 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163662 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163662 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163662 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163662 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163662 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163662 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163777 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163777 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163777 | 2 | returned | 0.5200 | n/a | n/a |
| candidates_argmax | vsi590k_163778 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163778 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163778 | 2 | returned | 0.5000 | n/a | n/a |
| candidates_argmax | vsi590k_163785 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163785 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163785 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163788 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163788 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163788 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163793 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163793 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163793 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163796 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163796 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163796 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163797 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163797 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163797 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163797 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163797 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163797 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163799 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163799 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163799 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163811 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163811 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163811 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163813 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163813 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163813 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163814 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163814 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163814 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163814 | 3 | error: malformed_v313_call | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163814 | 4 | error: malformed_v313_call | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163814 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163815 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163815 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_163815 | 2 | returned | 0.0858 | n/a | n/a |
| candidates_argmax | vsi590k_164325 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164325 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164325 | 2 | returned | 0.8189 | n/a | n/a |
| candidates_argmax | vsi590k_164334 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164334 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164334 | 2 | returned | 1.7000 | n/a | n/a |
| candidates_argmax | vsi590k_164335 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164335 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164335 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164335 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164335 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164335 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164340 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164340 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164340 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164340 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164340 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164340 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164348 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164348 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164348 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164348 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164348 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164348 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164354 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164354 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164354 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164354 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164354 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164354 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164784 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164784 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164784 | 2 | returned | 0.4700 | n/a | n/a |
| candidates_argmax | vsi590k_164785 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164785 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164785 | 2 | returned | 0.5100 | n/a | n/a |
| candidates_argmax | vsi590k_164801 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164801 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164801 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164801 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164801 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164801 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164817 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164817 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164817 | 2 | returned | 0.3800 | n/a | n/a |
| candidates_argmax | vsi590k_164821 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164821 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164821 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164821 | 3 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164821 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_164821 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165296 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165296 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165296 | 2 | returned | 0.6000 | n/a | n/a |
| candidates_argmax | vsi590k_165307 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165307 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165307 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165318 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165318 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165318 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165323 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165323 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165323 | 2 | returned | 0.0890 | n/a | n/a |
| candidates_argmax | vsi590k_165343 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165343 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165343 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165350 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165350 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165350 | 2 | returned | 1.4950 | n/a | n/a |
| candidates_argmax | vsi590k_165357 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165357 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_165357 | 2 | returned | 1.2100 | n/a | n/a |
| candidates_argmax | vsi590k_166609 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_166609 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_166609 | 2 | returned | 0.1923 | n/a | n/a |
| candidates_argmax | vsi590k_168046 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168046 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168046 | 2 | returned | 2.4527 | n/a | n/a |
| candidates_argmax | vsi590k_168055 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168055 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168055 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168055 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168055 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168055 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168067 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168067 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168067 | 2 | returned | 0.2505 | n/a | n/a |
| candidates_argmax | vsi590k_168070 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168070 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_168070 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169291 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169291 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169291 | 2 | returned | 1.7191 | n/a | n/a |
| candidates_argmax | vsi590k_169295 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169295 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169295 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169442 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169442 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169442 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169442 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169442 | 4 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169442 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169469 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169469 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169469 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169469 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169469 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_169469 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251447 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251447 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251447 | 2 | returned | 1.1839 | n/a | n/a |
| candidates_argmax | vsi590k_251449 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251449 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251449 | 2 | returned | 0.2873 | n/a | n/a |
| candidates_argmax | vsi590k_251452 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251452 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251452 | 2 | returned | 1.1400 | n/a | n/a |
| candidates_argmax | vsi590k_251453 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251453 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251453 | 2 | returned | 1.2600 | n/a | n/a |
| candidates_argmax | vsi590k_251454 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251454 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251454 | 2 | returned | 1.6675 | n/a | n/a |
| candidates_argmax | vsi590k_251506 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251506 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251506 | 2 | returned | 0.5100 | n/a | n/a |
| candidates_argmax | vsi590k_251515 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251515 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251515 | 2 | returned | 0.4400 | n/a | n/a |
| candidates_argmax | vsi590k_251702 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251702 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251702 | 2 | returned | 0.0490 | n/a | n/a |
| candidates_argmax | vsi590k_251912 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251912 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251912 | 2 | returned | 0.5200 | n/a | n/a |
| candidates_argmax | vsi590k_251919 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251919 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251919 | 2 | returned | 0.4869 | n/a | n/a |
| candidates_argmax | vsi590k_251923 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251923 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251923 | 2 | returned | 1.1491 | n/a | n/a |
| candidates_argmax | vsi590k_251924 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251924 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251924 | 2 | returned | 1.1489 | n/a | n/a |
| candidates_argmax | vsi590k_251925 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251925 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251925 | 2 | returned | 0.5805 | n/a | n/a |
| candidates_argmax | vsi590k_251927 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251927 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251927 | 2 | returned | 0.0000 | n/a | n/a |
| candidates_argmax | vsi590k_251965 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251965 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251965 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251967 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251967 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_251967 | 2 | returned | 1.2500 | n/a | n/a |
| candidates_argmax | vsi590k_252278 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252278 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252278 | 2 | returned | 0.2723 | n/a | n/a |
| candidates_argmax | vsi590k_252280 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252280 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252280 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252280 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252280 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252280 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252282 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252282 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252282 | 2 | returned | 2.3062 | n/a | n/a |
| candidates_argmax | vsi590k_252283 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252283 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252283 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252491 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252491 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252491 | 2 | returned | 0.2304 | n/a | n/a |
| candidates_argmax | vsi590k_252493 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252493 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252493 | 2 | returned | 1.1427 | n/a | n/a |
| candidates_argmax | vsi590k_252496 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252496 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252496 | 2 | returned | 0.2798 | n/a | n/a |
| candidates_argmax | vsi590k_252497 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252497 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252497 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252497 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252497 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252497 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252500 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252500 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252500 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252500 | 3 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252500 | 4 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252500 | 5 | unserved | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252505 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252505 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_252505 | 2 | returned | 0.8800 | n/a | n/a |
| candidates_argmax | vsi590k_253035 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253035 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253035 | 2 | returned | 1.2543 | n/a | n/a |
| candidates_argmax | vsi590k_253038 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253038 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253038 | 2 | returned | 1.6200 | n/a | n/a |
| candidates_argmax | vsi590k_253039 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253039 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253039 | 2 | returned | 0.1810 | n/a | n/a |
| candidates_argmax | vsi590k_253040 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253040 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253040 | 2 | returned | 1.4600 | n/a | n/a |
| candidates_argmax | vsi590k_253042 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253042 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253042 | 2 | returned | 0.8400 | n/a | n/a |
| candidates_argmax | vsi590k_253230 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253230 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253230 | 2 | returned | 0.1500 | n/a | n/a |
| candidates_argmax | vsi590k_253354 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253354 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253354 | 2 | returned | 0.6910 | n/a | n/a |
| candidates_argmax | vsi590k_253363 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253363 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253363 | 2 | returned | 0.0475 | n/a | n/a |
| candidates_argmax | vsi590k_253783 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253783 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253783 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253784 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253784 | 1 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_253784 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254132 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254132 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254132 | 2 | returned | 0.6300 | n/a | n/a |
| candidates_argmax | vsi590k_254285 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254285 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254285 | 2 | returned | 0.1221 | n/a | n/a |
| candidates_argmax | vsi590k_254594 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254594 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254594 | 2 | returned | 0.4600 | n/a | n/a |
| candidates_argmax | vsi590k_254604 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254604 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_254604 | 2 | returned | 0.0798 | n/a | n/a |
| candidates_argmax | vsi590k_255374 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255374 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255374 | 2 | returned | 0.4544 | n/a | n/a |
| candidates_argmax | vsi590k_255402 | 0 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255402 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255402 | 2 | not seen | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255407 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255407 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255407 | 2 | returned | 0.9900 | n/a | n/a |
| candidates_argmax | vsi590k_255863 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255863 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255863 | 2 | returned | 0.2600 | n/a | n/a |
| candidates_argmax | vsi590k_255865 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255865 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_255865 | 2 | returned | 0.1492 | n/a | n/a |
| candidates_argmax | vsi590k_256028 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_256028 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_256028 | 2 | returned | 0.8100 | n/a | n/a |
| candidates_argmax | vsi590k_256516 | 0 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_256516 | 1 | selected | n/a | n/a | n/a |
| candidates_argmax | vsi590k_256516 | 2 | returned | 0.0389 | n/a | n/a |

Any camera type meets the bar: None.

This is an own-versus-own self-check; it is not evidence about the tower arm.
