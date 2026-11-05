import pdb
from pathlib import Path

from tts_dictionary_interface.base import SemanticDictionary
from tts_dictionary_interface.contracts import (
    EnumTableContract,
    EnumValueContract,
    EvrArgumentContract,
    EvrContract,
)

# ==========================================
# 1. ENUM DEFINITIONS
# ==========================================

class EnumValue(SemanticDictionary, EnumValueContract):
    """
    Represents a single key-value pair within an enumeration table.

    Attributes:
        symbol (str): The human-readable string key (e.g., "TRUE").
        numeric (str): The raw numeric value associated with the symbol.
    """
    ATTR_XPATHS = {
        'name': ('@symbol', False, None),
        'symbol': ('@symbol', False, None),
        'numeric': ('@numeric', False, None),
    }

    @property
    def value(self):
        return self.numeric

class EnumTable(SemanticDictionary, EnumTableContract):
    """
    Represents a full enumeration definition table.

    Attributes:
        name (str): The unique name of the table (e.g., "SC_MODE").
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
# 2. EVR ARGUMENT DEFINITIONS
# ==========================================

class EvrArgument(SemanticDictionary, EvrArgumentContract):
    """Base class for all EVR argument types."""
    ATTR_XPATHS = {
        'name': ('@name', False, None),
    }

class StringEvrArgument(EvrArgument):
    """Represents a string-typed EVR argument (%s in the format message)."""
    pass

class IntegerEvrArgument(EvrArgument):
    """
    Represents an integer-typed EVR argument (%d in the format message).

    Attributes:
        byte_length (str): Size in bytes.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'byte_length': ('@byte_length', False, None),
    }

    @property
    def length(self):
        return self.byte_length

    @property
    def type(self):
        return 'integer'

class FloatEvrArgument(EvrArgument):
    """
    Represents a float-typed EVR argument (%f in the format message).

    Attributes:
        byte_length (str): Size in bytes.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'byte_length': ('@byte_length', False, None),
    }

    @property
    def length(self):
        return self.byte_length

    @property
    def type(self):
        return 'float'

class EnumEvrArgument(EvrArgument):
    """
    Represents an enumerated EVR argument (%s in the format message,
    rendered via an EnumTable lookup).

    Attributes:
        byte_length (str): Size in bytes.
        enum_name (str): The reference string to the EnumTable.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'byte_length': ('@byte_length', False, None),
        'enum_name': ('@enum_name', False, None),
    }

    @property
    def length(self):
        return self.byte_length

    @property
    def type(self):
        return 'enum'

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

class EvrArgumentList(SemanticDictionary):
    """
    A container for arguments defined directly under an EVR.
    """
    ITEM_XPATHS = [
        'string_arg', 'integer_arg', 'float_arg', 'enum_arg'
    ]
    ITEM_HUMAN_UNIQUE_IDS = ['name'] * 4
    ITEM_CLASSES = [
        StringEvrArgument, IntegerEvrArgument, FloatEvrArgument, EnumEvrArgument
    ]

# ==========================================
# 3. EVR DEFINITION
# ==========================================

class Evr(SemanticDictionary, EvrContract):
    """
    Represents a single Event Record (EVR) definition.

    Attributes:
        name (str): The unique EVR mnemonic (e.g., "EPS_BATTERY_SOC_LOW").
        evr_id (str): The hexadecimal EVR ID.
        severity (str): The severity/level (e.g., "WARNING_HI", "DIAGNOSTIC").
        source (str): Where the EVR originates (e.g., "flight").
        module (str): The owning FSW module (e.g., "eps").
        opscat (str): The operational category (e.g., "EPS").
        message (str): The raw, unformatted printf-style message template.
        number_of_arguments (str): Declared argument count.
        args (EvrArgumentList): The collection of arguments for this EVR.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'evr_id': ('@id', False, None),
        'severity': ('@level', False, None),
        'source': ('@source', False, None),
        'module': ('categories/module', True, None),
        'opscat': ('categories/ops_category', True, None),
        'message': ('format_message', True, None),
        'number_of_arguments': ('number_of_arguments', True, None),
    }

    @property
    def args(self):
        """
        Returns the EvrArgumentList wrapper if the <args> tag exists,
        otherwise returns an empty list.
        """
        matches = self.etree.xpath('args')
        if matches:
            return EvrArgumentList(matches[0])
        return []

# ==========================================
# 4. ROOT DICTIONARY
# ==========================================

class EvrDictionary(SemanticDictionary):
    """
    The root parser for the EVR Dictionary XML.

    Attributes:
        enums (EnumDefinitions): The container for shared enumeration tables.
    """
    ATTR_XPATHS = {
        'enums': ('enum_definitions', False, EnumDefinitions)
    }

    ITEM_XPATHS = ['evrs/evr']
    ITEM_HUMAN_UNIQUE_IDS = ['name|id']
    ITEM_CLASSES = [Evr]
