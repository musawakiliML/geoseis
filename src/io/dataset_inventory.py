# Dataset Inventory Class
from pathlib import Path

from configs.configs import GeoSeisSettings

# import pandas as pd
# from obspy import Stream, read, read_inventory


class DatasetInventory:
    def __init__(self, data_path: Path):
        self.data = data_path

    def get_dir_and_check(self):
        """Get the directory of the dataset."""
        data_dir = Path(self.data)
        print(f"Checking if directory {data_dir} exists...")

        if not data_dir.exists():
            raise FileNotFoundError(f"Directory {data_dir} does not exist.")

        for item in data_dir.iterdir():
            print(f" - {item.name}")

        return data_dir

    def __str__(self):
        return f"Dataset Inventory Directory: (data={self.data})"

    # TODO: Add methods for inventory management, such as filtering, summarizing, and exporting data.
    # Explore the data to understand its structure and contents.
    # Station and channel information, start and end times, sampling rates, and total samples are key attributes to consider.
    # Gaps in the data can be identified by analyzing the start and end times of each file, as well as the sampling rates and total samples.
    # Inventory information can be exported to a CSV or Excel file for further analysis or sharing with others.
    """
                ├── Files ✓
                 ├── Stations ✓
                 ├── Channels ✓
                 ├── Sampling rates ✓
                 ├── Spatial metadata ✓
                 ├── Physical units ✓
                 ├── Instrument response ✓
                 ├── Recording windows ✓
                 ├── Gaps/overlaps ✓
                 └── Common window ✓
    """


if __name__ == "__main__":
    settings = GeoSeisSettings()
    test = DatasetInventory(settings.RAW_DATA_DIR)
    print(test.get_dir_and_check())
