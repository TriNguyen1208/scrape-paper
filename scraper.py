import arxiv
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

from utils import get_id_from_arxiv_link, display_progress, is_month_different, find_first_id, find_last_id, CLIENT, ARXIV_RATE_LIMIT

BATCH_SIZE = 200


def get_remaining_versions_of_paper(arxiv_id):
    '''
    A function to get all the versions of a paper's ID

    Parameter
    ---------
    arxiv_id: str
        newest version's ID of a paper (format: 'xxxx.xxxxxvx', x is a digit from 0 to 9)

    Return
    ------
    dict
        a dict has
            key: a ID of a paper (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
            value: a list contains remaining versions'id of a paper (xxxx.xxxxxvx, x is a digit from 0 to 9)
    '''
    number_of_version = arxiv_id.split('v')[1]
    base_paper_id = arxiv_id.split('v')[0]

    versions_id = []

    for version in range(int(number_of_version) - 1):
        versions_id.append(base_paper_id + 'v' + str(version + 1))

    return versions_id

    
def expand_to_all_versions(paper_ids:list[str]) -> list[str]:
    '''
    A function to get all the remaining versions
    
    Parameter
    ---------
    paper_ids: list of str
        A list contains papers' id (format: 'xxxx.xxxxxvx', x is a digit from 0 to 9)
    
    Return
    ------
    list of str
        A list contains papers' id (format: 'xxxx.xxxxxvx', x is a digit from 0 to 9)
    '''
    expanded = []
    for paper_id in paper_ids:
        expanded.extend(get_remaining_versions_of_paper(paper_id))
        
    return expanded
            

def crawl_id_batches(batch:list[str], retry_times:int=3) -> list[arxiv.Result]:
    '''
    A function to crawl papers' id based in batch
    
    Parameter
    ---------
    batch: list of str
        A list contains papers' id (format: 'xxxx.xxxxxvx', x is a digit from 0 to 9)
    retry_times: int
        The number of attempts to crawl
        
    Return
    ------
    list of arxiv.Result
        a list contains elements with arxiv.Result type
    '''
    for attempt in range(1, retry_times + 1):
        try:
            search = arxiv.Search(id_list=batch)
            result = (list(CLIENT.results(search)))
            break
            
        except Exception as e:
            if '429' in str(e):
                sys.stdout.write('\n')
                print(f'429: Request too many times. Attempt {attempt}')
            else:
                sys.stdout.write('\n')
                print(f"[ERROR][crawl_id_batches]: {e}")
                
            if attempt == retry_times:
                return []
            
            time.sleep(ARXIV_RATE_LIMIT)
            
    time.sleep(ARXIV_RATE_LIMIT)
    return result


def crawl_lastest_papers_multithread(start_id, end_id, batch_size, max_workers=5):
    paper_ids = []
    start_id_int = int(start_id.replace('.', ''))
    end_id_int = int(end_id.replace('.', ''))
    
    if is_month_different(start_id, end_id):
        last_id = int(find_last_id(start_id[:2], start_id[2:4]).replace('.', ''))
        first_id = int(find_first_id(end_id[:2], end_id[2:4]).replace('.', ''))
    else:
        last_id, first_id = None, None
    
    if last_id is not None and first_id is not None:
        for paper_id in range(start_id_int, last_id + 1):
            paper_id_str = str(paper_id)
            paper_ids.append(paper_id_str[:4] + '.' + paper_id_str[4:])
            
        for paper_id in range(first_id, end_id_int + 1):
            paper_id_str = str(paper_id)
            paper_ids.append(paper_id_str[:4] + '.' + paper_id_str[4:])
    else:
        for paper_id in range(start_id_int, end_id_int + 1):
            paper_id_str = str(paper_id)
            paper_ids.append(paper_id_str[:4] + '.' + paper_id_str[4:])
        
    paper_id_batches = [paper_ids[i:i + batch_size] for i in range(0, len(paper_ids), batch_size)]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(crawl_id_batches, batch) for batch in paper_id_batches]
        
        paper_list = []
        completed = 0
        
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            
            if result:
                paper_list.extend(result)
            
            display_progress(completed, len(paper_id_batches), 'Get latest versions')
            
    paper_id_list = [get_id_from_arxiv_link(paper.entry_id, with_version=True) for paper in paper_list]
            
    return paper_list, paper_id_list


def crawl_all_versions_multithread(paper_ids:list[str], batch_size:int, max_workers:int=5) -> list[arxiv.Result]:
    '''
    A function to crawl all the versions using multiple threads
    
    Parameters
    ----------
    paper_ids: list[str]
        a list contains papers' id (format: 'xxxx.xxxxxvx', x is a digit from 0 to 9)
    batch_size: int
        number of batches
    max_workers: int
        number of threads
        
    Return
    ------
    list of arxiv.Result
        a list contains elements with arxiv.Result type
    '''
    paper_id_batches = [paper_ids[i:i + batch_size] for i in range(0, len(paper_ids), batch_size)]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(crawl_id_batches, batch) for batch in paper_id_batches]
        
        paper_list = []
        completed = 0
        
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            
            if result:
                paper_list.extend(result)
            
            display_progress(completed, len(paper_id_batches), 'Get remaining versions')
            
    return paper_list

def get_all_papers(start_id:str, end_id:str, num_threads:int=5):
    '''
    A function to crawl all the papers (all version from each paper) within start_id and end_id using arxiv API

    Parameters
    ----------
    start_id: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    end_id: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)

    Returns
    ------
    list of arxiv.Result
        a list contains crawled papers
    '''
    paper_list, paper_id_list = crawl_lastest_papers_multithread(start_id, end_id, BATCH_SIZE, num_threads)

    expanded_id_list = expand_to_all_versions(paper_id_list)                           # Get all the versions of each paper

    print()

    expanded_list = crawl_all_versions_multithread(expanded_id_list, BATCH_SIZE, num_threads)

    print()
    return sorted(paper_list + expanded_list, key=lambda d: d.entry_id)