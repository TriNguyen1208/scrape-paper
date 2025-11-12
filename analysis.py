import time
import psutil
import threading
import os
import json
from utils import convert_second_to_format
# ========== Analysis metrics ==========
def get_total_papers(paperList):
    return {'totalPapers': len(paperList)}

# ========== Measurement ==========
def measure_RAM_usage(memoryProcess, ramTrackingList, stopProcessFlag, interval=1):
    while not stopProcessFlag.is_set():
        ramTrackingList.append(memoryProcess.memory_info().rss)
        time.sleep(interval)


# Decorator functions
def apply_analysis(fieldName, folder_path='.'):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # RAM tracking
            memoryProcess = psutil.Process()
            ramTrackList = []
            stopRAMFlag = threading.Event()
            ramThread = threading.Thread(target=measure_RAM_usage, args=(memoryProcess, ramTrackList, stopRAMFlag,))
            ramThread.start()

            # Disk tracking
            storage_track_list = []
            stopDiskFlag = threading.Event()
            disk_thread = threading.Thread(target=measure_disk_usage, args=(folder_path, storage_track_list, stopDiskFlag))
            disk_thread.start()

            # Time tracking
            startTime = time.time()
            result = func(*args, **kwargs)
            endTime = time.time()

            # Stop threads
            stopRAMFlag.set()
            ramThread.join()
            stopDiskFlag.set()
            disk_thread.join()

            # RAM metrics
            highestRamUsage = max(ramTrackList) if ramTrackList else 0
            averageRamUsage = (sum(ramTrackList) / len(ramTrackList)) if ramTrackList else 0
            metrics_ram = {
                f'Highest_Ram_Usage_{fieldName}': f'{highestRamUsage / (1024 * 1024):.3f} MB',
                f'Average_Ram_Usage{fieldName}': f'{averageRamUsage / (1024 * 1024):.3f} MB'
            }

            # Disk metrics
            highest_disk_storage = max(storage_track_list) if storage_track_list else 0
            final_disk_storage = storage_track_list[-1] if storage_track_list else 0
            metrics_disk = {
                f'Highest_Disk_Usage_{fieldName}': f'{highest_disk_storage / (1024 * 1024):.3f} MB',
                f'Final_Disk_Usage_{fieldName}': f'{final_disk_storage / (1024 * 1024):.3f} MB'
            }

            # Time metrics
            if isinstance(result, (list, tuple)) and len(result) > 0:
                try:
                    avg_time = (endTime - startTime) / len(result)
                except TypeError:
                    avg_time = endTime - startTime
            else:
                avg_time = endTime - startTime

            metrics_time = {
                f'Total_Time_Of_{fieldName}': convert_second_to_format(endTime - startTime),
                f'Average_Time_Of_{fieldName}': convert_second_to_format(endTime - startTime)
            }

            # Combine all metrics
            metrics = {**metrics_ram, **metrics_time, **metrics_disk}
            return result, metrics
        return wrapper
    return decorator

def get_dir_size(path="."):
    total_size = 0
    for dirpath, _, file_names in os.walk(path):
        for f in file_names:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size

def measure_disk_usage(
    folder_path,
    storage_track_list, 
    stop_progress_flag, 
    interval=1
):
    while not stop_progress_flag.is_set():
        size = get_dir_size(folder_path)
        storage_track_list.append(size)
        time.sleep(interval)

def analysis_reference(dirname="./23127072"):
    count_reference = 0
    count_reference_per_paper = []
    total_paper = 0
    absolute_dir_name = os.path.dirname(os.path.abspath(__file__))
    dirname = os.path.join(absolute_dir_name, dirname)

    for folder in os.listdir(dirname):
        folder_name = os.path.join(dirname, folder)
        total_paper += 1
        if "references.json" in os.listdir(folder_name):
            count_reference += 1
            file_ref_name = os.path.join(folder_name, "references.json")
            
            with open(file_ref_name, encoding='utf-8') as f:
                references = json.load(f)
                count_ref = 0
                for _ in references.items():
                    count_ref += 1
                count_reference_per_paper.append(count_ref)

    if total_paper == 0:
        rate_success = 0
    else:
        rate_success = count_reference / total_paper
    if len(count_reference_per_paper) == 0:
        count_reference_per_paper_average = 0
    else:
        count_reference_per_paper_average = sum(count_reference_per_paper) // len(count_reference_per_paper)
    return rate_success, count_reference_per_paper_average
