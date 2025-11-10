import re
import os
import time
import arxiv
import shutil
import json
import tarfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import utils

TEMP_START_ID = '2306.14525'
TEMP_END_ID = '2307.00200'

paper_size = {} # {"paper_idv" : {"before:", "after:"}}

def remove_figures(folder_path: str):
    '''
    Delete all figures in a tex folder

    Parameters
    ---------
    text_path: str
    Return 
    ---------
    '''
    allowed_exts = {'.tex', '.bib', '.bbl'}

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            _, ext = os.path.splitext(item)
            if ext not in allowed_exts:
                os.remove(item_path)


def save_one_tex(paper: arxiv.Result, save_root: str = "./Save", report_size: bool = False):
    """
    Download all available versions of a paper given yyyymm-id (e.g., '2306-14525').
    """
    #Download the tar.gz 
    yyyymm_idv = paper.entry_id.split('/')[-1]
    base_id, version = yyyymm_idv.split('v')
    base_id = base_id.replace("-", ".")

    save_path = os.path.join(save_root, base_id, "tex")
    os.makedirs(save_path, exist_ok=True)

    client = arxiv.Client()
    search = arxiv.Search(id_list=[yyyymm_idv])
    results = list(client.results(search))

    if not results:
        print("Không tìm thấy paper.")
        return

    paper = results[0]
    paper.download_source(dirpath=save_path, filename=f"{yyyymm_idv}.tar.gz")

    #Extract the tar file
    extract_dir = os.path.join(save_path, yyyymm_idv)
    os.makedirs(extract_dir, exist_ok=True)

    tar_path = os.path.join(save_path, f"{yyyymm_idv}.tar.gz")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_dir)

    #Remove figures
    if (report_size):
        paper_size_before = utils.get_folder_size(extract_dir)
        remove_figures(extract_dir)
        paper_size_after = utils.get_folder_size(extract_dir)

        #Update paper_size
        paper_size[yyyymm_idv] = {"before": paper_size_before, "after": paper_size_after}
    else:
        remove_figures(extract_dir)

    os.remove(tar_path)

def transform_metadata(
    src_path="json_files/metadata_src.json", 
    dest_path="json_files/metadata_dest.json"
) -> None:
    '''
    Change the format of the metadata.json file for convenience
    '''

    with open(src_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {}

    for key, value in data.items():
        base_id = key.split('v')[0] 
    
        if base_id not in result:
            result[base_id] = {
                "title": value["title"],
                "authors": value["authors"],
                "submission_date": value["submission_date"],
                "update_dates": [value["updated_date"]],
                "publication venue": value["publication venue"]
            }
        else:
            result[base_id]["update_dates"].append(value["updated_date"])
    
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

def save_one_metadata(
    id: str, 
    metadata: dict, 
    save_root="./Save",
):
    save_dir = os.path.join(save_root, id)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "metadata.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

def save_one_reference(
    id: str, 
    reference: dict, 
    save_root="./Save",
):
    save_dir = os.path.join(save_root, id)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "reference.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(reference, f, ensure_ascii=False, indent=4)

def save_all_metadata(
    src_path="json_files/metadata_dest.json", 
    save_root="./Save",
    start_id=TEMP_START_ID,
    end_id=TEMP_END_ID
):

    with open(src_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    count = 0
    for key, value in metadata.items():
        if (key < TEMP_START_ID or key > TEMP_END_ID):
            break

        save_dir = os.path.join(save_root, key)
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, key + ".json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=4)

def get_all_paper_idvs(paper_list_path="json_files/paperList.json", max_count=None)->list:
    with open(paper_list_path, "r", encoding="utf-8") as f:
        paper_list = json.load(f)

    if (max_count is not None): max_count = min(max_count, len(paper_list))
    else: max_count = len(paper_list)

    paper_idv_list = [paper_list[i]["id"] for i in range(max_count)]
    return paper_idv_list

def save_all(save_root="./Save", start_id=TEMP_START_ID, end_id=TEMP_END_ID, max_workers=30, max_count=None):
    '''
    Save all neccessary files for a paper for submission, including: tex folder, metadata.json, reference.json
    '''
    paper_idvs = get_all_paper_idvs(max_count=max_count)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures_tex = {executor.submit(save_one_tex, pid): pid for pid in paper_idvs}
    
    for idv in paper_idvs:
        id = idv.split('v')[0]
        save_one_metadata(id)

    with open("json_files/paper_size", "w", encoding="utf-8") as f:
        json.dump(paper_size, f, ensure_ascii=False, indent=4)

# if __name__ == "__main__":
#     start_time = time.time()
#     save_all(max_count=10)
#     print("Time: ", time.time() - start_time)
    