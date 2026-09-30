from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from obspy import Stream, Trace, UTCDateTime
from obspy.core.inventory import Inventory, Response, Channel, Station, Network

from configs.configs import GeoSeisSettings
from src.io import dataset_inventory as inventory_module
from src.io.dataset_inventory import DatasetInventory, StationData, ChannelData


def make_settings(tmp_path: Path) -> GeoSeisSettings:
    """Create Temporary directory for testing

    Args:
        tmp_path (Path): _description_

    Returns:
        GeoSeisSettings: Settings Object
    """
    
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(exist_ok=True)
    return GeoSeisSettings(
        PROJECT_ROOT=tmp_path,
        RAW_DATA_DIR=raw_dir,
        RAW_DIR=raw_dir,
    )


def make_trace(
    station: str = "STA1",
    channel: str = "HHZ",
    network: str = "XX",
    starttime: str = "2026-01-01T00:00:00"
) -> Trace:
    """ Create a temporary fake trace object

    Args:
        station (str, optional): _description_. Defaults to "STA1".
        channel (str, optional): _description_. Defaults to "HHZ".
        network (str, optional): _description_. Defaults to "XX".
        starttime (_type_, optional): _description_. Defaults to "2026-01-01T00:00:00".

    Returns:
        Trace: Trace Object
    """
    trace = Trace(data=np.arange(100, dtype=np.int32))
    trace.stats.station = station
    trace.stats.channel = channel
    trace.stats.network = network
    trace.stats.starttime = UTCDateTime(starttime)
    trace.stats.sampling_rate = 20.0
    trace.stats.mseed = {"encoding": "STEIM2"}
    
    return trace


def make_metadata() -> pd.DataFrame:
    """Create Metadata as pandas dataframes

    Returns:
        pd.DataFrame: _description_
    """
    return pd.DataFrame(
        [
            {
                "file": "STA1/HHZ/one.mseed",
                "network": "XX",
                "station": "STA1",
                "channel": "HHZ",
                "starttime": pd.Timestamp("2026-01-01T00:00:00Z"),
                "endtime": pd.Timestamp("2026-01-01T00:00:09.9Z"),
                "sampling_rate": 10.0,
                "number_of_samples": 100,
            },
            {
                "file": "STA1/HHZ/two.mseed",
                "network": "XX",
                "station": "STA1",
                "channel": "HHZ",
                "starttime": pd.Timestamp("2026-01-01T00:00:10Z"),
                "endtime": pd.Timestamp("2026-01-01T00:00:19.9Z"),
                "sampling_rate": 10.0,
                "number_of_samples": 100,
            },
            {
                "file": "STA1/HHN/one.mseed",
                "network": "XX",
                "station": "STA1",
                "channel": "HHN",
                "starttime": pd.Timestamp("2026-01-01T00:00:00Z"),
                "endtime": pd.Timestamp("2026-01-01T00:00:09.9Z"),
                "sampling_rate": 10.0,
                "number_of_samples": 100,
            },
            {
                "file": "STA2/HHZ/one.mseed",
                "network": "YY",
                "station": "STA2",
                "channel": "HHZ",
                "starttime": pd.Timestamp("2026-01-02T00:00:00Z"),
                "endtime": pd.Timestamp("2026-01-02T00:00:09.9Z"),
                "sampling_rate": 20.0,
                "number_of_samples": 200,
            },
        ]
    )

def make_station(settings: GeoSeisSettings, metadata: pd.DataFrame) -> StationData:
    """ Create Station Data

    Args:
        settings (GeoSeisSettings): _description_
        metadata (pd.DataFrame): _description_

    Returns:
        StationData: StationData Class
    """
    
    station_rows = metadata.loc[metadata["station"] == "STA1"].copy()
    files = [settings.RAW_DATA_DIR / row for row in station_rows["file"]]
    
    return StationData(
        network="XX",
        code="STA1",
        files=files,
        metadata=station_rows,
        all_metadata=metadata,
        settings=settings,
    )

def make_inventory(station_code: str = "STA1") -> Inventory:
    """ Create an Inventory object for test

    Args:
        station_code (str, optional): _description_. Defaults to "STA1".

    Returns:
        Inventory: Inventory object
    """
    
    response = Response()
    
    channel = Channel(
        code="HHZ",
        location_code="",
        latitude=-38.0,
        longitude=176.0,
        elevation=100.0,
        depth=0.0,
        azimuth=0.0,
        dip=-90.0,
        sample_rate=100.0,
        response=response,
    )
    
    station = Station(
        code=station_code,
        latitude=-38.0,
        longitude=176.0,
        elevation=100.0,
        channels=[channel],
    )
    
    return Inventory(networks=[Network(code="XX", stations=[station])], source="test")


class TestStationData:
    def test_station_summaries_group_by_channel(self, tmp_path):
        metadata = make_metadata()
        station = make_station(settings=make_settings(tmp_path), metadata=metadata)
        
        sizes = station.get_size()
        aggregate = station.get_aggregate()
        coverage = station.get_coverage()
        
        assert sizes.loc[("STA1", "HHZ")] == 2
        assert sizes.loc[("STA1", "HHN")] == 1
        assert aggregate.loc[("STA1", "HHZ"), "total_samples"] == 200
        assert aggregate.loc[("STA1", "HHZ"), "files"] == 2
        assert len(coverage) == 2
        assert set(coverage["station"]) == {"STA1"}
    
    def test_all_station_summaries_include_all_metadata(self, tmp_path):
        station = make_station(make_settings(tmp_path), make_metadata())
        
        assert station.get_stations_size().loc[("STA2", "HHZ")] == 1
        aggregate = station.get_stations_aggregate()
        assert aggregate.loc[("STA2", "HHZ"), "total_samples"] == 200
        assert set(station.get_stations_coverage()["station"]) == {"STA1", "STA2"}
    
    def test_check_gaps_reads_only_this_station_files(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        station = make_station(settings, make_metadata())
        read_paths = []

        def read_file(path):
            read_paths.append(Path(path))
            return Stream([make_trace(station="STA1")])

        monkeypatch.setattr(inventory_module, "read", read_file)
        station.check_gaps()

        assert len(read_paths) == 3
        assert all(path.is_relative_to(settings.RAW_DATA_DIR) for path in read_paths)
            
class TestChannelData:
    def test_get_info_reads_all_inventories(self):
        channels = ChannelData(inventory=[make_inventory("STA1"), make_inventory("STA2")])

        info = channels.get_info()

        assert list(info["station"]) == ["STA1", "STA2"]
        assert set(info["channel_code"]) == {"HHZ"}

    def test_get_info_accepts_single_inventory_and_channel_filter(self):
        channels = ChannelData(inventory=[])

        info = channels.get_info(
            source_inventory=make_inventory("STA1"), channel_code="HHZ"
        )

        assert len(info) == 1
        assert info.iloc[0]["station"] == "STA1"
        assert info.iloc[0]["sample_rate"] == 100.0
        
    def test_get_info_returns_requested_response(self):
        inventory = make_inventory()
        expected_response = inventory[0][0][0].response

        response = ChannelData(inventory=[]).get_info(
            source_inventory=inventory,
            channel_code="HHZ",
            response=True,
        )

        assert response is expected_response


class TestDatasetInventory:
    def test_init_attribute_proxy_and_string(self, tmp_path):
        settings = make_settings(tmp_path)
        inventory = DatasetInventory(settings)

        assert inventory.RAW_DATA_DIR == settings.RAW_DATA_DIR
        assert "settings=" in str(inventory)
    
    def test_get_dir_and_check_returns_settings(self, tmp_path):
        settings = make_settings(tmp_path)
        inventory = DatasetInventory(settings)

        assert inventory.get_dir_and_check() is settings
    
    def test_get_dir_and_check_raises_for_missing_path(self, tmp_path):
        settings = make_settings(tmp_path)
        settings.RAW_DIR = tmp_path / "missing"

        with pytest.raises(FileNotFoundError, match="RAW_DIR"):
            DatasetInventory(settings).get_dir_and_check()
    
    def test_find_all_files_recursively_and_filter_extension(self, tmp_path):
        settings = make_settings(tmp_path)
        nested = settings.RAW_DATA_DIR / "STA1" / "HHZ"
        nested.mkdir(parents=True)
        expected = nested / "one.miniseed"
        expected.touch()
        (nested / "notes.txt").touch()

        assert DatasetInventory(settings).find_all_files() == [expected]
        
    def test_read_single_file_and_traces_returns_first_trace(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        stream = Stream([make_trace()])
        monkeypatch.setattr(inventory_module, "read", lambda path: stream)

        result_stream, trace = DatasetInventory(settings).read_single_file_and_traces(
            [settings.RAW_DATA_DIR / "sample.mseed"]
        )

        assert result_stream is stream
        assert trace is stream[0]
    
    def test_read_single_file_and_traces_rejects_empty_input(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            DatasetInventory(make_settings(tmp_path)).read_single_file_and_traces([])
    
    def test_inspect_file_extracts_trace_metadata(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        file_path = settings.RAW_DATA_DIR / "STA1" / "one.mseed"
        monkeypatch.setattr(
            inventory_module, "read", lambda path: Stream([make_trace()])
        )

        rows = DatasetInventory(settings).inspect_file(file_path)

        assert len(rows) == 1
        assert rows[0]["file"] == "STA1/one.mseed"
        assert rows[0]["station"] == "STA1"
        assert rows[0]["channel"] == "HHZ"
        assert rows[0]["number_of_samples"] == 100
        assert rows[0]["encoding"] == "STEIM2"

    def test_inspect_files_dataframe_combines_records(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        inventory = DatasetInventory(settings)
        monkeypatch.setattr(
            inventory,
            "inspect_file",
            lambda path: [{"file": Path(path).name, "station": "STA1"}],
        )

        result = inventory.inspect_files_dataframe([Path("a.mseed"), Path("b.mseed")])

        assert list(result["file"]) == ["a.mseed", "b.mseed"]
        assert len(result) == 2
    
    def test_inspect_station_xml_all_and_single_station(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        xml_dir = settings.RAW_DIR / "xml"
        xml_dir.mkdir()
        first = xml_dir / "XX.STA1.xml"
        second = xml_dir / "XX.STA2.xml"
        first.touch()
        second.touch()
        inventory_by_path = {first: make_inventory("STA1"), second: make_inventory("STA2")}
        monkeypatch.setattr(
            inventory_module, "read_inventory", lambda path: inventory_by_path[Path(path)]
        )
        dataset = DatasetInventory(settings)

        all_inventories = dataset.inspect_stationXML(xml_dir, all=True)
        one_inventory = dataset.inspect_stationXML(
            xml_dir, all=False, station_name="STA2"
        )

        assert all_inventories == [inventory_by_path[first], inventory_by_path[second]]
        assert one_inventory is inventory_by_path[second]
    
    def test_inspect_station_xml_missing_or_ambiguous_station(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        xml_dir = settings.RAW_DIR / "xml"
        xml_dir.mkdir()
        (xml_dir / "XX.STA1.xml").touch()
        (xml_dir / "YY.STA1.xml").touch()
        monkeypatch.setattr(inventory_module, "read_inventory", lambda path: make_inventory())
        dataset = DatasetInventory(settings)

        with pytest.raises(FileNotFoundError, match="MISSING"):
            dataset.inspect_stationXML(xml_dir, all=False, station_name="MISSING")
        with pytest.raises(ValueError, match="Multiple"):
            dataset.inspect_stationXML(xml_dir, all=False, station_name="STA1")
        with pytest.raises(ValueError, match="station_name"):
            dataset.inspect_stationXML(xml_dir, all=False)
    
    def test_inspect_station_xml_rejects_empty_folder(self, tmp_path):
        settings = make_settings(tmp_path)
        with pytest.raises(FileNotFoundError, match="No .xml files"):
            DatasetInventory(settings).inspect_stationXML(settings.RAW_DIR)
    
    def test_inspect_stations_reads_csv(self, tmp_path):
            settings = make_settings(tmp_path)
            csv_path = settings.RAW_DIR / "locations.csv"
            pd.DataFrame(
                [{"Station": "STA1", "Latitude": -38.0, "Longitude": 176.0}]
            ).to_csv(csv_path, index=False)
    
            result = DatasetInventory(settings).inspect_stations("locations.csv")
    
            assert result.loc[0, "Station"] == "STA1"
    
    def test_inspect_station_geometry_calculates_each_pair(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(
            inventory_module,
            "gps2dist_azimuth",
            lambda *coordinates: (calls.append(coordinates) or (1.0, 2.0, 3.0)),
        )
        locations = pd.DataFrame(
            [
                {"Station": "STA1", "Latitude": 1.0, "Longitude": 2.0},
                {"Station": "STA2", "Latitude": 3.0, "Longitude": 4.0},
                {"Station": "STA3", "Latitude": 5.0, "Longitude": 6.0},
            ]
        )

        DatasetInventory(make_settings(tmp_path)).inspect_station_geometry(locations)

        assert len(calls) == 3
    
    def test_build_stations_groups_files_and_metadata(self, tmp_path, monkeypatch):
        settings = make_settings(tmp_path)
        metadata = make_metadata()
        inventory = DatasetInventory(settings)
        monkeypatch.setattr(
            inventory, "inspect_files_dataframe", lambda all_files: metadata
        )
        files = [Path("first.mseed")]

        stations = inventory.build_stations(files)

        assert set(stations) == {("XX", "STA1"), ("YY", "STA2")}
        station = stations[("XX", "STA1")]
        assert len(station.metadata) == 3
        assert len(station.all_metadata) == 4
        assert len(station.files) == 3
        assert all(path.is_absolute() for path in station.files)
    
    def test_build_stations_returns_empty_mapping_for_no_records(self, tmp_path, monkeypatch):
        inventory = DatasetInventory(make_settings(tmp_path))
        monkeypatch.setattr(
            inventory,
            "inspect_files_dataframe",
            lambda all_files: pd.DataFrame(),
        )

        assert inventory.build_stations([]) == {}