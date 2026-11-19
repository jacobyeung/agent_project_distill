"""Physical-room separation for calibrated dev reads."""
import re


def room(scene):
    return re.sub(r'_\d{2}$', '', scene)


def partitions(scenes,tuning):
    scenes,tuning=set(scenes),set(tuning)
    tuning_rooms={room(s) for s in tuning}
    legacy=scenes-tuning
    return dict(all_scenes=sorted(scenes),tuning_scenes=sorted(tuning),tuning_rooms=sorted(tuning_rooms),
        legacy_read_scenes=sorted(legacy),room_disjoint_scenes=sorted(s for s in legacy if room(s) not in tuning_rooms),
        overlapping_read_scenes=sorted(s for s in legacy if room(s) in tuning_rooms))
