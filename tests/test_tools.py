"""Unit test cho 2 tool - chay duoc tren CI, khong goi mang, khong can API key that."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

import main_02_02 as lab  # noqa: E402


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

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
    assert names == {"search_travel_info", "weather_forecast"}
    for tool in lab.TOOLS:
        assert len(tool.description) > 30
