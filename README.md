# GeoSeis

A Python package for exploring seismic waveform datasets and their station metadata. GeoSeis can discover MiniSEED files, summarize waveform records by station and channel, inspect StationXML metadata, and calculate station geometry.

## Installation

Install the published package with pip:

```bash
python -m pip install geoseis
```

To work from a source checkout, install the development dependencies too:

```bash
poetry install --with dev
poetry run pytest
```

The `dev` group contains pytest and Twine. These tools are used to test and publish GeoSeis; they are not required to use the package.

## Configure Data Paths

GeoSeis reads paths from `GEOSEIS_`-prefixed environment variables or a `.env` file in the current working directory. Environment variables take precedence. Copy the example file and update its values for your machine:

```bash
cp .env.example .env
```

Set the paths in `.env`:

```dotenv
GEOSEIS_PROJECT_ROOT=/absolute/path/to/your/project
GEOSEIS_RAW_DATA_DIR=/absolute/path/to/your/miniseed/data
GEOSEIS_RAW_DIR=/absolute/path/to/your/raw/metadata
```

The local `.env` file is ignored by Git. You can also define these variables in your shell or deployment environment instead. The settings values are `pathlib.Path` objects.

## Quick Start

```python
from geoseis.configs.configs import GeoSeisSettings
from geoseis.io.dataset_inventory import DatasetInventory

settings = GeoSeisSettings()
inventory = DatasetInventory(settings)

waveform_files = inventory.find_all_files()
stations = inventory.build_stations(waveform_files)
channels = inventory.build_channels()
channel_metadata = channels.get_info()

station = stations[("LK", "LKG01")]
channel_summary = station.get_aggregate()
channel_coverage = station.get_coverage()
```

`build_stations()` returns a mapping keyed by `(network_code, station_code)`. Each `StationData` provides summaries for its waveform records. `build_channels()` reads the configured StationXML files; `get_info()` returns their channel metadata as a pandas DataFrame.

## Development

Run the test suite from the repository root:

```bash
poetry run pytest
```
