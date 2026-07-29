import json
import pytest

from pipeline.mqtt_ingestor import parse_hfp_json

class TestHFPIngestor:

    def test_parse_valid_hfp_telemetry(self):
        """Test parsing a fully populated HSL VP message."""
        raw_bytes = json.dumps({
            "ARR": {
                "desi": "10",
                "veh": "1234",
                "lat": 60.1699,
                "long": 24.9384,
                "tsi": 1718100000,
                "dl": -12,
                "stop": None,
            }
        }).encode("utf-8")

        parsed = parse_hfp_json(raw_bytes)[0]

        assert parsed["route_id"] == "10"
        assert parsed["vehicle_id"] == "1234"
        assert parsed["latitude"] == 60.1699
        assert parsed["longitude"] == 24.9384
        assert parsed["delay_seconds"] == -12

    def test_parse_missing_optional_speed_and_heading(self):
        """Verify speed and heading cleanly default to None when absent in payload."""
        raw_json = json.dumps({
            "VP": {
                "desi": "3",
                "veh": "5500",
                "lat": 60.1800,
                "long": 24.9500,
                "tsi": 1718100050,
            }
        }).encode("utf-8")

        parsed = parse_hfp_json(raw_json)[0]

        assert parsed is not None
        assert parsed["route_id"] == "3"
        assert parsed["speed"] is None
        assert parsed["heading"] == None

    def test_parse_invalid_payload_without_coordinates(self):
        """Verify messages missing spatial data return None to prevent corrupt DB writes."""
        raw_json = json.dumps({"VP": {"desi": "7", "veh": "9999"}}).encode("utf-8")

        parsed = parse_hfp_json(raw_json)
        assert parsed == []  # Should return an empty list since no valid records can be created