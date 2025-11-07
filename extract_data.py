import arxiv
import requests
import time
from scraper import get_paper_from_id, paper_id_without_version, paperList

def extract_metadata_one_paper(
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
    updated_date = paper.updated.strftime("%d/%m/%Y")
    return {
        "title": paper.title,
        "authors": authors,
        "submission_date": submission_date,
        "updated_date": updated_date,
        "publication venue": paper.journal_ref
    }
        

def extract_metadata(
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
        metadata[paper.entry_id.split('/')[-1]] = extract_metadata_one_paper(paper)
    return metadata

def extract_reference_one_paper(
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
        print("Refetch data after one second...")
        time.sleep(1)
        response = requests.get(url=url, params=params)
    data = response.json()
    references = data.get("references", [])
    arxiv_id_list = []
    for reference in references:
        external_id = reference.get("externalIds", {})
        if external_id is not None:
            arxiv_id = external_id.get("ArXiv")
        if arxiv_id is not None:
            arxiv_id_list.append(arxiv_id)
    papers_list = get_paper_from_id(arxiv_id_list=arxiv_id_list)
    meta_data = extract_metadata(paper_list=papers_list)
    return meta_data

def extract_reference(
    paper_id_without_version: list[str]
) -> object:
    '''
    A function to extract reference containing metadata of all papers

    Parameters
    ----------
    paper_id_without_version: list[str]
       list of string id without version
    Return
        object containing all data of references
    ------
    '''
    references = {}
    for arxiv_id in paper_id_without_version:
        ref = extract_reference_one_paper(arxiv_id=arxiv_id)
        references[arxiv_id] = ref
    return references

meta_data_paper = extract_metadata(paper_list=paperList)
meta_data_reference = extract_reference(paper_id_without_version=paper_id_without_version)