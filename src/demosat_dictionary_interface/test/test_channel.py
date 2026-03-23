import pytest
# ==========================================
# 0. COMPATIBILITY IMPORTS
# ==========================================
try:
    # Python 3.9+
    from importlib.resources import files, as_file
except ImportError:
    # Backport for older Python versions
    from importlib_resources import files, as_file

from demosat_dictionary_interface.channel import (
    ChannelDictionary, 
    EnumTable, 
    TelemetryGroup,
    Derivation,
    FswChannel
)

# ==========================================
# 1. FIXTURES
# ==========================================

@pytest.fixture(scope="module")
def channel_dict():
    """
    Loads the real demosat channel dictionary XML once for this module.
    Uses the modern 'files' API compatible with importlib.resources or importlib_resources.
    """
    # 1. Create a reference to the resource within the package
    # Note: Ensure the filename casing matches your file system (Channel.xml vs channel.xml)
    traversable_path = files("demosat_dict.dictionaries.v1").joinpath("Channel.xml")
    
    # 2. Use as_file to ensure a concrete Path exists on the file system
    with as_file(traversable_path) as xml_path:
        return ChannelDictionary(xml_path)


# ==========================================
# 2. ROOT & CONTAINERS (Namespaces)
# ==========================================

def test_root_and_containers(channel_dict):
    """
    Verify the root dictionary properly separates Channels from 
    its definition containers (enums, groups, derivations).
    """
    # 1. Channels are primary items
    assert 'BATTERY_VOLTAGE' in channel_dict
    
    # 2. Containers are attributes
    assert channel_dict.enums is not None
    assert 'GUIDANCE_MODE' in channel_dict.enums
    
    assert channel_dict.groups is not None
    assert 'EPS_HEALTH' in channel_dict.groups
    
    assert channel_dict.derivations is not None
    assert 'CALC_TOTAL_POWER' in channel_dict.derivations

def test_enum_definitions(channel_dict):
    """
    Verify parsing of Enum Tables within the container.
    Target: GUIDANCE_MODE
    """
    table = channel_dict.enums['GUIDANCE_MODE']
    assert isinstance(table, EnumTable)
    assert table['IDLE'].numeric == '0'
    assert table['NADIR_POINT'].numeric == '1'

def test_group_definitions(channel_dict):
    """
    Verify parsing of Telemetry Groups.
    Target: EPS_HEALTH
    """
    group = channel_dict.groups['EPS_HEALTH']
    assert isinstance(group, TelemetryGroup)
    assert group.group_desc == "Power System Health Snapshot"
    
    # Verify membership (lookup by Channel Name/ID)
    assert group['EPS-0001'] is not None
    assert group['EPS-0010'] is not None


def test_derivation_definitions(channel_dict):
    """
    Verify parsing of Math Derivations.
    Target: CALC_TOTAL_POWER
    """
    deriv = channel_dict.derivations['CALC_TOTAL_POWER']
    assert isinstance(deriv, Derivation)
    assert deriv.algorithm.name == 'math.multiply'
    
    # 1. Test Trigger Resolution
    # The XML has <trigger_id>EPS-0001</trigger_id>
    assert deriv.trigger is not None
    assert deriv.trigger.name == 'BATTERY_VOLTAGE'
    
    # 2. Test Parent Resolution (List)
    # The XML has parents EPS-0001 and EPS-0002
    assert len(deriv.parents) == 2
    
    parent_names = [p.name for p in deriv.parents]
    assert 'BATTERY_VOLTAGE' in parent_names
    assert 'BUS_CURRENT' in parent_names

# ==========================================
# 3. CHANNELS (Standard & Hardware)
# ==========================================

def test_standard_channel_attributes(channel_dict):
    """
    Verify standard FSW channel metadata and type logic.
    Target: BATTERY_VOLTAGE
    """
    chan = channel_dict['BATTERY_VOLTAGE']
    assert isinstance(chan, FswChannel)
    
    # Identity
    assert chan.id == 'EPS-0001'
    assert chan.ampcs_type == 'eu' # Float maps to EU
    
    # Conversions
    assert chan.raw_to_eng.eng_units == 'Volts'
    assert chan.raw_to_eng.algorithm['c1'].value == '0.015'

def test_hardware_mapping(channel_dict):
    """
    Verify REU/Mux hardware definitions.
    Target: BATTERY_VOLTAGE -> fsw_specification
    """
    chan = channel_dict['BATTERY_VOLTAGE']
    mapping = chan.fsw_specification['MAIN_REU']
    
    assert mapping.mux_id == '0x1000'
    assert mapping.side == 'A'


# ==========================================
# 4. CHANNEL EXPANSIONS (Linking)
# ==========================================

def test_enum_expansion(channel_dict):
    """
    Verify a channel can auto-resolve its Enum Table.
    Target: ADCS_MODE -> GUIDANCE_MODE
    """
    chan = channel_dict['ADCS_MODE']
    
    # 1. Check the reference string
    assert chan.enum_name == 'GUIDANCE_MODE'
    
    # 2. Check the expanded object (Property)
    assert isinstance(chan.enum, EnumTable)
    assert chan.enum.name == 'GUIDANCE_MODE'
    assert chan.enum['NADIR_POINT'].numeric == '1'

def test_derivation_expansion(channel_dict):
    """
    Verify a channel can auto-resolve its Calculation logic.
    Target: TOTAL_POWER_DRAW -> CALC_TOTAL_POWER
    """
    chan = channel_dict['TOTAL_POWER_DRAW']
    
    # 1. Check the reference string
    assert chan.derivation_ref_id == 'CALC_TOTAL_POWER'
    
    # 2. Check the expanded object (Property)
    assert isinstance(chan.derivation, Derivation)
    assert chan.derivation.algorithm.name == 'math.multiply'

def test_bit_extract_expansion(channel_dict):
    """
    Verify a channel can auto-resolve its Parent Channel.
    Target: HEATER_1_ENABLED -> EPS-0010 (HEATER_STATUS_WORD)
    """
    chan = channel_dict['HEATER_1_ENABLED']
    
    # 1. Check extract logic
    assert chan.bit_extract.offset == '0'
    assert chan.bit_extract.length == '1'
    
    # 2. Check Parent Expansion (Property)
    parent = chan.bit_extract.parent
    assert isinstance(parent, FswChannel)
    assert parent.id == 'EPS-0010'
    assert parent.name == 'HEATER_STATUS_WORD'