import arxiv
import requests
import time
from scraper import paperIdList, paperList
import utils 

def get_paper_from_id(
    arxiv_id_list: list[str]
) -> list[arxiv.Result]:
    '''
    A function to paper from id.

    Parameters
    ----------
    paper_list: list[arxiv.Result]
        List of the paper
    Return
    ------
    list of arxiv_id without version
        a list contains id.
    '''
    paper = list(arxiv.Client().results(arxiv.Search(id_list=arxiv_id_list)))
    return paper

def extract_metadata(
    paper: arxiv.Result
) -> object:
    '''
    A helper function to extract metadata of one paper

    Parameters
    ----------
    paper: arxiv.Result
       one paper
    Return
        object containing metadata
    ------
    '''
    authors = [author.name for author in paper.authors]
    submission_date = paper.published.strftime("%d/%m/%Y")
    # revised_dates = [v['date'].strftime("%d/%m/%Y") for v in paper.versions]
    # TODO: cái revised này phải coi lại, thêm cái sematic
    result = {
        "title": paper.title,
        "authors": authors,
        "submission_date": submission_date,
        # "revised_dates": revised_dates,
    }
    if paper.journal_ref is not None:
        result["publication_venue"] = paper.journal_ref
    return result

def extract_metadata_list(
    paper_list: list[arxiv.Result],
) -> dict:
    '''
    A function to extract metadata of all papers

    Parameters
    ----------
    paper_list: list[arxiv.Result]
       list of papers
    Return
        object containing all data.
    ------
    '''
    metadata = {}
    for paper in paper_list:
        metadata[paper.get_short_id()[:-2]] = extract_metadata(paper)
    return metadata

def extract_reference(
    arxiv_id: str
) -> object:
    '''
    A helper function to extract reference containing metadata of one paper

    Parameters
    ----------
    arxiv_id: string
       id of one paper
    Return
        object containing metadata
    ------
    '''

    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
    params = {
        "fields": "references.externalIds"
    }
    response = requests.get(url=url, params=params)
    while response.status_code == 429:
        print("Refetch getting references after one second...")
        time.sleep(1)
        response = requests.get(url=url, params=params)

    data = response.json()
    references = data.get("references", [])
    
    arxiv_id_ref_list = []

    for reference in references:
        external_id = reference.get("externalIds", {})
        if external_id is not None:
            arxiv_id_ref = external_id.get("ArXiv")
        if arxiv_id_ref is not None:
            arxiv_id_ref_list.append(arxiv_id_ref)
    papers_list = get_paper_from_id(arxiv_id_list=arxiv_id_ref_list)
    meta_data = extract_metadata_list(paper_list=papers_list)
    return meta_data

# meta_data_paper = extract_metadata(paper_list=paperList)
# utils.save_dict_to_json(meta_data_paper, save_path="Metadata_paper.json")

meta_data_reference = extract_reference(paper_id_without_version=paperIdList)
utils.save_dict_to_json(meta_data_reference, save_path="Metadata.json")
