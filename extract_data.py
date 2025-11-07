import arxiv
from scraper import paperList, get_paper_from_id
import requests
import time

#A “metadata.json” file storing the paper’s metadata, including at minimum: the paper title (as a string),
#authors (as a list of strings), submission date (as a string in ISO format), and revised dates (as a list
#of date strings in ISO format). Additionally, include the publication venue (e.g., journal or conference
#name) if applicable.

# Result(
#  |      entry_id: str,
#  |      updated: datetime = datetime.datetime(1, 1, 1, 0, 0),
#  |      published: datetime = datetime.datetime(1, 1, 1, 0, 0),
#  |      title: str = '',
#  |      authors: List[Author] = [],
#  |      summary: str = '',
#  |      comment: str = '',
#  |      journal_ref: str = '',
#  |      doi: str = '',
#  |      primary_category: str = '',
#  |      categories: List[str] = [],
#  |      links: List[Link] = [],
#  |      _raw: feedparser.FeedParserDict = None
#  |  )


def extract_metadata_one_paper(
    paper: arxiv.Result
) -> object:
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
    metadata = {}
    for paper in paper_list:
        metadata[paper.entry_id.split('/')[-1]] = extract_metadata_one_paper(paper)
    return metadata

def extract_reference_one_paper(
    arxiv_id: str
) -> object:
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
        arxiv_id = external_id.get("ArXiv")
        arxiv_id_list.append(arxiv_id)
 
    papers_list = get_paper_from_id(arxiv_id_list=arxiv_id_list)
    meta_data = extract_metadata(paper_list=papers_list)
    return meta_data

def extract_reference(
    paper_id_without_version: list[str]
):
    reference = {}
    for arxiv_id in paper_id_without_version:
        ref = extract_reference_one_paper(arxiv_id=arxiv_id)
        reference[arxiv_id] = ref
    return reference

print(extract_reference(["2307.04323"]))