import pytest
import contextlib

# ==========================================
# 0. COMPATIBILITY IMPORTS
# ==========================================
try:
    # Python 3.9+
    from importlib.resources import files, as_file
except ImportError:
    # Backport for older Python versions
    from importlib_resources import files, as_file

from demosat_dictionary_interface.command import (
    CommandDictionary, 
    EnumTable, 
    FswCommand, 
    HwCommand,
    IntegerArgument,
    UnsignedArgument,
    FloatArgument,
    VarStringArgument, 
    RepeatArgument
)

# ==========================================
# 1. FIXTURES
# ==========================================

@pytest.fixture(scope="module")
def cmd_dict():
    """
    Loads the real demosat command dictionary XML once for this module.
    Uses the modern 'files' API compatible with importlib.resources or importlib_resources.
    """
    # 1. Create a reference to the resource within the package
    traversable_path = files("demosat_dict.dictionaries.v1").joinpath("command.xml")
    
    # 2. Use as_file to ensure a concrete Path exists on the file system
    with as_file(traversable_path) as xml_path:
        return CommandDictionary(xml_path)


# ==========================================
# 2. ROOT & ENUM DEFINITIONS
# ==========================================

def test_root_and_enums_separation(cmd_dict):
    """
    Verify the dictionary root correctly separates Commands (items) 
    from Enums (attribute).
    """
    # 1. Verify Commands are accessible via __getitem__
    assert 'ADCS_YAW' in cmd_dict
    
    # 2. Verify Enums are accessible via .enums attribute
    assert cmd_dict.enums is not None
    assert 'HEMISPHERE' in cmd_dict.enums

def test_enum_table_parsing(cmd_dict):
    """
    Verify parsing of EnumTable and EnumValue objects.
    Target: HEMISPHERE
    """
    hemi_enum = cmd_dict.enums['HEMISPHERE']
    assert isinstance(hemi_enum, EnumTable)
    
    # Check individual values
    assert hemi_enum['S_HEMI'].numeric == '0'
    assert hemi_enum['N_HEMI'].numeric == '1'


# ==========================================
# 3. COMMAND DEFINITIONS
# ==========================================

def test_hw_command_attributes(cmd_dict):
    """
    Verify parsing of Hardware Command attributes.
    Target: TEST_HW_CMD_1
    """
    cmd = cmd_dict['TEST_HW_CMD_1']
    assert isinstance(cmd, HwCommand)
    
    assert cmd.opcode == '0x0001'
    assert cmd.opscat == 'AVS'
    assert "HW Command" in cmd.description

def test_fsw_command_attributes(cmd_dict):
    """
    Verify parsing of FSW Command metadata.
    Target: DO_SCIENCE
    """
    cmd = cmd_dict['DO_SCIENCE']
    assert isinstance(cmd, FswCommand)
    
    assert cmd.opcode == '0x0013'
    assert cmd.class_ == 'FSW' # Maps to @class in XML
    assert cmd.module == 'sci'
    assert cmd.completion_required == 'YES'


# ==========================================
# 4. ARGUMENTS (SCALARS)
# ==========================================

def test_integer_argument(cmd_dict):
    """
    Verify parsing of standard IntegerArgument.
    Target: SET_VCDU -> vcdu_number
    """
    cmd = cmd_dict['SET_VCDU']
    arg = cmd.args['vcdu_number']

    assert isinstance(arg, IntegerArgument)
    assert arg.bit_length == '8'
    assert "VCDY number" in arg.description

def test_unsigned_argument(cmd_dict):
    """
    Verify parsing of UnsignedArgument with unit and range metadata.
    Target: SET_HEATER_DUTY -> duty_cycle
    """
    cmd = cmd_dict['SET_HEATER_DUTY']
    arg = cmd.args['duty_cycle']

    assert isinstance(arg, UnsignedArgument)
    assert arg.bit_length == '8'
    assert arg.units == 'percent'
    
    # Verify range constraints
    assert arg.min == '0'
    assert arg.max == '100'

def test_float_argument(cmd_dict):
    """
    Verify parsing of FloatArgument attributes.
    Target: TRACK_GROUND_TARGET -> target_lat
    """
    cmd = cmd_dict['TRACK_GROUND_TARGET']
    arg = cmd.args['target_lat']
    
    assert isinstance(arg, FloatArgument)
    assert arg.bit_length == '32'
    assert arg.units == 'degrees'
    assert arg.min == '-90.0'
    assert arg.max == '90.0'

def test_enum_argument_subset(cmd_dict):
    """
    Verify parsing of EnumArgument with range constraints.
    Target: FORCE_HIGH_SPEED_DUMP -> dump_rate
    """
    cmd = cmd_dict['FORCE_HIGH_SPEED_DUMP']
    arg = cmd.args['dump_rate']
    
    assert arg.enum_name == 'PLAYBACK_RATES'
    assert arg.min == '400_MBPS'
    assert arg.max == '500_MBPS'


def test_enum_link_resolution(cmd_dict):
    """
    Feature: arg.enum property (Dynamic Lookup)
    Target: FORCE_HIGH_SPEED_DUMP -> dump_rate -> PLAYBACK_RATES
    """
    cmd = cmd_dict['FORCE_HIGH_SPEED_DUMP']
    arg = cmd.args['dump_rate']
    
    # 1. Verify the string name
    assert arg.enum_name == 'PLAYBACK_RATES'
    
    # 2. Verify the Object Link
    # This triggers the new @property
    linked_enum = arg.enum 
    
    assert linked_enum is not None
    assert isinstance(linked_enum, EnumTable)
    
    # 3. Verify we can read values from the linked table
    # "400_MBPS" should be in the table with value 3
    assert linked_enum['400_MBPS'].numeric == '3'

# ==========================================
# 5. ARGUMENTS (COMPLEX)
# ==========================================

def test_var_string_regex(cmd_dict):
    """
    Verify parsing of VarStringArgument regex.
    Target: UPDATE_CONFIG_KEY -> config_key
    """
    cmd = cmd_dict['UPDATE_CONFIG_KEY']
    arg = cmd.args['config_key']
    
    assert isinstance(arg, VarStringArgument)
    assert arg.regex == '^[A-Z]{3}_[0-9]{3}$'
    assert arg.max_bit_length == '256'

def test_repeat_argument_nesting(cmd_dict):
    """
    Verify nested structure of RepeatArgument.
    Target: UPLOAD_FILTER_TABLE -> filter_coefficients
    """
    cmd = cmd_dict['UPLOAD_FILTER_TABLE']
    arg = cmd.args['filter_coefficients']
    
    assert isinstance(arg, RepeatArgument)
    
    # 1. Check Repeat Constraints
    assert arg.min_reps == '1'
    assert arg.max_reps == '32'
    
    # 2. Check Children (Content of the repeat block)
    # SemanticDictionary iterates over children, enabling direct membership checks
    child_names = [child.name for child in arg]
    assert 'index' in child_names
    assert 'coeff_value' in child_names
    
    # 3. Check Child Attributes
    assert arg['coeff_value'].bit_length == '32'