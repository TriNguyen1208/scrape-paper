from scraper import get_all_papers
from utils import save_dict_to_json, convert_paper_list_to_dictionary
from extract_data import extract_metadata, extract_reference
from download import download_papers
import submission

import time

START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2307.00140'

def main():
    paper_list = get_all_papers(START_ID, TEST_END_ID)
    paper_dict = convert_paper_list_to_dictionary(paper_list)
    
    temp_paper_dict = paper_dict[0:1]
    
    for paper in temp_paper_dict:
        paper_id = paper['id']
        versions = paper['versions']
        
        # Trích metadata và ref, các giá trị trả về là một dictionary, có thể dùng 2 dòng lưu file dưới để xem format
        meta_data_reference = extract_reference(paper_id)
        # save_dict_to_json(meta_data_reference, save_path="Metadata.json")
        
        meta_data_paper = extract_metadata(versions)
        # save_dict_to_json(meta_data_paper, save_path="Metadata_paper.json")
        
        
        # TODO: Cần một hàm xử lí metadata ở đây
        # Implement here
        
        # Hàm này chỉ mới download, chưa extract. Có thể sử dụng hàm của Bảo đã implement
        for paper_version in versions:
            submission.save_one_tex(paper_version, report_size=True)
        
        submission.save_one_metadata(id=paper_id, metadata=meta_data_paper)
        submission.save_one_reference(id=paper_id, reference=meta_data_reference)


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("Time: ", time.time() - start_time)
    print()