"""Tests for per-model sensor gating and the per-string PV descriptions."""
from types import SimpleNamespace

from custom_components.marstek_local_api.compatibility import CompatibilityMatrix
from custom_components.marstek_local_api.sensor import (
    PV_STRING_SENSOR_TYPES,
    SENSOR_TYPES,
    VENUS_A_UNSUPPORTED_KEYS,
    VENUS_A_ZERO_COUNTER_KEYS,
    _standard_sensor_types,
)


def coordinator_stub(model, firmware):
    return SimpleNamespace(compatibility=CompatibilityMatrix(model, firmware))


def test_venus_a_skips_fields_the_firmware_never_sends():
    keys = {d.key for d in _standard_sensor_types(coordinator_stub("Venus A", 148))}
    assert keys & VENUS_A_UNSUPPORTED_KEYS == set()
    # Everything else is still there
    assert "battery_power" in keys
    assert "battery_soc" in keys
    assert "total_grid_import" in keys


def test_venus_a_zero_counters_disabled_by_default():
    descriptions = {
        d.key: d for d in _standard_sensor_types(coordinator_stub("Venus A", 148))
    }
    for key in VENUS_A_ZERO_COUNTER_KEYS:
        assert descriptions[key].entity_registry_enabled_default is False
    # Working counters stay enabled
    assert descriptions["total_grid_import"].entity_registry_enabled_default is True


def test_other_models_get_unmodified_sensor_types():
    for model, firmware in (("VenusE", 154), ("VenusE 3.0", 139), ("VenusD", 154), ("VenusC", 154)):
        assert _standard_sensor_types(coordinator_stub(model, firmware)) is SENSOR_TYPES


def test_pv_string_descriptions_cover_four_strings_without_current():
    keys = {d.key for d in PV_STRING_SENSOR_TYPES}
    expected = set()
    for n in range(1, 5):
        expected.add(f"pv{n}_power")
        expected.add(f"pv{n}_voltage")
    assert keys == expected


def test_pv_string_value_fns_bind_their_own_key():
    """Guard against the classic late-binding closure bug in the comprehension."""
    data = {"pv": {f"pv{n}_power": float(n) for n in range(1, 5)}}
    data["pv"].update({f"pv{n}_voltage": 10.0 * n for n in range(1, 5)})

    for description in PV_STRING_SENSOR_TYPES:
        assert description.value_fn(data) == data["pv"][description.key]


def test_pv_string_value_fn_handles_missing_data():
    assert PV_STRING_SENSOR_TYPES[0].value_fn({}) is None
