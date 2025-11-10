from scraper import get_all_papers_v2
from utils import save_dict_to_json, convert_paper_list_to_dictionary
from extract_data import extract_metadata, extract_reference
from download import download_all_paper

import time


START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2307.00140'


def main():
    paper_list = get_all_papers_v2(START_ID, TEST_END_ID)
    
    paper_dict = convert_paper_list_to_dictionary(paper_list)
    
    for i in range(1):
        paper_id = paper_dict[i]['id']
        versions = paper_dict[i]['versions']
        
        meta_data_reference = extract_reference(paper_id)
        save_dict_to_json(meta_data_reference, save_path="Metadata.json")
        
        meta_data_paper = extract_metadata(versions)
        save_dict_to_json(meta_data_paper, save_path="Metadata_paper.json")
        
        download_all_paper(versions)


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("Time: ", time.time() - start_time)
    print()