import arxiv
import requests
import time
# from scraper import paperIdList, paperList
from utils import CLIENT, get_id_from_arxiv_link

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
    paper = list(CLIENT.results(arxiv.Search(id_list=arxiv_id_list)))
    return paper

    
def extract_metadata(
    paper_id: str,
    paper_list_version: list[arxiv.Result],
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
    
    authors = [author.name for author in paper_list_version[0].authors]
    submission_date = paper_list_version[0].published.strftime("%d/%m/%Y")
    updated_date = [paper.updated.strftime("%d/%m/%Y") for paper in paper_list_version]

    metadata = {
        "paper_id": paper_id,
        "title": paper_list_version[0].title,
        "authors": authors,
        "submission_date": submission_date,
        "updated_date": updated_date    
    }
    if paper_list_version[0].journal_ref is not None:
        metadata["publication_venue"] = paper_list_version[0].journal_ref
    return metadata

def extract_metadata_reference(
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
    result = {
        "title": paper.title,
        "authors": authors,
        "submission_date": submission_date,
    }
    if paper.journal_ref is not None:
        result["publication_venue"] = paper.journal_ref
    return result

def extract_metadata_reference_list(
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
        metadata[paper.get_short_id()[:-2]] = extract_metadata_reference(paper)
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
    if response.status_code == 404:
        print(f"Paper is not found in semantic scholar")
        return
    
    while response.status_code == 429:
        print("Refetch getting references after one second...")
        time.sleep(1)
        response = requests.get(url=url, params=params)

    data = response.json()
    references = data.get("references", [])
    
    arxiv_id_ref_list = []
    arxiv_scholar_id = {}
    
    for reference in references:
        external_id = reference.get("externalIds", {})
        if external_id is not None:
            arxiv_id_ref = external_id.get("ArXiv")
        if arxiv_id_ref is not None:
            arxiv_id_ref_list.append(arxiv_id_ref)
            arxiv_scholar_id[arxiv_id_ref] = reference.get("paperId")
            
    papers_list = get_paper_from_id(arxiv_id_list=arxiv_id_ref_list)
    meta_data = extract_metadata_reference_list(paper_list=papers_list)
    for key, value in meta_data.items():
        value["semantic_scholar_id"] = arxiv_scholar_id[key]
    return meta_data