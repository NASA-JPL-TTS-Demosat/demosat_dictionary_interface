import pytest

from demosat_dictionary_interface.fprime.dictionary import FprimeDictionary
from demosat_dictionary_interface.fprime.channel import Channel
from tts_dictionary_interface.contracts import ChannelContract

pytestmark = pytest.mark.unreviewed_ai


@pytest.fixture(scope="module")
def fprime_dict():
    return FprimeDictionary('v1')


def test_channel_lookup_by_name_and_id(fprime_dict):
    by_name = fprime_dict.channels['CDH.health.BATT_VOLTAGE']
    by_id = fprime_dict.channels['0x1000']
    assert isinstance(by_name, Channel)
    assert by_name.channel_id == by_id.channel_id == '0x1000'


def test_channel_satisfies_channel_contract(fprime_dict):
    """
    Verify Channel satisfies ChannelContract against the F-Prime fixture (#27).
    """
    chan = fprime_dict.channels['CDH.health.BATT_VOLTAGE']
    assert isinstance(chan, ChannelContract)

    assert chan.channel_id == '0x1000'
    assert chan.channel_name == 'CDH.health.BATT_VOLTAGE'
    assert chan.opscat == 'CDH.health'
    assert chan.type == 'F32'


def test_channel_optional_attrs_are_none(fprime_dict):
    """
    F-Prime has no native 'module' (distinct from opscat) or
    'measurement_id' concept -- both must resolve to None, not raise (#27).
    """
    chan = fprime_dict.channels['CDH.health.BATT_VOLTAGE']
    assert chan.module is None
    assert chan.measurement_id is None


def test_enum_channel(fprime_dict):
    chan = fprime_dict.channels['ADCS.starTracker.ST_LOCK_STATE']
    assert chan.type == 'ADCS_StarTrackerLockState'
    assert chan.type_kind == 'enum'
    names = [c['name'] for c in chan.enumerated_constants]
    assert names == ['LOCKED', 'LOST', 'SEARCHING']


def test_channel_not_found_raises_key_error(fprime_dict):
    with pytest.raises(KeyError):
        fprime_dict.channels['DOES_NOT_EXIST']


def test_channel_iteration_and_membership(fprime_dict):
    assert 'CDH.health.BATT_VOLTAGE' in fprime_dict.channels
    assert len(fprime_dict.channels) == 3
    assert all(isinstance(c, Channel) for c in fprime_dict.channels)
