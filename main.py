from scraper import get_all_papers
from utils import convert_paper_list_to_dictionary, save_dict_to_json
from analysis import apply_disk_analysis, apply_time_analysis, apply_RAM_analysis
from thread_process import execute_pipeline

import time

START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2307.00140'
NUM_THREADS = 1

# def execute_paper(paper_dict: dict) -> dict:
#     paper_id = paper_dict['id']
#     versions = paper_dict['versions']

#     meta_data_paper = extract_metadata(paper_id, versions)
#     meta_data_reference = extract_reference(paper_id)

#     paper_sizes = {}
#     for paper_version in versions:
#         size = save_one_tex(paper_version, report_size=True)
#         paper_sizes.update(size)

#     save_one_metadata(id=paper_id, metadata=meta_data_paper)
#     save_one_reference(id=paper_id, reference=meta_data_reference)

#     time.sleep(RATE_LIMIT)
#     return paper_sizes

# def execute_paper_multithread(paper_dict_list, max_workers:int=5):
#     total = len(paper_dict_list[:5])
#     completed = 0
#     paper_size = {}
    
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = [executor.submit(execute_paper, paper) for paper in paper_dict_list[:5]]
        
#         for future in as_completed(futures):
#             result = future.result()
#             paper_size.update(result)
#             completed += 1
#             display_progress(completed, total, 'Downloading papers')
            
#     return paper_size

def main(start_id:str, end_id:str, max_workers:int=5, withAnalysis:bool=False):
    if withAnalysis:
        metrics = {}
        paper_list, metric = apply_time_analysis('CrawlPaperID')(get_all_papers)(start_id, end_id, max_workers)
        metrics.update(metric)
        
        paper_dict_list, metric = apply_time_analysis('ProcessPaper')(convert_paper_list_to_dictionary)(paper_list)
        save_dict_to_json(paper_size, "paper_sizes.json")
        metrics.update(metric)
        
        metrics.update({'Number of expected crawled papers': len(paper_dict_list)})
        metrics.update({'Number of successfully crawled papers': sum([1 for paper_dict in paper_dict_list if paper_dict != {}])})
        metrics.update({'Overall success rate': f'{(len(paper_dict_list) / sum([1 for paper_dict in paper_dict_list if paper_dict != {}])) * 100}:.3f%'})
        
    else:
        paper_list = get_all_papers(START_ID, TEST_END_ID, max_workers)
        paper_dict_list = convert_paper_list_to_dictionary(paper_list)
        
        # paper_size = execute_paper_multithread(paper_dict_list, NUM_THREADS)

        paper_size = execute_pipeline(paper_dict_list[:])
        save_dict_to_json(paper_size, "paper_sizes.json")

import arxiv

if __name__ == "__main__":
    start_time = time.time()
    main(start_id=START_ID, end_id=TEST_END_ID, max_workers=NUM_THREADS, withAnalysis=False)
    print("Time: ", time.time() - start_time)
    print()       