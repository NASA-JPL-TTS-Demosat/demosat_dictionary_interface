import pytest

try:
    from importlib.resources import files, as_file
except ImportError:
    from importlib_resources import files, as_file

from demosat_dictionary_interface.evr import (
    EvrDictionary,
    Evr,
    EnumTable,
    StringEvrArgument,
    IntegerEvrArgument,
    FloatEvrArgument,
    EnumEvrArgument,
)
from tts_dictionary_interface.contracts import EvrContract

pytestmark = pytest.mark.unreviewed_ai


@pytest.fixture(scope="module")
def evr_dict():
    """Loads the real demosat EVR dictionary XML once for this module."""
    traversable_path = files("demosat_dict.dictionaries.v1").joinpath("Evr.xml")
    with as_file(traversable_path) as xml_path:
        return EvrDictionary(xml_path)


def test_root_and_enums_separation(evr_dict):
    assert 'EPS_BATTERY_SOC_LOW' in evr_dict
    assert evr_dict.enums is not None
    assert 'SC_MODE' in evr_dict.enums


def test_evr_basic_attributes(evr_dict):
    """
    Target: SEQSVC_EVR_SEQUENCE_ACTIVATED
    """
    evr = evr_dict['SEQSVC_EVR_SEQUENCE_ACTIVATED']
    assert isinstance(evr, Evr)

    assert evr.name == 'SEQSVC_EVR_SEQUENCE_ACTIVATED'
    assert evr.evr_id == '0x01000001'
    assert evr.severity == 'ACTIVITY_LO'
    assert evr.source == 'flight'
    assert evr.module == 'seq'
    assert evr.opscat == 'SEQ'
    assert evr.message == 'Sequence %s is now active in sequence engine number %d'


def test_evr_no_argument_substitution(evr_dict):
    """
    message must be the raw, unformatted template -- no substitution.
    Target: EPS_BATTERY_SOC_LOW
    """
    evr = evr_dict['EPS_BATTERY_SOC_LOW']
    assert evr.message == 'Battery State of Charge has dropped below %f percent.'


def test_evr_arguments(evr_dict):
    """
    Target: CMDSVC_EVR_SEQ_CMD_DISPATCHED -> string_arg + integer_arg
    """
    evr = evr_dict['CMDSVC_EVR_SEQ_CMD_DISPATCHED']
    args = list(evr.args)
    arg_names = [a.name for a in args]

    assert 'cmd_stem' in arg_names
    assert 'seq_name' in arg_names
    assert 'module_name' in arg_names
    assert 'engine_id' in arg_names

    string_args = [a for a in args if isinstance(a, StringEvrArgument)]
    integer_args = [a for a in args if isinstance(a, IntegerEvrArgument)]
    assert len(string_args) == 3
    assert len(integer_args) == 1
    assert integer_args[0].byte_length == '1'


def test_evr_enum_argument_resolution(evr_dict):
    """
    Target: CCO_NOT_SET_FOR_IMM_RESTRCITED -> current_mode -> SC_MODE
    """
    evr = evr_dict['CCO_NOT_SET_FOR_IMM_RESTRCITED']
    args = list(evr.args)
    enum_args = [a for a in args if isinstance(a, EnumEvrArgument)]
    assert len(enum_args) == 1

    arg = enum_args[0]
    assert arg.enum_name == 'SC_MODE'
    assert isinstance(arg.enum, EnumTable)
    assert arg.enum['SAFE'].numeric == '3'


def test_evr_no_arguments(evr_dict):
    """
    Target: SEQSVC_EVR_CMD_COMPLETED_SUCCESS has no <args> tag at all.
    """
    evr = evr_dict['SEQSVC_EVR_CMD_COMPLETED_SUCCESS']
    assert evr.args == []


def test_evr_satisfies_evr_contract(evr_dict):
    """
    Verify Evr satisfies EvrContract against the real DemoSat fixture (#26).
    """
    evr = evr_dict['ADCS_ST_LOCK_LOST']
    assert isinstance(evr, EvrContract)

    assert evr.name == 'ADCS_ST_LOCK_LOST'
    assert evr.severity == 'WARNING_LO'
    assert evr.message == 'Star Tracker %d lost solution.'
