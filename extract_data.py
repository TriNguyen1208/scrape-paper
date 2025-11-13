import arxiv
import requests
import time
import sys
from dotenv import load_dotenv
import os
import re

from config import CLIENT, SEMANTIC_RATE_LIMIT, ARXIV_RATE_LIMIT, SEMANTIC_DELAY_LOCK, semantic_last_request_time, ARXIV_DELAY_LOCK, arxiv_last_request_time

load_dotenv()

def get_paper_from_id(
    arxiv_id_list: list[str],
    retry_times:int=3
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
    global arxiv_last_request_time
    paper = []
    
    for attempt in range(1, retry_times + 1):
        try:
            with ARXIV_DELAY_LOCK:
                time_since_last = time.time() - arxiv_last_request_time
                
                if time_since_last < ARXIV_RATE_LIMIT:
                    time.sleep(ARXIV_RATE_LIMIT - time_since_last)
                    
                arxiv_last_request_time = time.time()
            
            paper = list(CLIENT.results(arxiv.Search(id_list=arxiv_id_list)))
            break
        
        except Exception as e:
            is_recoverable = ('400' in str(e) or '429' in str(e))
            
            if is_recoverable:
                if attempt < retry_times:
                    time.sleep(ARXIV_RATE_LIMIT)
                else:
                    return []
            else:
                return []
            
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
    submission_date = paper_list_version[0].published.strftime("%Y-%m-%d")
    revised_date = [paper.updated.strftime("%Y-%m-%d") for paper in paper_list_version]

    metadata = {
        "paper_title": paper_list_version[0].title,
        "authors": authors,
        "submission_date": submission_date,
        "revised_date": revised_date    
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
    submission_date = paper.published.strftime("%Y-%m-%d")
    result = {
        "paper_title": paper.title,
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
        id = paper.get_short_id()[:-2]
            
        metadata[id.replace('.', '-')] = extract_metadata_reference(paper)
    return metadata

def extract_reference(
    arxiv_id: str,
    retry_times:int=3
) -> dict:
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
    # Handle rate limit
    global semantic_last_request_time
    with SEMANTIC_DELAY_LOCK:
        time_since_last = time.time() - semantic_last_request_time
        
        if time_since_last < SEMANTIC_RATE_LIMIT:
            time.sleep(SEMANTIC_RATE_LIMIT - time_since_last)
            
        semantic_last_request_time = time.time()
    
    
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
    params = {
        "fields": "references.externalIds"
    }
    api_key = os.getenv("API_KEY")
    headers = {"x-api-key": api_key}
    
    response = requests.get(url=url, params=params, headers=headers)
    if response.status_code == 404 or response.status_code == 400:
        sys.stdout.write('\n')
        print(f"Paper {arxiv_id} is not found in semantic scholar")
        return {}
    
    if response.status_code == 429:
        for _ in range(1, retry_times + 1):
            sys.stdout.write('\n')
            print(f"Refetch getting references after {SEMANTIC_RATE_LIMIT} second...")
            
            time.sleep(SEMANTIC_RATE_LIMIT)
            
            response = requests.get(url=url, params=params)

            if response.status_code != 429:
                break
            
        if response.status_code == 429:
            return {}
        
    try:
        data = response.json()
        
    except:
        sys.stdout.write('\n')
        print(f"Failed to decode JSON response for {arxiv_id}.")
        return {}
    
    if data is None:
        sys.stdout.write('\n')
        print(f"Semantic Scholar API returned success status but an empty body for {arxiv_id}.")
        return {}
    
    references = data.get("references", [])
    
    arxiv_id_ref_list = []
    arxiv_scholar_id = {}
    
    for reference in references:        
        external_id = reference.get("externalIds", {})
        arxiv_id_ref = None
        
        if external_id is not None:
            arxiv_id_ref = external_id.get("ArXiv")
            
        if arxiv_id_ref is not None:
            arxiv_id_ref_list.append(arxiv_id_ref)
            arxiv_scholar_id[arxiv_id_ref] = reference.get("paperId")
            print(arxiv_id_ref)
            
    papers_list = get_paper_from_id(arxiv_id_list=arxiv_id_ref_list)
    
    if papers_list == []:
        return {}
    
    meta_data = extract_metadata_reference_list(paper_list=papers_list)
    for key, value in meta_data.items():
        
        pattern = r'\d{4}.\d{5}'
        
        if re.match(pattern, key):
            value["semantic_scholar_id"] = arxiv_scholar_id[key.replace('-', '.')]
        else:
            value["semantic_scholar_id"] = arxiv_scholar_id[key]
        
    return meta_data