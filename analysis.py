import time
import psutil
import threading
import os
# ========== Analysis metrics ==========
def get_total_papers(paperList):
    return {'totalPapers': len(paperList)}

# ========== Measurement ==========
def measure_RAM_usage(memoryProcess, ramTrackingList, stopProcessFlag, interval=1):
    while not stopProcessFlag.is_set():
        ramTrackingList.append(memoryProcess.memory_info().rss)
        time.sleep(interval)


# Decorator functions
def apply_time_analysis(fieldName):
    def decorator(func):
        def wrapper(*args, **kwargs):
            startTime = time.time()
            
            result = func(*args, **kwargs)
            
            endTime = time.time()
            
            if isinstance(result, tuple) and (len(result) >= 2):
                paperList, *_ = result
            else:
                paperList = result
            
            metrics = {
                f'TotalTimeOf{fieldName}': f'{endTime - startTime:.3f}s',
                f'AverageTimeOf{fieldName}': f'{(endTime - startTime) / len(paperList):.3f}s'
            }
            
            return result, metrics
        return wrapper
    return decorator

def apply_RAM_analysis(fieldName):
    def decorator(func):
        def wrapper(*args, **kwargs):
            memoryProcess = psutil.Process()
            ramTrackList = []
            stopProcessFlag = threading.Event()
            
            ramThread = threading.Thread(target=measure_RAM_usage, args=(memoryProcess, ramTrackList, stopProcessFlag,))
            ramThread.start()
            
            result = func(*args, **kwargs)
            
            stopProcessFlag.set()
            ramThread.join()
            
            # Calculate the ram usage
            highestRamUsage = max(ramTrackList) if ramTrackList else 0
            averageRamUsage = (sum(ramTrackList) / len(ramTrackList)) if ramTrackList else 0
            
            metrics = {
                f'HighestRamUsage{fieldName}': f'{highestRamUsage / (1024 * 1024):.3f} MB',
                f'AverageRamUsage{fieldName}': f'{averageRamUsage / (1024 * 1024):.3f} MB'
            }
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


def apply_disk_analysis(field_name, folder_path='.'):
    def decorator(func):
        def wrapper(*arg, **kwargs):
            storage_track_list = []
            stop_progress_flag = threading.Event()

            disk_thread = threading.Thread(
                target=measure_disk_usage,
                args=(folder_path, storage_track_list, stop_progress_flag)
            )

            disk_thread.start()

            result = func(*arg, **kwargs)

            stop_progress_flag.set()
            disk_thread.join()

            highest_disk_storage = max(storage_track_list) if storage_track_list else 0
            final_disk_storage = storage_track_list[-1] if storage_track_list else 0

            metrics = {
                f'HighestDiskUsage {field_name}': f'{highest_disk_storage / (1024 * 1024):.3f} MB',
                f'FinalDiskUsage {field_name}': f'{final_disk_storage / (1024 * 1024):.3f} MB'
            }
            return result, metrics
        return wrapper
    return decorator