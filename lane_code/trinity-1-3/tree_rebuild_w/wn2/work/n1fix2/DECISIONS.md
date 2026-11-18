# Build decisions

The sealed producer excludes preparation from its export config hash. Options: change the sealed export format, or retain its hash for export authentication and add a preparation-inclusive continuation identity. Default: retain the sealed format and bind the preparation through checkpoint complete.json and its embedded binding. The checkpoint receipt is a required pinned input; production P bytes remain unavailable.

N identity excludes its own derived identity fields, handover mapping, and host/review attestations to avoid circular hashes. All remaining config fields and authenticated stream receipt database hashes define the target. Mapping values cannot replace them.

The host script requires Python 3.12 or newer, stated in its kit and checked before using modern pathlib/tarfile APIs. This build does not stage an interpreter or launch a job.

The complete reviewer variant set also contains fullwidth text, a Cyrillic e and an accented e. Default: apply compatibility decomposition, strip combining marks and normalize the specified Cyrillic e in each independent admission check. This affects input admission only.

N excludes preparation, admission, authorization and milestone-gate records from its canonical config because those records already bind the config identity. Options: a circular whole-config hash or the trainer's established exclusion of derived records. Default: exclude derived records; authenticate preparation separately through the native trainer. P's donor continuation identity still includes its authenticated preparation.
