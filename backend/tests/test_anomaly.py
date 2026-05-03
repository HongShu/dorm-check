import pytest
from services.anomaly import determine_anomaly


class TestDetermineAnomaly:
    def test_应在未在(self):
        assert determine_anomaly("在校", False) == "应在未在"

    def test_应离已返(self):
        assert determine_anomaly("离校", True) == "应离已返"

    def test_正常_在校且在寝(self):
        assert determine_anomaly("在校", True) is None

    def test_正常_离校且不在寝(self):
        assert determine_anomaly("离校", False) is None

    def test_非法状态返回None(self):
        assert determine_anomaly("未知", True) is None
        assert determine_anomaly("未知", False) is None
