import pytest

from geo_bakeoff.admission import parse_card


def test_gpu_admission_rejects_busy_or_wrong_host_without_querying_cuda():
    record = "0, GPU-test, RTX 6000 Ada, 49140, 500\n"
    assert parse_card(record, "GPU-other, 42\n", "node-a", "node-a.example")["uuid"] == "GPU-test"
    with pytest.raises(RuntimeError):
        parse_card(record, "GPU-test, 42\n", "node-a", "node-a")
    with pytest.raises(RuntimeError):
        parse_card(record.replace("500", "1025"), "", "node-a", "node-a")
    with pytest.raises(PermissionError):
        parse_card(record, "", "node-b", "node-a")
    with pytest.raises(RuntimeError):
        parse_card(record.replace("49140", "24576"), "", "node-a", "node-a")
