import arxiv
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

from utils import get_id_from_arxiv_link, display_progress, CLIENT, ARXIV_RATE_LIMIT

START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2307.00140'
BATCH_SIZE = 200

def get_daily_paper_ids(query, max_results=1000,
                  sort_by=arxiv.SortCriterion.SubmittedDate,
                  sort_order=arxiv.SortOrder.Ascending,
                  retry_times:int=3) -> list[str]:

    '''
    A function to crawl paper using arxiv API

    Parameters
    ----------
    query: str
        Ensure the query is correctly formated from arxiv API
    max_results: int
        The maximum number of results in a single query
    sort_by: arxiv.SortCriterion
        The feature to sort
    sort_order: arxiv.SortOrder
        The sort order (Ascending, Descending)
    retry_times: int
        The number of attempts to crawl

    Return
    ------
    list of str
        List of papers'id with format (xxxx.xxxxxvx, x is a digit from 0 to 9)
    ''' 
    
    for attempt in range(1, retry_times + 1):
        try:
            search = arxiv.Search(query=query,
                            max_results=max_results,
                            sort_by=sort_by,
                            sort_order=sort_order)

            
            paper_list = list(CLIENT.results(search))
            break

        except Exception as e:
            if '429' in e:
                sys.stdout.write('\n')
                print(f'429: Request too many times. Attempt {attempt}')
            else:
                sys.stdout.write('\n')
                print(f'[EXCEPTION][get_daily_paper_ids]: {e}')
                
            if attempt == retry_times:
                return []
            
            time.sleep(ARXIV_RATE_LIMIT)

    time.sleep(ARXIV_RATE_LIMIT)

    return [get_id_from_arxiv_link(paper.entry_id, with_version=True) for paper in paper_list]


def filter_papers_in_id_range(paper_id_list, start_id=None, end_id=None):
    '''
    A function to filter the list of papers in a given date range

    Parameters
    ----------
    paper_id_list: list of str
        a list of papers' id to filter with format (xxxx.xxxxxvx, x is a digit from 0 to 9)
    start_id: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    end_id: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)

    Return
    ------
    list of str
        a list contains filtered papers'id with format (xxxx.xxxxxvx, x is a digit from 0 to 9)
    '''
    if start_id is None:
        return [paper for paper in paper_id_list if get_id_from_arxiv_link(paper, with_version=False) <= end_id]
    
    if end_id is None:
        return [paper for paper in paper_id_list if start_id <= get_id_from_arxiv_link(paper, with_version=False)]

    return [paper for paper in paper_id_list if start_id <= get_id_from_arxiv_link(paper, with_version=False) <= end_id]


def get_date_range_from_id(start_id, end_id, retry_times:int=3):
    '''
    A function to detect start date and end date from ids

    Parameters
    ----------
    start_id: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    end_id: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    retry_times: int
        The number of attempts to crawl
    
    Return
    ------
    tuple of datetime.datetime (format: '%Y-%m-%d %H:%M:%S)
        a tuple with start date and end date
    '''
    for attempt in range(1, retry_times + 1):
        try:
            search = arxiv.Search(id_list=[start_id, end_id])
            paper_list = list(CLIENT.results(search))
            break
            
        except Exception as e:
            if '429' in e:
                sys.stdout.write('\n')
                print(f'429: Request too many times. Attempt {attempt}')
            else:
                sys.stdout.write('\n')
                print(f'[EXCEPTION][get_date_range_from_id]: {e}')
                
            if attempt == retry_times:
                return []
            
            time.sleep(ARXIV_RATE_LIMIT)
    
    return(paper_list[0].published, paper_list[1].published)


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

def generate_date_range(start_date, end_date):
    date = []
    for n in range((end_date - start_date).days + 1):
        date.append(start_date + timedelta(n))
        
    return date
    
def crawl_daily_papers(date):
    fmt_date = date.strftime('%Y%m%d')
    query = f'all AND submittedDate:[{fmt_date}0000 TO {fmt_date}2359]'

    daily_paper_ids = get_daily_paper_ids(query=query)
    
    return daily_paper_ids


def crawl_all_daily_papers_multithread(start_date, end_date, max_workers=5):
    paper_ids = []
    total_days = (end_date - start_date).days + 1
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(crawl_daily_papers, date) for date in generate_date_range(start_date, end_date)]
        
        completed = 0
        
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            
            if result:
                paper_ids.extend(result)
                
            display_progress(completed, total_days, "Get daily papers")
        
    return sorted(paper_ids)
    
    
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
        
    return paper_ids + expanded
            

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
            if '429' in e:
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
            
    return sorted(paper_list, key=lambda d: d.entry_id)

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
    print('Get range')
    (start_date, end_date) = get_date_range_from_id(start_id, end_id)
    
    paper_id_list = crawl_all_daily_papers_multithread(start_date, end_date, num_threads)        # Get all daily papers within date range

    paper_id_list = filter_papers_in_id_range(paper_id_list, start_id, end_id)      # Filter papers to ensure within id range

    paper_id_list = expand_to_all_versions(paper_id_list)                           # Get all the versions of each paper

    print()

    paper_list = crawl_all_versions_multithread(paper_id_list, BATCH_SIZE, num_threads)

    print()
    return paper_list



# def test_func():
#     start_time = time.time()
    
#     paper_list = get_all_papers(START_ID, TEST_END_ID)
    
#     end_time = time.time()
#     print()
    
#     print(f'Duration: {(end_time - start_time):.2f}s')
#     print(f'Number of papers: {len(paper_list)}')
    
#     # Print for checking
#     for i in range(5):
#         print(f'{paper_list[i].entry_id} - {paper_list[i].title}')
    
    
    
# test_func()