# Dataset Inventory Class
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from obspy import Stream, read, read_inventory
from obspy.geodetics import gps2dist_azimuth

from configs.configs import GeoSeisSettings, logging


@dataclass
class StationData:
    network: str
    code: str
    files: list[Path]
    metadata: pd.DataFrame
    all_metadata: pd.DataFrame
    settings: GeoSeisSettings

    def get_size(self) -> pd.Series:
        """Return trace-record counts per station and channel. For Single Station

        Returns:
            pd.Series: _description_
        """
        return self.metadata.groupby(["station", "channel"]).size()

    def get_aggregate(self) -> pd.DataFrame:
        """Summarize file records, time bounds, rates, and samples by channel. For Single Station

        Returns:
            pd.DataFrame: _description_
        """

        return self.metadata.groupby(["station", "channel"]).agg(
            files=("file", "count"),
            start=("starttime", "min"),
            end=("endtime", "max"),
            sampling_rate=("sampling_rate", "unique"),
            total_samples=("number_of_samples", "sum"),
        )

    def get_coverage(self) -> pd.DataFrame:
        """Return start/end bounds and record counts by station and channel. For Single Station


        Returns:
            pd.DataFrame: _description_
        """
        return (
            self.metadata.groupby(["station", "channel"])
            .agg(
                start=("starttime", "min"),
                end=("endtime", "max"),
                files=("file", "count"),
            )
            .reset_index()
        )

    def get_stations_size(self) -> pd.DataFrame | pd.Series:
        """Get All stations Sizes by channels

        Returns:
            pd.DataFrame | pd.Series: _description_
        """
        return self.all_metadata.groupby(["station", "channel"]).size()

    def get_stations_aggregate(self) -> pd.DataFrame | pd.Series:
        """Get All Stations Aggregate based on channels

        Returns:
            pd.DataFrame | pd.Series: _description_
        """
        return self.all_metadata.groupby(["station", "channel"]).agg(
            files=("file", "count"),
            start=("starttime", "min"),
            end=("endtime", "max"),
            sampling_rate=("sampling_rate", "unique"),
            total_sanples=("number_of_samples", "sum"),
        )

    def get_stations_coverage(self) -> pd.DataFrame | pd.Series:
        """Get Station Coverage by channels

        Returns:
            pd.DataFrame | pd.Series: _description_
        """
        coverage = (
            self.all_metadata.groupby(["station", "channel"])
            .agg(
                starts=("starttime", "min"),
                end=("endtime", "max"),
                files=("file", "count"),
            )
            .reset_index()
        )
        return coverage

    def check_gaps(self):
        """This fucntions checks the gaps available in the traces records
        Gaps in the data can be identified by analyzing the start and end times of each file,
        as well as the sampling rates and total samples.

        Raises:
            FileNotFoundError: _description_
            FileNotFoundError: _description_

        Returns:
            _type_: _description_
        """

        # Check Gaps

        for station in sorted(self.all_metadata["station"].unique()):
            for channel in sorted(self.all_metadata["channel"].unique()):

                files = sorted(
                    self.all_metadata[
                        (self.all_metadata["station"] == station)
                        & (self.all_metadata["channel"] == channel)
                    ]["file"]
                )

                if not files:
                    continue

                stream = Stream()
                
                for file in files:
                    stream += read(self.settings.RAW_DATA_DIR / file)
                
                logging.info(f"\n{station} {channel}")
                logging.info(stream)
                logging.info(f"Gaps: {len(stream.get_gaps())}")
    
    @dataclass
    class ChannelData:
        inventory: Any
        
        def get_channel_info(self) -> pd.DataFrame | pd.Series:
            
            channels_info = []
            
            for network in self.inventory:
                for station in network:
                    for channel in station:
                        logging.info(
                            channel.code,
                            "sample_rate =", channel.sample_rate,
                            "latitude =", channel.latitude,
                            "longitude =", channel.longitude,
                            "elevation =", channel.elevation,
                            "depth =", channel.depth,
                            "azimuth =", channel.azimuth,
                            "dip =", channel.dip,
                        )
                        channel_data = {
                            "channel_code": channel.code,
                            "sample_rate": channel.sample_rate,
                            "latitude": channel.latitude,
                            "longitude": channel.longitude,
                            "elevation": channel.elevation,
                            "depth": channel.depth,
                            "azimuth": channel.azimuth,
                            "dip": channel.dip
                        }
                    
                    channels_info.append(channel_data)
                    
            channels_df = pd.DataFrame(channels_info)
            
            return channels_df

        def get_channel_response(self):
            pass
    
class DatasetInventory:
    def __init__(self, settings: GeoSeisSettings):
        self.settings = settings
        self.data = settings

    def __getattr__(self, name):
        return getattr(self.settings, name)

    def get_dir_and_check(self):
        """Validate each configured directory and return the settings object.

        Raises:
            FileNotFoundError: _description_

        Returns:
            object: Geosettings object
        """
        
        path_map = {
            "PROJECT_ROOT": self.settings.PROJECT_ROOT,
            "RAW_DATA_DIR": self.settings.RAW_DATA_DIR,
            "RAW_DIR": self.settings.RAW_DIR,
        }

        validated_paths = {}
        for name, path in path_map.items():
            path = Path(path)

            logging.info(f"Checking if {name} directory exists: {path}")

            if not path.exists():
                raise FileNotFoundError(f"{name} directory does not exist: {path}")

            for item in path.iterdir():
                logging.info(f" - {item.name}")

            validated_paths[name] = path

        return self.settings

    def find_all_files(
        self, file_extension: str = ".miniseed", source_dir: Path | None = None
    ) -> list[Path]:
        """Find all dataset files in the selected directory with the given extension.

        Args:
            file_extension (str, optional): _description_. Defaults to ".miniseed".
            source_dir (Path | None, optional): _description_. Defaults to None.

        Returns:
            list[Path]: List of Path
        """
        
        
        if source_dir is None:
            source_dir = self.settings.RAW_DATA_DIR

        source_dir = Path(source_dir)
        dataset_files = sorted(source_dir.rglob("*" + file_extension))

        logging.info(
            f"Found {len(dataset_files)} {file_extension.upper()} files in {source_dir}."
        )

        for path in dataset_files[:10]:
            logging.info(path)

        return dataset_files

    def read_single_file_and_traces(self, file) -> tuple:
        """Read a single miniseed or any other data format file

        Args:
            file (_type_): mseed files

        Raises:
            FileNotFoundError: mseed files

        Returns:
            tuple: stream, trace
        """
        
        if not file:
            raise FileNotFoundError("File does not exist")

        path = file[0]
        stream = read(path)

        logging.info(f"\nContents of the first MiniSeed File ({path})")
        logging.info(stream)

        trace = stream[0]

        logging.info(f"\nTrace Information:\n{trace}")
        logging.info(trace.stats)

        return (stream, trace)

    def inspect_file(self, file_path: Path) -> list:
        """This Method inspects the file for contents
        Explore the data to understand its structure and contents.
        Station and channel information, start and end times, sampling rates,
        and total samples are key attributes to consider.

        Args:
            file_path (Path): _description_

        Returns:
            list: List of files with information
        """

        stream = read(file_path)

        rows = []

        for trace in stream:
            stats = trace.stats

            rows.append(
                {
                    "file": str(file_path.relative_to(self.settings.RAW_DATA_DIR)),
                    "network": stats.network,
                    "station": stats.station,
                    "channel": stats.channel,
                    "starttime": stats.starttime,
                    "endtime": stats.endtime,
                    "sampling_rate": stats.sampling_rate,
                    "number_of_samples": stats.npts,
                    "duration_time": trace.stats.endtime - trace.stats.starttime,
                    "encoding": getattr(stats.mseed, "encoding", None),
                }
            )

        return rows

    def inspect_files_dataframe(self, all_files):
        """Inspect all files and generate a dataframe for inspection

        Args:
            all_files (_type_): all mseed files

        Return: dataframe
        """

        records = []

        for path in all_files:
            records.extend(self.inspect_file(path))

        inventory_df = pd.DataFrame(records)

        return inventory_df

    def inspect_stationXML(
        self, folder_path: Path, extension=".xml", all: bool = True | False, station_name = None
    ):
        """Inspect The StationXML file for extra information about the equipment, networks, channels, response etc..

        Args:
            file_path (Path): File path

        Return
        """

        # Check if file exists
        if not folder_path:
            folder_path = self.settings.RAW_DIR
            folder_path = Path(folder_path)

        xml_files = sorted(folder_path.rglob("*" + extension))

        if not xml_files:
            raise FileNotFoundError(f"No {extension} files found in {folder_path}")

        logging.info(
            f"Found {len(xml_files)} {extension.upper()} files in {folder_path}."
        )
        
        station_filenames = [xml_file.name for xml_file in xml_files]
        logging.info("StationXML filenames: %s", station_filenames)

        records_stationXML = []

        if all:
            
            for item in range(len(xml_files)):
                inventory = read_inventory(xml_files[item])

                logging.info(
                    f"Inventory Details For StationXML File {xml_files[item]!s}"
                )
                logging.info(inventory)

                records_stationXML.append(inventory)

            return records_stationXML
        
        elif not all:
            if not station_name:
                raise ValueError("station_name is required when all=False eg. station_name='LKG01'")

            matching_files = [
                xml_file
                for xml_file in xml_files
                if station_name in xml_file.stem.split(".")
            ]
            if not matching_files:
                raise FileNotFoundError(
                    f"No StationXML file found for station {station_name!r}"
                )
            if len(matching_files) > 1:
                raise ValueError(
                    f"Multiple StationXML files found for station {station_name!r}: "
                    f"{matching_files}"
                )

            station_xml_path = matching_files[0]
            inventory = read_inventory(station_xml_path)
            logging.info("Returning StationXML inventory from %s", station_xml_path)
            
            return inventory

    def inspect_stations(self, file_name: str):
        """Inspect The station locations provided if available

        Args:
            file_path (Path): station locations
        """

        locations = pd.read_csv(self.settings.RAW_DIR / file_name)

        logging.info("The Locations of the available stations")
        logging.info(locations)

        return locations

    def inspect_station_geometry(self, locations: pd.DataFrame):
        """This method calculates the station geometry

        Args:
            locations (pd.DataFrame): Locations with lat, long and elevation

        Return: distances
        """
        stations = {}

        for i in range(len(locations)):
            stations[locations.get("Station")[i]] = (
                locations.get("Latitude")[i],
                locations.get("Longitude")[i],
            )

        for station_a, coords_a in stations.items():
            for station_b, coords_b in stations.items():
                if station_a >= station_b:
                    continue
                distance_m, azimuth, back_azimuth = gps2dist_azimuth(
                    coords_a[0], coords_a[1], coords_b[0], coords_b[1]
                )
                logging.info(
                    f"Distance between {station_a} and {station_b}: {distance_m:.2f} meters, Azimuth: {azimuth:.2f} degrees, Back Azimuth: {back_azimuth:.2f} degrees"
                )

    def build_stations(
        self, all_files: list[Path] | None = None
    ) -> dict[tuple[str, str], StationData]:
        """_summary_

        Args:
            all_files (list[Path] | None, optional): _description_. Defaults to None.

        Returns:
            dict[tuple[str, str], StationData]: _description_
        """
        if all_files is None:
            all_files = self.find_all_files()

        metadata = self.inspect_files_dataframe(all_files)
        stations = {}
        
        # xml_metadata = self.inspect_stationXML()

        if metadata.empty:
            return stations

        for (network, code), rows in metadata.groupby(["network", "station"]):
            files = sorted(
                {
                    self.settings.RAW_DATA_DIR / Path(relative_path)
                    for relative_path in rows["file"]
                }
            )
            key = (network, code)
            stations[key] = StationData(
                network=network,
                code=code,
                files=files,
                metadata=rows.copy(),
                all_metadata=metadata,
                settings = self.settings
            )
            logging.info(f"Rows: {rows}")

        return stations

    def __str__(self):
        return f"Dataset Inventory Directory: (settings={self.settings})"


if __name__ == "__main__":
    settings = GeoSeisSettings()
    inventory = DatasetInventory(settings)
    # validated_settings = inventory.get_dir_and_check()
    # print(validated_settings.RAW_DATA_DIR)
    # print(validated_settings.RAW_DIR)
    # print(validated_settings.PROJECT_ROOT)
    # dataset_files = inventory.find_all_files(file_extension=".miniseed")
    # single_file = inventory.read_single_file_and_traces(dataset_files)
    # inspect = inventory.inspect_file(file_path=dataset_files[0])
    # print(inspect)
    stationxml = inventory.inspect_stationXML(folder_path=settings.RAW_DIR, all=False, station_name="LKG01")
    print(stationxml.get_contents())

    # stations = inventory.inspect_stations(file_name="stat_locations.csv")
    # stations_geo = inventory.inspect_station_geometry(locations=stations)

    # all_stations = inventory.build_stations()
    # logging.info(all_stations)
