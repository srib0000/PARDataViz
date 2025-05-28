# A scanset is a grouping of scans into an object backed by a file (also called 
# a scanset) which represents a collection of scans. Scans are a collection of 
# files which contain the data for the volumes in the scan.
from pathlib import Path
from scan import Scan
import json

# {
#   "scanset_name": "value",
#   "base_dir": "common_ancestor_dir",
#   "scans": [
#       {
#           "scan_name": "value",
#           "rel_dir": "relative_path_to_base_dir",
#           "scan_files": [
#               "filename1",
#               "filename2",
#               ...
#           ]
#       },
#       {
#           ...
#       },
#   ]
# }

class ScanSet(object):
    def __init__(self, name: str, base_dir: Path | str | None):
        self.name = name
        self.base_dir = base_dir.__str__()
        self.scans = []

    def get_name(self) -> str:
        return self.name
    
    def set_name(self, name: str) -> None:
        self.name = name
    
    def get_base_dir(self) -> Path:
        return Path(self.base_dir)
    
    def set_base_dir(self, base_dir: Path) -> None:
        self.base_dir = base_dir.__str__()

    def get_scans(self) -> list[Scan]:
        return self.scans
    
    def add_scan(self, scan: Scan):
        self.scans.append(scan)

    def remove_scan(self, scan: Scan):
        self.scans.remove(scan)

    @staticmethod
    def load_scanset(scanset_path: Path):
        with scanset_path.open("r") as scanset_file:
            scanset_json = json.load(scanset_file)
            scanset = ScanSet(scanset_json["name"], scanset_json["base_dir"])

            for scan_json in scanset_json["scans"]:
                scanset.add_scan(Scan(**scan_json))

            # print(scanset.get_scans())
            return scanset

    @staticmethod
    def dump_scanset(scanset_path: Path, scanset):
        with scanset_path.open("w") as scanset_file:
            json.dump(vars(scanset), scanset_file, default=Scan.serialize_scan, indent=4)

def main():
    scanset = ScanSet("Horus-NOAA 2024-May-06 WX Event", Path("D:\\cs5093\\20240506"))
    scan = Scan("Scan 10", Path("scan_10\\MATLAB"))
    scanset.add_scan(scan)
    print(f'Scanset Name: {scanset.get_name()}')
    print(f'Scanset Base Dir: {scanset.get_base_dir()}')
    print(f'Scan Name: {scanset.get_scans()[0].get_name()}')
    print(f'Scan Rel Dir: {scanset.get_scans()[0].get_rel_dir()}')
    print(f'{Path(scanset.get_base_dir(), scanset.get_scans()[0].get_rel_dir())}')

if __name__ == '__main__':
    main()
