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

# Create Temporary directory for testing
def make_settings(tmp_path: Path) -> GeoSeisSettings:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(exist_ok=True)
    return GeoSeisSettings(
        PROJECT_ROOT=tmp_path,
        RAW_DATA_DIR=raw_dir,
        RAW_DIR=raw_dir,
    )