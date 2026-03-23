import pdb
from pathlib import Path

from tts_dictionary_interface.base import SemanticDictionary

# ==========================================
# 1. HELPER CLASSES
# ==========================================

class EnumValue(SemanticDictionary):
    """
    Represents a single key-value pair in an enumeration.

    Attributes:
        symbol (str): The text label (e.g., "OFF", "ON").
        numeric (str): The integer value associated with the label.
    """
    ATTR_XPATHS = {
        'name': ('@symbol', False, None),
        'symbol': ('@symbol', False, None),
        'numeric': ('@numeric', False, None),
        'value': ('@value', False, None)
    }

class EnumTable(SemanticDictionary):
    """
    Represents a full enumeration table definition.

    Attributes:
        name (str): The unique name of the enum table (e.g., "GUIDANCE_MODE").
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None)
    }
    ITEM_XPATHS = ['values/enum']
    ITEM_CLASSES = [EnumValue]
    ITEM_HUMAN_UNIQUE_IDS = ['symbol | numeric']

class AlgorithmParameter(SemanticDictionary):
    """
    Represents a named parameter input for an algorithm.

    Attributes:
        name (str): The parameter name (e.g., "slope", "intercept").
        value (str): The parameter value.
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None),
        'value': ('text()', False, None)
    }

class ParameterizedAlgorithm(SemanticDictionary):
    """
    Represents a mathematical algorithm definition with specific parameters.

    Attributes:
        name (str): The algorithm identifier (e.g., "poly.linear").
    """
    ATTR_XPATHS = {
        'name': ('@name', False, None)
    }
    ITEM_XPATHS = ['parameter']
    ITEM_CLASSES = [AlgorithmParameter]
    ITEM_HUMAN_UNIQUE_IDS = ['name']

class ReuMuxMapping(SemanticDictionary):
    """
    Represents hardware connectivity information for a channel.

    Attributes:
        reu (str): The Remote Electronics Unit ID.
        mux_id (str): The multiplexer hardware address.
        length (str): Data length in bytes.
        offset (str): Byte offset.
        side (str): Redundancy side (e.g., "A" or "B").
    """
    ATTR_XPATHS = {
        'reu': ('@reu', False, None),
        'mux_id': ('@mux_id', False, None),
        'length': ('@length', False, None),
        'offset': ('@offset', False, None),
        'side': ('@side', False, None),
    }

class FswSpecification(SemanticDictionary):
    """
    Represents Flight Software (FSW) specific configuration for a channel.

    Attributes:
        sbs_buffer_depth (str): The depth of the side-by-side buffer.
    """
    ATTR_XPATHS = {
        'sbs_buffer_depth': ('@sbs_buffer_depth', False, None)
    }
    ITEM_XPATHS = ['reu_mux_mapping']
    ITEM_CLASSES = [ReuMuxMapping]
    ITEM_HUMAN_UNIQUE_IDS = ['reu'] 

class RawToEng(SemanticDictionary):
    """
    Represents a conversion definition from raw Digital Numbers (DN) to Engineering Units (EU).

    Attributes:
        eng_units (str): The resulting units string (e.g., "Volts").
        algorithm (ParameterizedAlgorithm): The mathematical conversion logic.
    """
    ATTR_XPATHS = {
        'eng_units': ('eng_units', True, None),
        'algorithm': ('parameterized_algorithm', False, ParameterizedAlgorithm)
    }

# ==========================================
# 2. DEFINITION CONTAINERS (Namespaces)
# ==========================================

class EnumDefinitions(SemanticDictionary):
    """
    Dedicated container for Enumeration Tables.
    
    Access via ``dictionary.enums``.
    """
    ITEM_XPATHS = ['enum_table']
    ITEM_CLASSES = [EnumTable]
    ITEM_HUMAN_UNIQUE_IDS = ['name']

class TelemetryGroup(SemanticDictionary):
    """
    Represents a logical grouping of channels (e.g., "EPS_HEALTH").

    Attributes:
        group_name (str): The identifier for the group.
        group_desc (str): A description of the group's purpose.

    Custom Behavior:
        Accessing items in this group by key (e.g. ``group['EPS-0001']``) does **not**
        return the raw group XML node. Instead, it resolves the ID to the full
        :class:`FswChannel` definition found in the main dictionary.
    """
    ATTR_XPATHS = {
        'group_name': ('@group_name', False, None),
        'group_desc': ('@group_desc', False, None),
    }
    ITEM_XPATHS = ['group_channel']
    ITEM_CLASSES = [SemanticDictionary] 
    ITEM_HUMAN_UNIQUE_IDS = ['text()']

    def __getitem__(self, item):
        """
        Retrieves the actual FswChannel definition for a member of this group.
        
        Args:
            item (str): The channel name or abbreviation.

        Returns:
            FswChannel: The fully resolved channel object.

        Raises:
            Exception: If the channel is not in the group or cannot be resolved.
        """
        try:
            ref = super().__getitem__(item)
        except Exception:
             raise Exception(f'Channel "{item}" not found in group "{self.group_name}"')

        channel_id = ref.etree.text
        query = f"//telemetry_definitions/telemetry[@abbreviation='{channel_id}' or @name='{channel_id}']"
        matches = self.etree.xpath(query)
        
        if matches:
            return FswChannel(matches[0])
        print(f"Warning: Channel {channel_id} is in group {self.group_name} but has no definition.")
        return None

class GroupDefinitions(SemanticDictionary):
    """
    Dedicated container for Telemetry Groups.
    
    Access via ``dictionary.groups``.
    """
    ITEM_XPATHS = ['group']
    ITEM_CLASSES = [TelemetryGroup]
    ITEM_HUMAN_UNIQUE_IDS = ['group_name']

class Derivation(SemanticDictionary):
    """
    Represents a ground-based calculation definition.

    Attributes:
        id (str): The unique derivation identifier.
        algorithm (ParameterizedAlgorithm): The math to perform.
        trigger_ref (str): The ID of the channel that triggers this calculation.
        parent_refs (list[str]): A list of IDs for input channels used in the calculation.
    """
    ATTR_XPATHS = {
        'id': ('@derivation_id', False, None),
        'algorithm': ('parameterized_algorithm', False, ParameterizedAlgorithm),
        # Map the raw text IDs from the XML tags
        'trigger_ref': ('trigger_id/text()', False, None),
        'parent_refs': ('parent_id/text()', False, None, True)
    }

    def _resolve_channel(self, channel_id):
        """Helper: Finds a channel definition by Name or ID anywhere in the doc."""
        if not channel_id:
            return None
        
        # Search Root for the telemetry definition
        query = f"//telemetry_definitions/telemetry[@abbreviation='{channel_id}' or @name='{channel_id}']"
        matches = self.etree.xpath(query)
        
        if matches:
            return FswChannel(matches[0])
        
        print(f"Warning: Derivation {self.id} references missing channel '{channel_id}'")
        return None

    @property
    def trigger(self):
        """
        The resolved :class:`FswChannel` object for the trigger_id.
        """
        return self._resolve_channel(self.trigger_ref)

    @property
    def parents(self):
        """
        A list of resolved :class:`FswChannel` objects for all parent_ids.
        """
        if not self.parent_refs:
            return []
            
        # Ensure iteration safety
        refs = self.parent_refs if isinstance(self.parent_refs, list) else [self.parent_refs]
        
        # Resolve all
        return [self._resolve_channel(pid) for pid in refs if pid]

class DerivationDefinitions(SemanticDictionary):
    """
    Dedicated container for Derivation Definitions.
    
    Access via ``dictionary.derivations``.
    """
    ITEM_XPATHS = ['derivation']
    ITEM_CLASSES = [Derivation]
    ITEM_HUMAN_UNIQUE_IDS = ['derivation_id']

# ==========================================
# 3. CHANNEL CLASSES (With Expansion)
# ==========================================

class EhaTypeDef(SemanticDictionary):
    """Represents a type definition within the EHA dictionary structure."""
    pass

class BitExtract(SemanticDictionary):
    """
    Represents the logic to extract specific bits from a parent integer.

    Attributes:
        parent_id (str): The ID of the channel containing the source data.
        offset (str): The start bit offset.
        length (str): The number of bits to extract.
    """
    ATTR_XPATHS = {
        'parent_id': ('parent_id', True, None),
        'offset': ('bits/@offset', False, None),
        'length': ('bits/@length', False, None)
    }

    @property
    def parent(self):
        """
        The resolved :class:`FswChannel` object that serves as the source.
        """
        if not self.parent_id:
            return None
        # Try finding by abbreviation (standard for parent_id ref) then name
        query = f"//telemetry_definitions/telemetry[@abbreviation='{self.parent_id}' or @name='{self.parent_id}']"
        matches = self.etree.xpath(query)
        if matches:
            return FswChannel(matches[0])
        return None

class EhaChannel(SemanticDictionary):
    """Base class for all EHA-compatible channels."""
    
    @property
    def ampcs_type(self):
        """
        Maps the dictionary type (integer, unsigned, float) to the AMPCS equivalent
        (dn, eu, state, dnString).
        """
        if not hasattr(self, 'type') or self.type is None:
            return None
        mapping = {
            'enum': 'state', 'integer': 'dn', 'unsigned': 'dn',
            'boolean': 'dn', 'string': 'dnString', 'float': 'eu',
            'time': 'eu'
        }
        return mapping.get(self.type, None)

class BitUnpackedChannel(EhaChannel):
    """
    Represents a bit unpacked ground derived channel.
    
    Attributes:
        id (str): Unique channel abbreviation.
        opscat (str): Operational category.
        module (str): Owning software module.
        description (str): Channel description.
        typedef (EhaTypeDef): Type definition.
    """
    ATTR_XPATHS = {
            'id': ('@abbreviation', False, None),
            'opscat': ('categories/ops_category', True, None),
            'module': ('categories/module', True, None),
            'description': ('sysdesc', True, None),
            'typedef': ('float | integer | enum | bool | var_string', False, EhaTypeDef)
        }

class JavaChannel(EhaChannel):
    """
    Represents a Java-derived ground channel.
    
    Attributes:
        opscat (str): Operational category.
        module (str): Owning software module.
        description (str): Channel description.
        typedef (EhaTypeDef): Type definition.
    """
    ATTR_XPATHS = {
            'opscat': ('@ops_cat', False, None),
            'module': ('@fsw_module', False, None),
            'description': ('sysdesc', True, None),
            'typedef': ('float | integer | enum | bool | var_string', False, EhaTypeDef)
        }

class FswChannel(EhaChannel):
    """
    Represents a standard channel originating from Flight Software (FSW).

    Attributes:
        id (str): Unique channel abbreviation (e.g. "EPS-0001").
        name (str): Human readable name.
        description (str): Detailed description.
        categories_module (str): Owning FSW module.
        categories_opscat (str): Operational category.
        type (str): Data type (float, unsigned, enum, etc).
        byte_length (str): Size in bytes.
        measurement_id (str): Unique Packet ID.
        format (str): Display format string (e.g. "%0.2f").
        enum_name (str): Name of the associated enum table, if applicable.
        boolean_true (str): String representation for True.
        boolean_false (str): String representation for False.
        derivation_ref_id (str): ID of the calculation derivation, if applicable.
        bit_extract (BitExtract): Definition for bit extraction logic.
        raw_to_eng (RawToEng): Definition for DN-to-EU conversion.
        fsw_specification (FswSpecification): Hardware/Buffer configs.
    """
    ATTR_XPATHS = {
            # --- Identity & Metadata ---
            'id': ('@abbreviation', False, None),
            'name': ('@name', False, None),
            'description': ('description', True, None),
            'categories_module': ('categories/module', True, None),
            'categories_opscat': ('categories/ops_category', True, None),
            
            # --- Type & Format ---
            'type': ('@type', False, None),
            'byte_length': ('@byte_length', False, None),
            'measurement_id': ('measurement_id', True, None),
            'format': ('format', True, None),
            'enum_name': ('enum_format/@enum_name', False, None),
            'boolean_true': ('boolean_format/@true_str', False, None),
            'boolean_false': ('boolean_format/@false_str', False, None),
            
            # --- Derivations & conversions ---
            'derivation_ref_id': ('derivation_ref', True, None), # Stores the ID string
            'bit_extract': ('bit_extract', False, BitExtract),
            'raw_to_eng': ('raw_to_eng', False, RawToEng),
            'fsw_specification': ('fsw_specification', False, FswSpecification),
            
            # --- Backwards Compat Aliases ---
            'opscat': ('categories/ops_category', True, None),
            'module': ('categories/module', True, None),
        }

    @property
    def enum(self): #TO DO: Figure out a smart way to generalize this kind of lookup
        """
        The resolved :class:`EnumTable` object referenced by ``enum_name``.
        """
        if not self.enum_name:
            return None
        query = f"//enum_definitions/enum_table[@name='{self.enum_name}']"
        matches = self.etree.xpath(query)
        return EnumTable(matches[0]) if matches else None

    @property
    def derivation(self): #TO DO: Figure out a smart way to generalize this kind of lookup
        """
        The resolved :class:`Derivation` object referenced by ``derivation_ref_id``.
        """
        if not self.derivation_ref_id:
            return None
        query = f"//derivation_definitions/derivation[@derivation_id='{self.derivation_ref_id}']"
        matches = self.etree.xpath(query)
        return Derivation(matches[0]) if matches else None

# ==========================================
# 4. ROOT DICTIONARY
# ==========================================

class ChannelDictionary(SemanticDictionary):
    """
    Root parser for the Channel Dictionary.
    
    This class serves as the entry point for the Channel.xml file. It allows access
    to Channels (primary items) as well as the namespaced containers for
    Enums, Groups, and Derivations.

    Attributes:
        enums (EnumDefinitions): Access to enum tables.
        groups (GroupDefinitions): Access to telemetry groups.
        derivations (DerivationDefinitions): Access to calculation definitions.

    Access patterns:
        >>> # Get a Channel
        >>> chan = dictionary['BATTERY_VOLTAGE']
        
        >>> # Get an Enum
        >>> enum = dictionary.enums['ON_OFF']
        
        >>> # Get a Group
        >>> group = dictionary.groups['EPS_HEALTH']
    """
    
    # 1. Namespaced Containers
    ATTR_XPATHS = {
        'enums': ('enum_definitions', False, EnumDefinitions),
        'groups': ('telemetry_groups', False, GroupDefinitions),
        'derivations': ('derivation_definitions', False, DerivationDefinitions)
    }

    # 2. Channels (Primary Items)
    ITEM_XPATHS = [
        'telemetry_definitions/telemetry'
    ]
    
    ITEM_HUMAN_UNIQUE_IDS = [
        'name|abbreviation'
    ]
    
    ITEM_CLASSES = [
        FswChannel
    ]

# For backwards compatibility
class ChannelEnums(SemanticDictionary):
    """
    Legacy accessor for Enum Tables. Use ``ChannelDictionary.enums`` instead.
    """
    ITEM_XPATHS = ['enum_definitions/enum_table']
    ITEM_HUMAN_UNIQUE_IDS = ['name']
    ITEM_CLASSES = [EnumTable]