import os
import arxiv
import shutil
import json
import tarfile
import sys
import gzip
import time
from utils import get_id_from_arxiv_link, get_folder_size

def remove_figures(folder_path: str):
    '''
    Delete all figures in a tex folder

    Parameters
    ---------
    text_path: str
    Return 
    ---------
    '''
    allowed_exts = {'.tex', '.bib'}

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
    yyyymm_idv = get_id_from_arxiv_link(paper.entry_id, True)
    base_id = get_id_from_arxiv_link(paper.entry_id, False)
    
    if yyyymm_idv is None or base_id is None:
        print(f"[EXCEPTION][save_one_tex]: Failed to parse IDs from entry_id={paper.entry_id}")
        return {}
    
    yyyymm_idv, base_id = yyyymm_idv.replace('.', '-'), base_id.replace('.', '-')

    save_path = os.path.join(save_root, base_id, "tex")
    os.makedirs(save_path, exist_ok=True)

    try:
        file_path = paper.download_source(dirpath=save_path, filename=f"{yyyymm_idv}.tar.gz")
        if file_path is None:
            print(f'[DEBUG][save_one_tex]: file_path is None. ({yyyymm_idv})')
        else:
            print(f'[DEBUG][save_one_tex]: file_path is not None. ({yyyymm_idv})')

    except Exception as e:
        sys.stdout.write('\n')
        print(f'[EXCEPTION][save_one_tex][download_source]: {e}.')
        return {}
        
        # if attempt == retry_attempts:
        #     print(f'[EXCEPTION][save_one_tex]: Give up to retry')
        #     return {}

    #Extract the tar file
    extract_dir = os.path.join(save_path, yyyymm_idv)
    os.makedirs(extract_dir, exist_ok=True)

    tar_path = os.path.join(save_path, f"{yyyymm_idv}.tar.gz")

    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
    
    except Exception as e:
        sys.stdout.write('\n')
        print(f"[EXCEPTION][save_one_tex][extract]: Failed to extract {tar_path}: {e}")
        return {}

    #Remove figures
    paper_size = {}
    if (report_size):
        paper_size_before = get_folder_size(extract_dir)
        remove_figures(extract_dir)
        paper_size_after = get_folder_size(extract_dir)

        #Update paper_size
        paper_size[yyyymm_idv] = {"before": paper_size_before, "after": paper_size_after}
    else:
        remove_figures(extract_dir)

    os.remove(tar_path)
    time.sleep(1)
    return paper_size

def save_one_metadata(
    id: str, 
    metadata: dict, 
    save_root="./Save",
):
    save_dir = os.path.join(save_root, id.replace('.', '-'))
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "metadata.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

def save_one_reference(
    id: str, 
    reference: dict, 
    save_root="./Save",
):
    save_dir = os.path.join(save_root, id.replace('.', '-'))
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "reference.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(reference, f, ensure_ascii=False, indent=4)