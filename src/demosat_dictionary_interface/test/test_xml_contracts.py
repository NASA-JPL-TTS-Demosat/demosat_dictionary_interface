import pytest

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files

from demosat_dictionary_interface.channel import ChannelDictionary
from demosat_dictionary_interface.command import CommandDictionary
from demosat_dictionary_interface.evr import EvrDictionary
from tts_dictionary_interface.contracts import (
    ArgumentContract,
    ChannelContract,
    CommandContract,
    EnumTableContract,
    EnumValueContract,
    EvrArgumentContract,
    EvrContract,
)


def _load_dictionary(dictionary_class, filename):
    resource = files("demosat_dict.dictionaries.v1").joinpath(filename)
    with as_file(resource) as path:
        return dictionary_class(path)


@pytest.fixture(scope="module")
def channel_dictionary():
    return _load_dictionary(ChannelDictionary, "Channel.xml")


@pytest.fixture(scope="module")
def command_dictionary():
    return _load_dictionary(CommandDictionary, "command.xml")


@pytest.fixture(scope="module")
def evr_dictionary():
    return _load_dictionary(EvrDictionary, "Evr.xml")


def test_every_xml_channel_implements_channel_contract(channel_dictionary):
    for channel in channel_dictionary:
        assert isinstance(channel, ChannelContract)
        assert channel.channel_id
        assert channel.channel_name
        assert channel.opscat
        assert channel.type
        # The contract names are aliases; retain the historical XML names.
        assert channel.channel_id == channel.id
        assert channel.channel_name == channel.name
        assert channel.opscat == channel.categories_opscat


def test_every_xml_event_implements_evr_contract(evr_dictionary):
    for event in evr_dictionary:
        assert isinstance(event, EvrContract)
        assert event.name
        assert event.message
        assert event.severity
        for argument in event.args:
            assert isinstance(argument, EvrArgumentContract)
            assert argument.name


def test_every_xml_command_and_argument_implements_contracts(command_dictionary):
    for command in command_dictionary:
        assert isinstance(command, CommandContract)
        assert command.stem
        assert command.opcode
        assert command.opscat

        for argument in command.args:
            assert isinstance(argument, ArgumentContract)
            assert argument.name
            assert argument.length
            # These are optional in the shared contract, but the XML
            # implementation exposes them where the argument type supports
            # them.
            argument.type
            argument.description
            argument.enum


def test_xml_enum_objects_implement_enum_contracts(
    channel_dictionary, command_dictionary, evr_dictionary
):
    for dictionary in (channel_dictionary, command_dictionary, evr_dictionary):
        for enum_table in dictionary.enums:
            assert isinstance(enum_table, EnumTableContract)
            assert enum_table.name
            assert enum_table.values
            for enum_value in enum_table.values:
                assert isinstance(enum_value, EnumValueContract)
                assert enum_value.name
                assert enum_value.value is not None


def test_xml_contract_optional_attributes_remain_optional(channel_dictionary):
    channel = channel_dictionary["BATTERY_VOLTAGE"]

    # These attributes are format-dependent. Access must be safe even when
    # the XML node does not provide one of them.
    assert channel.module is not None
    assert channel.measurement_id
