import pytest

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files

from demosat_dictionary_interface.apid import (
    Apid,
    ApidDictionary,
    ContinuousDataProductLimits,
    DownlinkInfo,
)
from tts_dictionary_interface.contracts import ApidContract


@pytest.fixture(scope="module")
def apid_dict():
    resource = files("demosat_dict.dictionaries.v1").joinpath("Apid.xml")
    with as_file(resource) as xml_path:
        return ApidDictionary(xml_path)


def test_apid_dictionary_lookup_by_id_and_name(apid_dict):
    by_id = apid_dict["0"]
    by_name = apid_dict["DATA_PRODUCT_NOMINAL"]

    assert isinstance(by_id, Apid)
    assert isinstance(by_id, ApidContract)
    assert by_id.apid == by_name.apid
    assert by_id.apid == "0"
    assert by_id.apid_id == by_id.apid
    assert by_id.name == "DATA_PRODUCT_NOMINAL"


def test_apid_attributes(apid_dict):
    apid = apid_dict["0"]

    assert apid.format == "DATA_PRODUCT"
    assert apid.recorded == "true"
    assert apid.title == "AWESOME NOMINAL DATA PRODUCT"
    assert apid.description == "This is a totally rad nominal data product that was created for testing."
    assert apid.module == "ant_mgr"
    assert apid.opscat == "AVS"


def test_apid_downlink_info(apid_dict):
    apid = apid_dict["8"]
    downlink = apid.downlink_info

    assert isinstance(downlink, DownlinkInfo)
    assert downlink.product_type == "Data Product"
    assert downlink.auto_delete == "No"
    assert downlink.default_priority == "100"
    assert downlink.compress == "Yes"
    assert downlink.continuous_dp_limits is None


def test_apid_continuous_data_product_limits(apid_dict):
    apid = apid_dict["5"]
    limits = apid.downlink_info.continuous_dp_limits

    assert isinstance(limits, ContinuousDataProductLimits)
    assert limits.continuous_dp_max_size == "5555"
    assert limits.restartable == "Yes"


def test_apid_iteration_and_missing_lookup(apid_dict):
    assert len(apid_dict) == 11
    assert all(isinstance(apid, Apid) for apid in apid_dict)

    with pytest.raises(KeyError):
        apid_dict["does-not-exist"]
