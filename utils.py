import os
import json
import arxiv
# import scraper
# import extract_data

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

# save_paperlist_to_json(scraper.paperList)
# save_dict_to_json(extract_data.meta_data_paper, save_path="json_files/metadata_src.json")
# save_dict_to_json(extract_data.meta_data_reference, save_path="reference_src.json")