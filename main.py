from scraper import get_all_papers
from utils import convert_paper_list_to_dictionary, save_dict_to_json, update_metrics, convert_second_to_format
from analysis import apply_analysis, analysis_reference
from thread_process import execute_pipeline
import time

START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2307.00656'
NUM_THREADS = 5

def main(start_id:str, end_id:str, max_workers:int=5, withAnalysis:bool=False):
    if withAnalysis:
        metrics = {}
        metrics['time'] = {}
        metrics['memory'] = {}
        metrics['general'] = {}
        paper_list, metric_crawl = apply_analysis('CrawlPaperID')(get_all_papers)(start_id, end_id, max_workers)

        metrics = update_metrics(metrics, metric_crawl)
        
        paper_dict_list = convert_paper_list_to_dictionary(paper_list)
        paper_size, metric_process = apply_analysis('ProcessPaper')(execute_pipeline)(paper_dict_list)

        save_dict_to_json(paper_size, "paper_sizes.json")
        
        metrics = update_metrics(metrics, metric_process)
        
        metrics['general'].update({'Number of expected crawled papers': len(paper_list)})
        metrics['general'].update({'Number of successfully crawled papers': sum([1 for size in paper_size if size != {}])})
        if len(paper_dict_list) == 0:
            metrics['general'].update({'Overall success rate': f'0%'})
        else:
            metrics['general'].update({'Overall success rate': f'{(sum([1 for size in paper_size if size != {}]) / len(paper_list)) * 100:.3f}%'})
        rate_success, count_reference_per_paper_average = analysis_reference(dirname="./Save")
        metrics['general'].update({'Average number of references per paper': f'{count_reference_per_paper_average}'})
        metrics['general'].update({'Average success rate for scraping reference metadata': f'{rate_success * 100:.3f}%'})

        return metrics
        
    else:
        paper_list = get_all_papers(start_id, end_id, max_workers)
        paper_dict_list = convert_paper_list_to_dictionary(paper_list)

        paper_size = execute_pipeline(paper_dict_list)
        save_dict_to_json(paper_size, "paper_sizes.json")
        return {}


if __name__ == "__main__":
    start_time = time.time()
    metrics = main(start_id=START_ID, end_id=TEST_END_ID, max_workers=NUM_THREADS, withAnalysis=True)
    
    print('=' * 50)
    if metrics != {}:
        for analysis_field, sub_dict in metrics.items():
            print(f'{analysis_field.upper()}:')
            for key, value in sub_dict.items():
                print(f'- {key}: {value}')
            
    print("Overall Time: ", convert_second_to_format(time.time() - start_time))