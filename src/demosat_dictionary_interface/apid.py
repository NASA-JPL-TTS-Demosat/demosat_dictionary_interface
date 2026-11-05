from tts_dictionary_interface.base import SemanticDictionary
from tts_dictionary_interface.contracts import ApidContract


class ContinuousDataProductLimits(SemanticDictionary):
    """Optional limits for a continuously produced data product."""

    @property
    def continuous_dp_max_size(self):
        return self.node.get("continuous_dp_max_size")

    @property
    def continuous_dp_max_time(self):
        return self.node.get("continuous_dp_max_time")

    @property
    def continuous_dp_max_writes(self):
        return self.node.get("continuous_dp_max_writes")

    @property
    def restartable(self):
        return self.node.get("restartable")


class DownlinkInfo(SemanticDictionary):
    """Downlink handling metadata associated with an APID."""

    @property
    def product_type(self):
        return self.node.get("product_type")

    @property
    def auto_delete(self):
        return self.node.get("auto_delete")

    @property
    def default_priority(self):
        return self.node.get("default_priority")

    @property
    def compress(self):
        return self.node.get("compress")

    @property
    def continuous_dp_limits(self):
        matches = self.node.xpath("continuous_dp_limits")
        if not matches:
            return None
        return ContinuousDataProductLimits(matches[0], document=self.document)


class Apid(SemanticDictionary, ApidContract):
    """
    A single XML Application Packet Identifier definition.

    XML-specific values are intentionally kept in their source
    representation. For example, ``recorded`` is ``"true"`` or ``"false"``
    rather than a Python boolean, matching the existing XML dictionary
    readers.
    """

    ATTR_XPATHS = {
        "apid": ("@apid", False, None),
        "format": ("@format", False, None),
        "name": ("name", True, None),
        "title": ("title", True, None),
        "description": ("description", True, None),
        "module": ("categories/module", True, None),
        "opscat": ("categories/ops_category", True, None),
    }

    @property
    def apid_id(self):
        """Backward-compatible alias for the APID number."""
        return self.apid

    @property
    def recorded(self):
        return self.node.get("recorded")

    @property
    def downlink_info(self):
        matches = self.node.xpath("downlink_info")
        if not matches:
            return None
        return DownlinkInfo(matches[0], document=self.document)


class ApidDictionary(SemanticDictionary):
    """Root reader for a versioned DemoSat APID XML dictionary."""

    ITEM_XPATHS = ["apids/apid_definition"]
    ITEM_HUMAN_UNIQUE_IDS = ["apid|name"]
    ITEM_CLASSES = [Apid]

    def __getitem__(self, item):
        """Look up an APID by numeric ID, then fall back to its child name."""
        try:
            return super().__getitem__(item)
        except KeyError:
            matches = [apid for apid in self if apid.name == item]
            if not matches:
                raise
            if len(matches) > 1:
                raise KeyError(f'More than one element found with name "{item}"')
            return matches[0]

    def __contains__(self, item):
        return super().__contains__(item) or any(
            apid.name == item for apid in self
        )
