import pdb
from pathlib import Path

from tts_dictionary_interface.base import SemanticDictionary
from tts_dictionary_interface.contracts import (
    ArgumentContract,
    CommandContract,
    EnumTableContract,
    EnumValueContract,
)

# ==========================================
# 1. ENUM DEFINITIONS
# ==========================================

class EnumValue(SemanticDictionary, EnumValueContract):
    """
    Represents a single key-value pair within an enumeration table.

    Attributes:
        symbol (str): The human-readable string key (e.g., "OFF").
        numeric (str): The raw numeric value associated with the symbol (e.g., "0").
    """
    ATTR_XPATHS = {
        'name': ('@symbol', False, None),
        'symbol': ('@symbol', False, None),
        'numeric': ('@numeric', False, None),
        'value': ('@numeric', False, None)
    }

class EnumTable(SemanticDictionary, EnumTableContract):
    """
    Represents a full enumeration definition table.

    Attributes:
        name (str): The unique name of the table (e.g., "HEMISPHERE").
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None)
    }
    ITEM_XPATHS = ['values/enum']
    ITEM_CLASSES = [EnumValue]
    ITEM_HUMAN_UNIQUE_IDS = ['symbol']

    @property
    def values(self):
        return list(self)

class EnumDefinitions(SemanticDictionary):
    """
    A namespaced container for all Enumeration Tables defined in the dictionary.
    """
    ITEM_XPATHS = ['enum_table']
    ITEM_CLASSES = [EnumTable]
    ITEM_HUMAN_UNIQUE_IDS = ['name']

# ==========================================
# 2. ARGUMENT DEFINITIONS
# ==========================================

class CommandArgument(SemanticDictionary):
    """Base class for all command argument types."""
    pass

class EnumArgument(CommandArgument, ArgumentContract):
    """
    Represents a command argument constrained to a specific set of enumerated values.

    Attributes:
        name (str): The argument identifier.
        bit_length (str): The size of the argument in bits.
        enum_name (str): The reference string to the EnumTable (e.g., "PLAYBACK_RATES").
        description (str): Human-readable description of the argument.
        min (str): Minimum valid raw value (from definition).
        max (str): Maximum valid raw value (from definition).
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'bit_length': ('@bit_length', False, None),
        'length': ('@bit_length', False, None),
        'enum_name': ('@enum_name', False, None),
        'description': ('description', True, None),
        'min': ('range_of_values/include/@min', False, None),
        'max': ('range_of_values/include/@max', False, None),
    }

    @property
    def enum(self):
        """
        Resolves the ``enum_name`` string to the actual :class:`EnumTable` object.
        """
        if not getattr(self, 'enum_name', None):
            return None
        query = f"//enum_definitions/enum_table[@name='{self.enum_name}']"
        matches = self.etree.xpath(query)
        return EnumTable(matches[0]) if matches else None

    @property
    def type(self):
        return f'ENUM.{self.enum_name}'

class IntegerArgument(CommandArgument, ArgumentContract):
    """
    Represents a signed integer command argument.

    Attributes:
        name (str): The argument identifier.
        bit_length (str): The size of the argument in bits.
        units (str): Engineering units (e.g., "Volts").
        description (str): Human-readable description.
        min (str): Minimum valid value.
        max (str): Maximum valid value.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'bit_length': ('@bit_length', False, None),
        'length': ('@bit_length', False, None),
        'units': ('@units', False, None),
        'min': ('range_of_values/include/@min', False, None),
        'max': ('range_of_values/include/@max', False, None),
        'description': ('description', True, None),
    }

    @property
    def type(self):
        return f'I{self.bit_length}'

class UnsignedArgument(CommandArgument, ArgumentContract):
    """
    Represents an unsigned integer command argument.

    Attributes:
        name (str): The argument identifier.
        bit_length (str): The size of the argument in bits.
        units (str): Engineering units.
        description (str): Human-readable description.
        min (str): Minimum valid value.
        max (str): Maximum valid value.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'bit_length': ('@bit_length', False, None),
        'length': ('@bit_length', False, None),
        'units': ('@units', False, None),
        'min': ('range_of_values/include/@min', False, None),
        'max': ('range_of_values/include/@max', False, None),
        'description': ('description', True, None),
    }

    @property
    def type(self):
        return f'U{self.bit_length}'


class FloatArgument(CommandArgument, ArgumentContract):
    """
    Represents a floating point command argument.

    Attributes:
        name (str): The argument identifier.
        bit_length (str): The size of the argument in bits.
        units (str): Engineering units.
        description (str): Human-readable description.
        min (str): Minimum valid value.
        max (str): Maximum valid value.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'bit_length': ('@bit_length', False, None),
        'length': ('@bit_length', False, None),
        'units': ('@units', False, None),
        'min': ('range_of_values/include/@min', False, None),
        'max': ('range_of_values/include/@max', False, None),
        'description': ('description', True, None),
    }

    @property
    def type(self):
        return f'F{self.bit_length}'


class VarStringArgument(CommandArgument, ArgumentContract):
    """
    Represents a variable-length string argument.

    Attributes:
        name (str): The argument identifier.
        prefix_bit_length (str): The size (in bits) of the length prefix integer.
        max_bit_length (str): The maximum allowed size of the string payload.
        regex (str): Regex pattern for validation.
        description (str): Human-readable description.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'prefix_bit_length': ('@prefix_bit_length', False, None),
        'max_bit_length': ('@max_bit_length', False, None),
        # ArgumentContract: a variable string's "length" is its max payload size.
        'length': ('@max_bit_length', False, None),
        'regex': ('valid_regex', True, None),
        'description': ('description', True, None),
    }

    @property
    def type(self):
        return f'STRING{self.max_bit_length}'


class RepeatArgument(CommandArgument, ArgumentContract):
    """
    Represents a nested list of arguments that can be repeated multiple times.

    Attributes:
        name (str): The identifier for this repetition block.
        prefix_bit_length (str): Bit length of the integer describing the repetition count.
        min_reps (str): Minimum number of repetitions allowed.
        max_reps (str): Maximum number of repetitions allowed.
        description (str): Human-readable description.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'prefix_bit_length': ('@prefix_bit_length', False, None),
        # ArgumentContract: a repeat block's "length" is the bit length of its
        # repetition-count prefix -- the only single scalar size concept it has.
        'length': ('@prefix_bit_length', False, None),
        'min_reps': ('repeat/@min', False, None),
        'max_reps': ('repeat/@max', False, None),
        'description': ('description', True, None),
    }

    ITEM_XPATHS = [
        'repeat/arguments/enum_arg',
        'repeat/arguments/integer_arg',
        'repeat/arguments/unsigned_arg',
        'repeat/arguments/var_string_arg',
        'repeat/arguments/float_arg'
    ]
    ITEM_HUMAN_UNIQUE_IDS = ['name'] * 5
    ITEM_CLASSES = [
        EnumArgument,
        IntegerArgument,
        UnsignedArgument,
        VarStringArgument,
        FloatArgument
    ]

    @property
    def type(self):
        return f'REPEAT'

class ArgumentList(SemanticDictionary):
    """
    A container for arguments defined directly under a command.
    """
    ITEM_XPATHS = [
        'enum_arg', 'integer_arg', 'unsigned_arg',
        'var_string_arg', 'float_arg', 'repeat_arg'
    ]
    ITEM_HUMAN_UNIQUE_IDS = ['name'] * 6
    ITEM_CLASSES = [
        EnumArgument, IntegerArgument, UnsignedArgument,
        VarStringArgument, FloatArgument, RepeatArgument
    ]

# ==========================================
# 3. COMMAND DEFINITIONS
# ==========================================

class HwCommand(SemanticDictionary, CommandContract):
    """
    Represents a hardware-level command definition.

    Attributes:
        stem (str): The unique command mnemonic (e.g., "NOOP").
        opcode (str): The hexadecimal opcode.
        opscat (str): The operational category.
        description (str): Human-readable description.
    """
    ATTR_XPATHS = {
        'stem': ('@stem', False, None),
        'opcode': ('@opcode', False, None),
        'opscat': ('categories/ops_category', True, None),
        'description': ('description', True, None),
    }
    @property
    def args(self):
        return []

class FswCommand(SemanticDictionary, CommandContract):   
    """
    Represents a Flight Software (FSW) command definition.

    Attributes:
        stem (str): The unique command mnemonic (e.g., "SET_HEATER_STATE").
        opcode (str): The hexadecimal opcode.
        class_ (str): The execution class (e.g., "FSW", "SEQ").
        opscat (str): The operational category (e.g., "EPS").
        module (str): The FSW module owner (e.g., "adcs").
        description (str): Human-readable description.
        completion_required (str): "YES" if command returns a completion packet.
        custom_validation (str): "YES" if command requires specific logic validation.
        prime_string_only (str): "YES" if restricted to prime string.
        args (ArgumentList): The collection of arguments for this command.
    """
    ATTR_XPATHS = {
        'stem': ('@stem', False, None),
        'opcode': ('@opcode', False, None),
        'class_': ('@class', False, None),
        'opscat': ('categories/ops_category', True, None),
        'module': ('categories/module', True, None),
        'description': ('description', True, None),
        'completion_required': ('completion', True, None),
        'custom_validation': ('fsw_specification/@custom_validation_required', False, None),
        'prime_string_only': ('restricted_modes/prime_string_restriction/@prime_string_only', False, None),
        'args': ('arguments', False, ArgumentList)
    }

    @property
    def args(self):
        """
        Returns the ArgumentList wrapper if the arguments tag exists, 
        otherwise returns an empty list.
        """
        # Look for the <arguments> tag specifically
        matches = self.etree.xpath('arguments')
        if matches:
            # If found, wrap it in the ArgumentList class (which is iterable)
            return ArgumentList(matches[0])
        
        # If not found, return an empty list (which is also iterable)
        return []

# ==========================================
# 4. ROOT DICTIONARY
# ==========================================

class CommandDictionary(SemanticDictionary):
    """
    The root parser for the Command Dictionary XML.

    Attributes:
        enums (EnumDefinitions): The container for shared enumeration tables.
    """
    ATTR_XPATHS = {
        'enums': ('enum_definitions', False, EnumDefinitions)
    }

    ITEM_XPATHS = [
        'command_definitions/hw_command',
        'command_definitions/fsw_command'
    ]
    ITEM_HUMAN_UNIQUE_IDS = ['stem', 'stem']
    ITEM_CLASSES = [HwCommand, FswCommand]