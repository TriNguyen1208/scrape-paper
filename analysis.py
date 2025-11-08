import time
import psutil
import threading
from scraper import get_all_papers, START_ID, TEST_END_ID

# ========== Analysis metrics ==========
def get_total_papers(paperList):
    return {'totalPapers': len(paperList)}

def get_avg_paper_size(paperList):
    pass

def get_avg_refs_per_paper(paperList):
    pass

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
                f'totalTimeOf{fieldName}': f'{endTime - startTime:.3f}s',
                f'averageTimeOf{fieldName}': f'{(endTime - startTime) / len(paperList):.3f}s'
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
                f'highestRamUsage{fieldName}': f'{highestRamUsage / (1024 * 1024):.3f} MB',
                f'averageRamUsage{fieldName}': f'{averageRamUsage / (1024 * 1024):.3f} MB'
            }
            return result, metrics
        return wrapper
    return decorator


result, metrics = apply_time_analysis('CrawlPaper')(get_all_papers)(START_ID, TEST_END_ID)

if isinstance(result, tuple) and len(result) == 2:
    paperList, *_ = result
else:
    paperList = result
    
for i in range(5):
    print(f'{paperList[i].entry_id} - {paperList[i].title}')

for key, value in metrics.items():
    print(f'{key}: {value}')