# Dataset Inventory Class
from pathlib import Path

from configs.configs import GeoSeisSettings

# import pandas as pd
from obspy import Stream, read, read_inventory


class DatasetInventory:
    def __init__(self, settings: GeoSeisSettings):
        self.settings = settings
        self.data = settings

    def __getattr__(self, name):
        return getattr(self.settings, name)

    def get_dir_and_check(self):
        """Validate each configured directory and return the settings object."""
        path_map = {
            "PROJECT_ROOT": self.settings.PROJECT_ROOT,
            "RAW_DATA_DIR": self.settings.RAW_DATA_DIR,
            "RAW_DIR": self.settings.RAW_DIR,
        }

        validated_paths = {}
        for name, path in path_map.items():
            path = Path(path)
            print(f"Checking if {name} directory exists: {path}")

            if not path.exists():
                raise FileNotFoundError(f"{name} directory does not exist: {path}")

            for item in path.iterdir():
                print(f" - {item.name}")

            validated_paths[name] = path

        return self.settings

    def find_all_files(self, file_extension: str = ".miniseed", source_dir: Path | None = None):
        """Find all dataset files in the selected directory with the given extension."""
        if source_dir is None:
            source_dir = self.settings.RAW_DATA_DIR

        source_dir = Path(source_dir)
        dataset_files = sorted(source_dir.rglob("*" + file_extension))

        print(f"Found {len(dataset_files)} {file_extension.upper()} files in {source_dir}.")

        for path in dataset_files[:10]:
            print(path)

        return dataset_files
    
    def read_single_file_and_traces(self, file):
        """Read a single miniseed or any other data format file"""
        if not file:
            raise FileNotFoundError("File does not exist")
        
        path = file[0]
        stream = read(path)
        
        print(f"\nContents of the first MiniSeed File ({path})")
        print(stream)
        
        trace = stream[0]
        
        print(f"\nTrace Information:\n{trace}")
        print(trace.stats)
        
        return (stream, trace)
    
    def inspect_file(self, file_path: Path):
        """This Method inspects the file for contents"""
        
        stream = read(file_path)
        
        rows = []
        
        for trace in stream:
            stats = trace.stats
            
            rows.append({
                "file": str(file_path.relative_to(self.settings.RAW_DATA_DIR)),
                "network": stats.network,
                "station": stats.station,
                "channel": stats.channel,
                "starttime": stats.starttime,
                "endtime": stats.endtime,
                "sampling_rate": stats.sampling_rate,
                "number_of_samples": stats.npts,
                "duration_time": trace.stats.endtime - trace.stats.starttime,
            })
        
        return rows

    def __str__(self):
        return f"Dataset Inventory Directory: (settings={self.settings})"

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
    inventory = DatasetInventory(settings)
    validated_settings = inventory.get_dir_and_check()
    # print(validated_settings.RAW_DATA_DIR)
    # print(validated_settings.RAW_DIR)
    # print(validated_settings.PROJECT_ROOT)
    dataset_files = inventory.find_all_files(file_extension=".miniseed")
    single_file = inventory.read_single_file_and_traces(dataset_files)
    inspect = inventory.inspect_file(file_path=dataset_files[0])
    print(inspect)
    
