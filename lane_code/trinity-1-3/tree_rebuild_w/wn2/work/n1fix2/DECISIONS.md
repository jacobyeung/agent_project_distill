# Build decisions

The sealed producer excludes preparation from its export config hash. Options: change the sealed export format, or retain its hash for export authentication and add a preparation-inclusive continuation identity. Default: retain the sealed format and bind the preparation through checkpoint complete.json and its embedded binding. The checkpoint receipt is a required pinned input; production P bytes remain unavailable.

N identity excludes its own derived identity fields, handover mapping, and host/review attestations to avoid circular hashes. All remaining config fields and authenticated stream receipt database hashes define the target. Mapping values cannot replace them.

The host script requires Python 3.12 or newer, stated in its kit and checked before using modern pathlib/tarfile APIs. This build does not stage an interpreter or launch a job.
