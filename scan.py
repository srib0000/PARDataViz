from pathlib import Path

class Scan(object):
    # def __init__(self, scan_name: str, rel_dir: Path) -> None:
    def __init__(self, name: str, scan_files: list[str] = None) -> None:
        self.name = name
        # self.rel_dir = rel_dir
        self.scan_files = scan_files if scan_files is not None else []
    
    def get_name(self) -> str:
        return self.name
    
    def set_name(self, name: str) -> None:
        self.name = name
    
    # def get_rel_dir(self) -> Path:
    #     return self.rel_dir

    def get_scan_files(self) -> list[str]:
        return self.scan_files
    
    @staticmethod
    def serialize_scan(obj):
        if isinstance(obj, Scan):
            return vars(obj)