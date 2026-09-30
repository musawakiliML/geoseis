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
    
    