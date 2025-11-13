from utils import display_progress
from extract_data import extract_metadata, extract_reference
from saving import save_one_tex, save_one_metadata, save_one_reference

from config import NUM_DOWNLOAD_THREADS, NUM_EXTRACT_THREADS, NUM_SAVE_THREADS
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import sys

q_extract = Queue()
q_download = Queue()
q_save = Queue()

progress_lock = threading.Lock()
paper_size_update_lock = threading.Lock()
completed = 0
total = 0
            
def downloading_worker(paper_sizes):
    while True:
        paper_dict = q_download.get()
        
        if paper_dict is None:            
            q_download.task_done()
            break
        
        
        try:
            paper_id = paper_dict['id']
            versions = paper_dict['versions']
            
            for paper_version in versions:
                size = save_one_tex(paper=paper_version, report_size=True)
                
                with paper_size_update_lock:
                    paper_sizes.append(size)
            
            q_extract.put((paper_id, versions))
        except Exception as e:
            sys.stdout.write('\n')
            print(f'[EXCEPTION][downloading_worker]: {e}')
            
        finally:     
            q_download.task_done()
        
def extracting_worker():
    while True:
        item = q_extract.get()
        
        if item is None:                
            q_extract.task_done()
            break
        
        paper_id, versions = item
        
        try:
            meta_data_paper = extract_metadata(paper_id, versions)
            
        except Exception as e:
            meta_data_paper = None
            sys.stdout.write('\n')
            print(f'Cannot get metadata of {paper_id}')
        
        
        try:
            meta_data_reference = extract_reference(paper_id)
            
            if meta_data_reference == {}:
                meta_data_reference = None
                sys.stdout.write('\n')
                print(f'Cannot get refs of {paper_id}')
                
        except Exception as e:
            meta_data_reference = None
            sys.stdout.write('\n')
            print(f'Unexpected error during reference extraction for {paper_id}: {type(e).__name__} - {e}')
                
        q_save.put((paper_id, meta_data_paper, meta_data_reference))
        q_extract.task_done()
            
def saving_worker():
    global completed
    while True:
        item = q_save.get()
        
        if item is None:
            
            q_save.task_done()
            break
        
        paper_id, meta_data_paper, meta_data_reference = item
        
        try:
            if meta_data_paper is not None:
                save_one_metadata(id=paper_id, metadata=meta_data_paper)
                
            if meta_data_reference is not None:
                save_one_reference(id=paper_id, reference=meta_data_reference)
        except Exception as e:
            sys.stdout.write('\n')
            print(f'[EXCEPTION][saving_worker]: {e}')
            
        finally:
            with progress_lock:
                try:
                    completed += 1
                    display_progress(completed, total, "Processing papers")
                except Exception as e:
                    sys.stdout.write('\n')
                    print(f'[EXCEPTION][progress_lock][saving_worker]: {e}')

            q_save.task_done()
    
            
def execute_pipeline(paper_dict_list):
    global total, completed
    total = len(paper_dict_list)
    completed = 0
    paper_sizes = []
    
    for paper_dict in paper_dict_list:
        q_download.put(paper_dict)
        
    with ThreadPoolExecutor(max_workers=NUM_DOWNLOAD_THREADS + NUM_EXTRACT_THREADS + NUM_SAVE_THREADS) as executor:
        for _ in range(NUM_DOWNLOAD_THREADS):
            executor.submit(downloading_worker, paper_sizes)
            
        for _ in range(NUM_EXTRACT_THREADS):
            executor.submit(extracting_worker)
            
        for _ in range(NUM_SAVE_THREADS):
            executor.submit(saving_worker)
            
            
            
        for _ in range(NUM_DOWNLOAD_THREADS):
            q_download.put(None)
        q_download.join()        
        
        for _ in range(NUM_EXTRACT_THREADS):
            q_extract.put(None)
        q_extract.join()
        
        for _ in range(NUM_SAVE_THREADS):
            q_save.put(None)
        q_save.join()
        
    return paper_sizes