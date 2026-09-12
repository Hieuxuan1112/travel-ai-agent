"""Unit test cho 2 tool - chay duoc tren CI, khong goi mang, khong can API key that."""

import os
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import main_02_02 as lab  # noqa: E402


class _FakeResponse:
    """Gia lap requests.Response - can ca status_code va raise_for_status vi
    _get_json() kiem tra ma trang thai truoc khi doc JSON."""

    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._payload


GEOCODE_PAYLOAD = {
    "results": [
        {"name": "Falmouth", "country": "United States", "country_code": "US",
         "latitude": 41.5, "longitude": -70.6},
        {"name": "Falmouth", "country": "United Kingdom", "country_code": "GB",
         "latitude": 50.15, "longitude": -5.07},
    ]
}
FORECAST_PAYLOAD = {
    "current": {
        "time": "2026-08-11T10:30", "temperature_2m": 14.4, "apparent_temperature": 14.1,
        "precipitation": 0.0, "weather_code": 0, "wind_speed_10m": 9.2,
    }
}


@pytest.fixture
def fake_open_meteo(monkeypatch):
    """Gia lap 2 endpoint cua Open-Meteo, tra ve toa do dua tren URL duoc goi."""
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params))
        if "geocoding" in url:
            return _FakeResponse(GEOCODE_PAYLOAD)
        return _FakeResponse(FORECAST_PAYLOAD)

    monkeypatch.setattr(lab.requests, "get", fake_get)
    return calls


def test_weather_tool_normalises_open_meteo_payload(fake_open_meteo, monkeypatch):
    monkeypatch.setattr(lab, "WEATHER_MODE", "real")
    result = lab.weather_forecast.invoke({"town": "Falmouth"})

    assert result["town"] == "Falmouth"
    assert result["weather"] == "clear sky"  # weather_code 0 -> chu
    assert result["temperature"] == 14.4
    assert result["source"] == "open-meteo.com"


def test_country_argument_disambiguates_same_named_towns(fake_open_meteo, monkeypatch):
    """Falmouth co ca o My lan Anh: truyen country phai chon dung ban ghi Anh."""
    monkeypatch.setattr(lab, "WEATHER_MODE", "real")
    lab.weather_forecast.invoke({"town": "Falmouth", "country": "United Kingdom"})

    forecast_params = [p for url, p in fake_open_meteo if "forecast" in url][0]
    assert forecast_params["latitude"] == 50.15  # toa do cua Falmouth, Cornwall


def test_unknown_town_returns_structured_error(monkeypatch):
    monkeypatch.setattr(lab, "WEATHER_MODE", "real")
    monkeypatch.setattr(lab.requests, "get", lambda *a, **k: _FakeResponse({"results": []}))

    result = lab.weather_forecast.invoke({"town": "Khong Ton Tai 123"})
    assert "error" in result


def test_service_failure_is_reported_as_error_not_exception(monkeypatch):
    """Tool hong phai tra dict co 'error' de LLM tu xu ly, khong duoc nem exception."""
    monkeypatch.setattr(lab, "WEATHER_MODE", "real")

    def boom(*args, **kwargs):
        raise ConnectionError("network down")

    monkeypatch.setattr(lab.requests, "get", boom)
    result = lab.weather_forecast.invoke({"town": "Newquay"})

    assert "error" in result and "network down" in result["details"]


def test_mock_service_matches_book_schema(monkeypatch):
    monkeypatch.setattr(lab, "WEATHER_MODE", "mock")
    result = lab.weather_forecast.invoke({"town": "St Ives"})

    assert result["town"] == "St Ives"
    assert result["weather"] in ["sunny", "foggy", "rainy", "windy"]
    assert 18 <= result["temperature"] <= 31


def test_search_tool_joins_top_documents(monkeypatch):
    class _Doc:
        def __init__(self, text):
            self.page_content = text
            self.metadata = {"source": "https://en.wikivoyage.org/wiki/Cornwall"}

    class _Retriever:
        def invoke(self, query):
            return [_Doc(f"doc{i}") for i in range(6)]

    monkeypatch.setattr(lab, "get_travel_info_retriever", lambda: _Retriever())
    result = lab.search_travel_info.invoke({"query": "beaches"})

    assert result.count("---") == 3  # chi giu 4 ket qua dau -> 3 dau phan cach
    assert "doc4" not in result


def test_existing_but_empty_store_directory_triggers_a_rebuild(monkeypatch, tmp_path):
    """Docker volume moi gan vao: thu muc co san nhung rong -> phai build lai.

    Neu chi kiem tra os.path.isdir thi agent van chay ma tool tim kiem tra ve rong.
    """
    monkeypatch.setattr(lab, "PERSIST_DIR", str(tmp_path))  # thu muc ton tai, rong
    monkeypatch.setattr(lab, "_ti_vectorstore_client", None)

    class _EmptyStore:
        def get(self, limit=None):
            return {"ids": []}

    rebuilt = []
    monkeypatch.setattr(lab, "Chroma", lambda **kwargs: _EmptyStore())
    monkeypatch.setattr(lab, "build_vectorstore", lambda dests: rebuilt.append(dests) or "REBUILT")

    assert lab.get_travel_info_vectorstore() == "REBUILT"
    assert rebuilt == [lab.UK_DESTINATIONS]


def test_both_tools_are_registered_with_descriptions():
    """Mo ta tool la thu LLM dua vao de chon tool -> khong duoc de trong."""
    names = {t.name for t in lab.TOOLS}
    assert names == {"search_travel_info", "weather_forecast", "rank_town_candidates"}
    for tool in lab.TOOLS:
        assert len(tool.description) > 30


def test_temp_score_trong_khoang_la_1():
    assert lab._temp_score(20.0, min_temp_c=15.0, max_temp_c=25.0) == 1.0


def test_temp_score_ngoai_khoang_giam_tuyen_tinh():
    # 10 do, khoang [15, 25], lech 5 do = het bien do -> 0.0
    assert lab._temp_score(10.0, min_temp_c=15.0, max_temp_c=25.0) == 0.0
    # lech 2.5 do trong bien do 5 do -> con 0.5
    assert lab._temp_score(12.5, min_temp_c=15.0, max_temp_c=25.0) == pytest.approx(0.5)


def test_temp_score_qua_xa_khong_am():
    assert lab._temp_score(-10.0, min_temp_c=15.0, max_temp_c=25.0) == 0.0


def test_condition_score_mua_thi_0():
    assert lab._condition_score({"weather": "rain", "precipitation_mm": 2.0}) == 0.0
    assert lab._condition_score({"weather": "thunderstorm", "precipitation_mm": 0}) == 0.0


def test_condition_score_luong_mua_nho_van_0_neu_qua_nguong():
    assert lab._condition_score({"weather": "overcast", "precipitation_mm": 1.0}) == 0.0


def test_condition_score_kho_rao_thi_1():
    assert lab._condition_score({"weather": "clear sky", "precipitation_mm": 0.0}) == 1.0


def test_weather_fit_ket_hop_ca_hai_nua():
    # dep ca nhiet do lan dieu kien -> 1.0
    weather = {"temperature": 20.0, "weather": "clear sky", "precipitation_mm": 0.0}
    assert lab._weather_fit_score(weather, 15.0, 25.0) == 1.0
    # dung nhiet do nhung mua -> chi con nua diem
    weather_rain = {"temperature": 20.0, "weather": "rain", "precipitation_mm": 3.0}
    assert lab._weather_fit_score(weather_rain, 15.0, 25.0) == 0.5


def test_weather_fit_thieu_nhiet_do_thi_0():
    assert lab._weather_fit_score({"weather": "clear sky"}, 15.0, 25.0) == 0.0


class _FakeVectorStoreForRanking:
    """Gia lap similarity_search_with_score: tra ve distance co dinh theo ten town."""

    def __init__(self, distances: dict[str, float]):
        self._distances = distances

    def similarity_search_with_score(self, query, k=1):
        distance = self._distances.get(query, 10.0)  # xa mac dinh neu khong khai bao
        return [(None, distance)]


def test_relevance_score_la_ham_don_dieu_giam_theo_distance(monkeypatch):
    fake_store = _FakeVectorStoreForRanking({"St Ives": 0.1, "Bude": 4.0})
    monkeypatch.setattr(lab, "get_travel_info_vectorstore", lambda: fake_store)

    close = lab._relevance_score("St Ives")
    far = lab._relevance_score("Bude")
    assert close > far
    assert 0.0 < far <= 1.0


def test_score_candidates_khong_relax_khi_du_ung_vien_dat_nguong(monkeypatch):
    monkeypatch.setattr(lab, "_relevance_score", lambda town: 0.9)
    candidates = [
        {"town": "A", "weather": {"temperature": 20.0, "weather": "clear sky",
                                   "precipitation_mm": 0.0}},
        {"town": "B", "weather": {"temperature": 19.0, "weather": "clear sky",
                                   "precipitation_mm": 0.0}},
        {"town": "C", "weather": {"temperature": 30.0, "weather": "rain",
                                   "precipitation_mm": 5.0}},
    ]
    result = lab._score_candidates(candidates, min_temp_c=15.0, max_temp_c=25.0,
                                    min_weather_fit=0.5, top_n=2)

    assert result["relaxed"] is False
    assert result["relax_reason"] is None
    assert [c["town"] for c in result["ranked"]] == ["A", "B"]


def test_score_candidates_relax_khi_khong_du_ung_vien(monkeypatch):
    monkeypatch.setattr(lab, "_relevance_score", lambda town: 0.5)
    candidates = [
        {"town": "A", "weather": {"temperature": 30.0, "weather": "rain",
                                   "precipitation_mm": 5.0}},
        {"town": "B", "weather": {"temperature": 31.0, "weather": "rain",
                                   "precipitation_mm": 5.0}},
    ]
    result = lab._score_candidates(candidates, min_temp_c=15.0, max_temp_c=25.0,
                                    min_weather_fit=0.5, top_n=2)

    assert result["relaxed"] is True
    assert "threshold" in result["relax_reason"]
    assert len(result["ranked"]) == 2


def test_rank_town_candidates_tool_tra_ve_dung_cau_truc(monkeypatch):
    fake_store = _FakeVectorStoreForRanking({"St Ives": 0.2, "Newquay": 0.3})
    monkeypatch.setattr(lab, "get_travel_info_vectorstore", lambda: fake_store)

    fake_weather = {
        "St Ives": {"temperature": 20.0, "weather": "clear sky", "precipitation_mm": 0.0},
        "Newquay": {"temperature": 21.0, "weather": "sunny", "precipitation_mm": 0.0},
    }

    class _FakeWeatherTool:
        def invoke(self, args):
            return fake_weather[args["town"]]

    monkeypatch.setattr(lab, "weather_forecast", _FakeWeatherTool())

    result = lab.rank_town_candidates.invoke({"towns": ["St Ives", "Newquay"]})

    assert result["relaxed"] is False
    assert {c["town"] for c in result["ranked"]} == {"St Ives", "Newquay"}
    assert set(result["ranked"][0]) == {
        "town", "relevance", "weather_fit", "composite", "weather",
    }
    # Nguyen du lieu thoi tiet phai co that de model trich so, khong chi 3 diem so.
    ranked_by_town = {c["town"]: c for c in result["ranked"]}
    assert ranked_by_town["St Ives"]["weather"] == fake_weather["St Ives"]


def test_rank_town_candidates_tool_co_trong_danh_sach_tool():
    assert lab.rank_town_candidates in lab.TOOLS
