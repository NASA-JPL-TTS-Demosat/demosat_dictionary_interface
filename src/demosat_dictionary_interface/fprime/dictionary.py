import json
import os
from pathlib import Path
from typing import Optional

try:
    from importlib.resources import files, as_file
except ImportError:
    from importlib_resources import files, as_file

from demosat_dictionary_interface.fprime.channel import ChannelCollection
from demosat_dictionary_interface.fprime.evr import EventCollection

DICTIONARY_MODULE = "demosat_dictionary_interface.fprime.dictionaries"
DICTIONARY_FILENAME = "demosat_topology.json"


class FprimeDictionary:
    """
    Root reader for a single F-Prime JSON topology dictionary.

    Args:
        source (str, os.PathLike, or dict):
            - Version string (e.g. 'v1', 'current'): resolves the packaged
              fixture dictionary from DICTIONARY_MODULE/DICTIONARY_FILENAME.
            - File path string or Path object: parses the specified JSON
              file on disk.
            - dict: uses the pre-parsed JSON data directly.

    Attributes:
        channels (ChannelCollection): All telemetry channel definitions.
        events (EventCollection): All event (EVR) definitions.
    """

    def __init__(self, source=None):
        if source is None:
            raise ValueError(
                f"Must explicitly specify a version (e.g., {self.__class__.__name__}('v1') "
                f"or {self.__class__.__name__}('current')), a file path, or a parsed dict."
            )

        if isinstance(source, dict):
            data = source
        elif isinstance(source, (str, os.PathLike)) and str(source).lower().endswith('.json'):
            with open(source) as f:
                data = json.load(f)
        else:
            package_target = f"{DICTIONARY_MODULE}.{source}"
            try:
                traversable_path = files(package_target).joinpath(DICTIONARY_FILENAME)
                with as_file(traversable_path) as json_path:
                    if not json_path.exists():
                        raise FileNotFoundError(
                            f"File '{DICTIONARY_FILENAME}' not found in package '{package_target}'."
                        )
                    with open(json_path) as f:
                        data = json.load(f)
            except Exception as e:
                raise FileNotFoundError(
                    f"Failed to resolve version '{source}' for {self.__class__.__name__} "
                    f"in '{package_target}/{DICTIONARY_FILENAME}': {e}"
                )

        self._data = data
        self.channels = ChannelCollection(data.get('channels', []))
        self.events = EventCollection(data.get('events', []))

    @property
    def version(self) -> Optional[str]:
        """The dictionary's project version string, if declared in
        ``metadata.projectVersion``. Returns ``None`` when absent."""
        metadata = self._data.get('metadata') or {}
        return metadata.get('projectVersion')
