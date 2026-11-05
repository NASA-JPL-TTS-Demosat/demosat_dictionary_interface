import pytest

from demosat_dictionary_interface.fprime.dictionary import FprimeDictionary
from demosat_dictionary_interface.fprime.evr import Event
from tts_dictionary_interface.contracts import EvrContract

pytestmark = pytest.mark.unreviewed_ai


@pytest.fixture(scope="module")
def fprime_dict():
    return FprimeDictionary('v1')


def test_event_lookup_by_name_and_id(fprime_dict):
    by_name = fprime_dict.events['EPS.EPS_BATTERY_SOC_LOW']
    by_id = fprime_dict.events['0x20000001']
    assert isinstance(by_name, Event)
    assert by_name.event_id == by_id.event_id == '0x20000001'


def test_event_satisfies_evr_contract(fprime_dict):
    """
    Verify Event satisfies EvrContract against the F-Prime fixture (#27).
    """
    evr = fprime_dict.events['EPS.EPS_BATTERY_SOC_LOW']
    assert isinstance(evr, EvrContract)

    assert evr.name == 'EPS.EPS_BATTERY_SOC_LOW'
    assert evr.severity == 'WARNING_HI'
    assert evr.message == 'Battery State of Charge has dropped below %f percent.'


def test_event_no_argument_substitution(fprime_dict):
    """
    message must be the raw, unformatted template -- no substitution.
    """
    evr = fprime_dict.events['ADCS.ADCS_ST_LOCK_LOST']
    assert evr.message == 'Star Tracker %d lost solution.'


def test_event_not_found_raises_key_error(fprime_dict):
    with pytest.raises(KeyError):
        fprime_dict.events['DOES_NOT_EXIST']


def test_event_iteration_and_membership(fprime_dict):
    assert 'EPS.EPS_BATTERY_SOC_LOW' in fprime_dict.events
    assert len(fprime_dict.events) == 40
    assert all(isinstance(e, Event) for e in fprime_dict.events)
