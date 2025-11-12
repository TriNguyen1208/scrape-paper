from scraper import get_all_papers
from utils import convert_paper_list_to_dictionary, save_dict_to_json
from analysis import apply_disk_analysis, apply_time_analysis, apply_RAM_analysis
from thread_process import execute_pipeline

import time

START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2306.14800'
NUM_THREADS = 5

def main(start_id:str, end_id:str, max_workers:int=5, withAnalysis:bool=False):
    if withAnalysis:
        metrics = {}
        paper_list, metric = apply_time_analysis('CrawlPaperID')(get_all_papers)(start_id, end_id, max_workers)
        metrics.update(metric)
        
        paper_dict_list = convert_paper_list_to_dictionary(paper_list)
        
        paper_size, metric = apply_time_analysis('ProcessPaper')(execute_pipeline)(paper_dict_list[:20])
        save_dict_to_json(paper_size, "paper_sizes.json")
        metrics.update(metric)
        
        metrics.update({'Number of expected crawled papers': len(paper_list)})
        metrics.update({'Number of successfully crawled papers': sum([1 for size in paper_size if size != {}])})
        metrics.update({'Overall success rate': f'{(sum([1 for size in paper_size if size != {}]) / len(paper_list)) * 100:.3f}%'})
        return metrics
        
    else:
        paper_list = get_all_papers(start_id, end_id, max_workers)
        paper_dict_list = convert_paper_list_to_dictionary(paper_list)

        paper_size = execute_pipeline(paper_dict_list)
        save_dict_to_json(paper_size, "paper_sizes.json")
        return {}


if __name__ == "__main__":
    start_time = time.time()
    metrics = main(start_id=START_ID, end_id=TEST_END_ID, max_workers=NUM_THREADS, withAnalysis=False)
    print()
    
    for key, value in metrics.items():
        print(f'{key}: {value}')
    print("Time: ", time.time() - start_time)
    