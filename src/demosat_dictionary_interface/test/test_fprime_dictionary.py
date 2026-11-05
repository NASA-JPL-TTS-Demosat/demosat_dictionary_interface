import pytest

try:
    from importlib.resources import files, as_file
except ImportError:
    from importlib_resources import files, as_file

from demosat_dictionary_interface.fprime.dictionary import FprimeDictionary

pytestmark = pytest.mark.unreviewed_ai


def test_resolve_by_version_string():
    d = FprimeDictionary('v1')
    assert len(d.channels) == 24
    assert len(d.events) == 40


def test_resolve_by_file_path():
    traversable_path = files("demosat_dictionary_interface.fprime.dictionaries.v1").joinpath(
        "demosat_topology.json"
    )
    with as_file(traversable_path) as json_path:
        d = FprimeDictionary(str(json_path))
    assert len(d.channels) == 24


def test_v1_matches_amples_dictionary_parity_metadata():
    d = FprimeDictionary("v1")
    assert d._data["metadata"]["parity"] == {"channels": 24, "events": 40}
    assert all("." in channel.channel_name for channel in d.channels)
    assert all("." in event.name for event in d.events)
    assert len({channel.channel_id for channel in d.channels}) == 24
    assert len({event.event_id for event in d.events}) == 40


def test_resolve_by_parsed_dict():
    d = FprimeDictionary({'channels': [], 'events': []})
    assert len(d.channels) == 0
    assert len(d.events) == 0


def test_missing_source_raises_value_error():
    with pytest.raises(ValueError):
        FprimeDictionary(None)


def test_unresolvable_version_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        FprimeDictionary('does_not_exist')
