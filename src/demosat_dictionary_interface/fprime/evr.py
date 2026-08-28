from tts_dictionary_interface.contracts import EvrContract


class Event(EvrContract):
    """
    A single F-Prime event (EVR) definition.

    Implements EvrContract as plain, real properties directly over a
    parsed JSON dict entry -- no dynamic __getattr__ resolution involved.

    Unlike AIT, F-Prime does have a native severity concept, so `severity`
    is a genuine, always-populated required attribute here (see
    EvrContract's docstring for why severity stays required at the
    contract level even for formats that lack it).
    """

    def __init__(self, entry):
        self._entry = entry

    @property
    def name(self):
        return self._entry['name']

    @property
    def message(self):
        """
        The raw, unformatted printf-style/format-string template -- no
        parameter substitution against live telemetry values.
        """
        return self._entry['formatString']

    @property
    def severity(self):
        return self._entry['severity']

    @property
    def event_id(self):
        """Not part of EvrContract, but useful F-Prime-specific metadata."""
        return self._entry['id']

    @property
    def component_name(self):
        """Not part of EvrContract, but useful F-Prime-specific metadata."""
        return self._entry['componentName']


class EventCollection:
    """
    A name/id-addressable, iterable collection of :class:`Event` objects.
    """

    def __init__(self, entries):
        self._events = [Event(e) for e in entries]

    def __iter__(self):
        return iter(self._events)

    def __len__(self):
        return len(self._events)

    def __contains__(self, key):
        return any(e.name == key or e.event_id == key for e in self._events)

    def __getitem__(self, key):
        matches = [e for e in self._events if e.name == key or e.event_id == key]
        if len(matches) == 0:
            raise KeyError(f'No event found with name/id "{key}"')
        if len(matches) > 1:
            raise KeyError(f'More than one event found with name/id "{key}"')
        return matches[0]
