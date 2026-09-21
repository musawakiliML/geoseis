# Dataset Inventory Class
from pathlib import Path
import pandas as pd
from obspy import Stream, read, read_inventory

class DatasetInventory:
    def __init__(self, data_path:Path):
        self.data = data_path
        
    
    #TODO: Add methods for inventory management, such as filtering, summarizing, and exporting data.
    # Explore the data to understand its structure and contents.
    # Station and channel information, start and end times, sampling rates, and total samples are key attributes to consider.
    # Gaps in the data can be identified by analyzing the start and end times of each file, as well as the sampling rates and total samples.
    # Inventory information can be exported to a CSV or Excel file for further analysis or sharing with others.
    '''
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
    '''
    