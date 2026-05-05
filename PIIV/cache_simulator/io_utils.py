from typing import List, Dict
import csv

def save_trace_csv(trace: List[Dict[str, int]], filename: str) -> None:
    fieldnames = sorted({k for item in trace for k in item.keys()})
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trace)
        
def load_trace_csv(filename: str) -> List[Dict[str, int]]:
    trace: List[Dict[str, int]] = []
    with open(filename, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item: Dict[str, int] = {}
            if "address" not in row or row["address"] == "":
                raise ValueError("O CSV precisa ter a coluna 'address'.")
            item["address"] = int(row["address"])
            if "pc" in row and row["pc"] not in (None, ""):
                item["pc"] = int(row["pc"])
            trace.append(item)
    return trace