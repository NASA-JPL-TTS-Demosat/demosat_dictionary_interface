from tts_dictionary_interface.contracts import ChannelContract


class Channel(ChannelContract):
    """
    A single F-Prime telemetry channel definition.

    Unlike AMPCS's SemanticDictionary-based classes, this implements
    ChannelContract as plain, real properties directly over a parsed JSON
    dict entry -- no dynamic __getattr__ resolution involved.

    F-Prime has no native concept of a channel's `module` distinct from its
    owning component (`opscat` already captures that), and no per-channel
    `measurement_id`/packet ID; both resolve to None per ChannelContract's
    optional-attribute contract.
    """

    def __init__(self, entry):
        self._entry = entry

    @property
    def channel_id(self):
        return self._entry['id']

    @property
    def channel_name(self):
        return self._entry['name']

    @property
    def opscat(self):
        return self._entry['componentName']

    @property
    def type(self):
        return self._entry['type']['name']

    @property
    def type_kind(self):
        """'enum' for enumerated channels, otherwise the F-Prime primitive kind."""
        return self._entry['type'].get('kind')

    @property
    def format(self):
        """Display format string, if any (e.g. '{:.2f} V'). Not part of ChannelContract."""
        return self._entry.get('format')

    @property
    def enumerated_constants(self):
        """List of {'name', 'value'} dicts for enum-typed channels, else None."""
        return self._entry['type'].get('enumeratedConstants')

    # module and measurement_id intentionally not overridden -- they fall
    # through to ChannelContract's optional-attribute placeholders, which
    # resolve to None since this class defines no ATTR_XPATHS-style config
    # and no __getattr__.


class ChannelCollection:
    """
    A name/id-addressable, iterable collection of :class:`Channel` objects.
    """

    def __init__(self, entries):
        self._channels = [Channel(e) for e in entries]

    def __iter__(self):
        return iter(self._channels)

    def __len__(self):
        return len(self._channels)

    def __contains__(self, key):
        return any(c.channel_name == key or c.channel_id == key for c in self._channels)

    def __getitem__(self, key):
        matches = [c for c in self._channels if c.channel_name == key or c.channel_id == key]
        if len(matches) == 0:
            raise KeyError(f'No channel found with name/id "{key}"')
        if len(matches) > 1:
            raise KeyError(f'More than one channel found with name/id "{key}"')
        return matches[0]
