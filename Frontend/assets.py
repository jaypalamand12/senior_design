from dataclasses import dataclass

@dataclass
class Assets:
    hightemp: str = "Frontend/assets/hightemp.png"
    lowhealth: str = "Frontend/assets/basicalert.png"
    connectivity: str = "Frontend/assets/connectivity.png"
    file_path: str = "/Users/jaypalamand/Senior_Design/csv_data/"