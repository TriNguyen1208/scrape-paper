import os
import json
import arxiv
from collections import defaultdict
import sys

def save_paperlist_to_json(paper_list: list[arxiv.Result], save_path: str = "paperList.json"):
    """
    Save all papers' metadata from paperList into a JSON file.
    
    Parameters
    ----------
    paper_list : list[arxiv.Result]
        List of arxiv papers (already downloaded via API)
    save_path : str
        Path to save JSON file
    """
    data = []

    for paper in paper_list:
        metadata = {
            "id": paper.get_short_id(),  # e.g. 2503.01234v1
            "title": paper.title.strip(),
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary.strip(),
            "published": paper.published.strftime("%Y-%m-%d"),
            "updated": paper.updated.strftime("%Y-%m-%d"),
            "categories": paper.categories,
            "primary_category": paper.primary_category,
            "pdf_url": paper.pdf_url,
            "entry_id": paper.entry_id,
        }
        data.append(metadata)

    # Tạo thư mục nếu cần
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    # Lưu JSON (UTF-8, có định dạng đẹp)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ Saved metadata for {len(paper_list)} papers to {save_path}")

def save_dict_to_json(data: dict, save_path: str):
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_folder_size(folder_path: str) -> int:
    """
    Tính tổng kích thước của tất cả các file trong folder (tính theo bytes).

    Parameters
    ----------
    folder_path : str
        Đường dẫn đến folder

    Returns
    -------
    int
        Kích thước folder (bytes)
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            file_path = os.path.join(dirpath, f)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def get_id_from_arxiv_link(url, with_version=True):
    '''
    A function to get id from arxiv url

    Parameter
    ---------
    url: str
        An arxiv url (format: 'http://arxiv.org/abs/xxxx.xxxxxvx', x is a digit from 0 to 9)

    Return
    ------
    str
        paper's ID with/without version (format: 'xxxx.xxxxxvx' or 'xxxx.xxxxx', x is a digit from 0 to 9)
    '''
    if '/abs/' in url:
        full_id = url.split('/abs/')[1]
    else:
        full_id = url

    if with_version:
        return full_id
    else:
        arxiv_id = full_id.split('v')[0]
        return arxiv_id

def display_progress(current_value, total_value, display_text, length=50, end=False):
    '''
    A function to display progress bar
    
    Parameters
    ----------
    current_value: float
        current value
    total_value: float
        total value
    display_text: str
        the bar's title
    length: int
        the length of the bar
    '''
    percent = current_value / total_value
    filled = int(length * percent)
    bar = '█' * filled + '-' * (length - filled)
    sys.stdout.write(f'\r{display_text}: |{bar}| {percent*100:6.2f}% ({current_value}/{total_value})')
    sys.stdout.flush()
    if end or current_value == total_value:
        sys.stdout.write('\n')


def convert_paper_list_to_dictionary(paper_list:list[arxiv.Result])->list[dict]:
    '''
    A function to group papers'id 
    
    Parameter
    ---------
    paper_list: list of arxiv.Result
        a list contains papers in arxiv.Result type
        
    Return
    ------
    list of dictionary

        Example format:
        [
            {
                'id': '2306.14505',
                'versions': list[arxiv.Result]
            },
            {
                'id': '2306.14528',
                'versions': list[arxiv.Result]
            }
        ]
    '''
    
    paper_dict = defaultdict(list)
    
    for paper in paper_list:
        paper_id = get_id_from_arxiv_link(paper.entry_id, False)
        paper_dict[paper_id].append(paper)
        
    format_paper_dict = [{'id': paper_id, 'versions': versions} for paper_id, versions in paper_dict.items()]
        
    return format_paper_dict


def group_by_base_id_list(data_list):
    """
    Groups papers by their base ID (removing 'vX' version suffix) 
    and returns the result as a list of dictionaries.
    """
    paper_dict = defaultdict(list)
    
    for item in data_list:
        base_id = get_id_from_arxiv_link(item['id'], with_version=False)
        paper_dict[base_id].append(item)
        
    result_list = [
        {
            "id": base_id,
            "versions": versions_list
        }
        for base_id, versions_list in paper_dict.items()
    ]
    
    return result_list


def is_id_existed(paper_id):
    search = arxiv.Search(id_list=[paper_id])
    client = arxiv.Client(page_size=1, delay_seconds=0.2)
    try:
        next(client.results(search))
        return True
    except StopIteration:
        return False
    except Exception:
        # Network or parsing error — assume not found for safety
        return False

def form_paper_id(year, month, number):
    return f'{year}{'0' * (2 - len(month))}{month}.{'0' * (5 - len(str(number)))}{number}'
    
def find_last_id(year, month):
    low, high = 1, 1
    while is_id_existed(form_paper_id(year, month, high)):
        high *= 2
        if high > 99999:
            return 99999
    low = high // 2
    
    while low + 1 < high:
        mid = (low + high) // 2
        if is_id_existed(form_paper_id(year, month, mid)):
            low = mid
        else:
            high = mid
    return form_paper_id(year, month, low)

def find_first_id(year, month):
    low, high = 1, 1
    
    while not is_id_existed(form_paper_id(year, month, high)):
        high *= 2
        if high > 99999:
            return None
        
    while low + 1 < high:
        mid = (low + high) // 2
        
        if is_id_existed(form_paper_id(year, month, mid)):
            high = mid
        else:
            low = mid
            
    return form_paper_id(year, month, high)

def is_month_different(start_id, end_id):
    return (start_id[2:4] != end_id[2:4])


def update_metrics(metrics, new_metric_data):
    for key, value in new_metric_data.items():
        if 'time' in key.lower():
            metrics['time'].update({key: value})
        else:
            metrics['memory'].update({key: value})

    return metrics

def convert_second_to_format(value:float):
    value = int(value)
    minute = value // 60
    second = value % 60
    
    return f'{minute}m {second}s'