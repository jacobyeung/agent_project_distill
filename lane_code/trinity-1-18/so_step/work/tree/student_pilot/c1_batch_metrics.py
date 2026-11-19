"""Transfer detached scalar metrics together; retain the exact Python sum order."""
import torch


class Components:
    def __init__(self, denominator):
        self.denominator = denominator
        self.rows = []

    def add(self, stream, components):
        self.rows.append((stream, {key: value.detach() if isinstance(value, torch.Tensor) else value
                                   for key, value in components.items()}))

    def finish(self):
        groups, values = {}, {}
        for row, (_, components) in enumerate(self.rows):
            for key, value in components.items():
                if isinstance(value, torch.Tensor):
                    groups.setdefault((value.device, value.dtype), []).append(((row, key), value.reshape(())))
                else:
                    values[row, key] = float(value)
        for entries in groups.values():
            numbers = torch.stack([value for _, value in entries]).cpu().tolist()
            values.update((index, float(value)) for (index, _), value in zip(entries, numbers))
        components, streams = {}, {}
        # GPU summation or summing after division in FP32 would change the logs.
        # These are the same Python double operations in the same row/key order.
        for row, (stream, items) in enumerate(self.rows):
            for key in items:
                components[key] = components.get(key, 0.) + values[row, key] / self.denominator
            streams[stream] = streams.get(stream, 0.) + values[row, stream]
        return components, streams
