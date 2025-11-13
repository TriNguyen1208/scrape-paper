import os
import arxiv
import shutil
import json
import tarfile
import sys
import time
import requests
import gzip

from utils import get_id_from_arxiv_link, get_folder_size
from config import ARXIV_RATE_LIMIT, ARXIV_DELAY_LOCK, arxiv_last_request_time

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
            remove_figures(item_path)
        else:
            _, ext = os.path.splitext(item)
            if ext not in allowed_exts:
                os.remove(item_path)  

def download_zip_file(paper_id: str, save_dir: str):
    url = f"https://arxiv.org/e-print/{paper_id.replace('-', '.')}"
    os.makedirs(save_dir, exist_ok=True)
    
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        temp_path = os.path.join(save_dir, f"{paper_id}.tmp")
        
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        
        with open(temp_path, "rb") as f:
            magic = f.read(4)
        
        if magic[:2] == b'%P':  # PDF file (%PDF)
            os.remove(temp_path)
            return ''
        elif magic[:2] == b'\x1f\x8b':  # gzip magic number
            if tarfile.is_tarfile(temp_path):
                ext = '.tar.gz'
            else:
                ext = '.gz'
        
        dest_path = os.path.join(save_dir, paper_id + ext)
        os.rename(temp_path, dest_path)
        
        return dest_path
    elif response.status_code == 404:
        sys.stdout.write('\n')
        print(f"{paper_id} has been deleted! (404 NOT FOUND)")
        return ''
    else:
        sys.stdout.write('\n')
        print(f"[Exception][download_zip_file]: Failed to download {paper_id}: HTTP {response.status_code}")
        return None

def save_one_tex(paper: arxiv.Result, save_root: str = "./Save", report_size: bool = False, retry_times:int=3):
    """
    Download all available versions of a paper given yyyymm-id (e.g., '2306-14525').
    """

    global arxiv_last_request_time

    #Download the tar.gz
    yyyymm_idv = get_id_from_arxiv_link(paper.entry_id, True)
    base_id = get_id_from_arxiv_link(paper.entry_id, False)
    
    yyyymm_idv, base_id = yyyymm_idv.replace('.', '-'), base_id.replace('.', '-')

    save_path = os.path.join(save_root, base_id, "tex")
    os.makedirs(save_path, exist_ok=True)
    
    dest_path = None

    for attempt in range(1, retry_times + 1):
        with ARXIV_DELAY_LOCK:
            time_since_last = time.time() - arxiv_last_request_time
            
            if time_since_last < ARXIV_RATE_LIMIT:
                time.sleep(ARXIV_RATE_LIMIT - time_since_last)
                
            arxiv_last_request_time = time.time()
        
        try:
            dest_path = download_zip_file(paper_id=yyyymm_idv, save_dir=save_path)
            break

        except Exception as e:
            if '429' in str(e):
                sys.stdout.write('\n')
                print(f'429: Request too many times. Attempt {attempt}')
            else:
                sys.stdout.write('\n')
                print(f'[EXCEPTION][save_one_tex][download_source]: {e}.')
            
            if attempt == retry_times:
                return {}
            
            time.sleep(ARXIV_RATE_LIMIT)

    if dest_path is not None and dest_path != '':
        #Extract the tar file
        extract_dir = os.path.join(save_path, yyyymm_idv)
        os.makedirs(extract_dir, exist_ok=True)

        tar_path = os.path.join(save_path, f"{yyyymm_idv}.tar.gz")
        gz_path = os.path.join(save_path, f"{yyyymm_idv}.gz")
        
        try:
            if os.path.exists(tar_path):
                if tarfile.is_tarfile(tar_path):
                    with tarfile.open(tar_path, "r:gz") as tar:
                        tar.extractall(path=extract_dir)
                os.remove(tar_path)
                        
            else:
                with gzip.open(gz_path, 'rb') as f_in:
                    file_name = getattr(f_in, 'name', None)
                    
                    if not file_name:
                        file_name = os.path.basename(gz_path)[:-3]
                        
                    file_name = os.path.splitext(os.path.basename(file_name))[0]

                    output_path = os.path.join(extract_dir, file_name + '.tex')
                    
                    with open(output_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                        
                os.remove(gz_path)
        
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
            paper_size['id'] = yyyymm_idv
            paper_size['size'] = {"before": paper_size_before, "after": paper_size_after}
        else:
            remove_figures(extract_dir)
        return paper_size
    
    elif dest_path == '':
        paper_size = {}
        paper_size['id'] = yyyymm_idv
        paper_size['size'] = {"before": 0, "after": 0}

    else:
        return {}

def save_one_metadata(
    id: str, 
    metadata: dict, 
    save_root="./Save",
):
    if metadata == {}:
        return
    
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
    if reference == {}:
        return
    
    save_dir = os.path.join(save_root, id.replace('.', '-'))
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "references.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(reference, f, ensure_ascii=False, indent=4)