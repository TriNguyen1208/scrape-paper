import arxiv
from datetime import timedelta
import os

START_ID = '2306.14505'
END_ID = '2307.11656'

def get_daily_paper_ids(query='all', maxResults=1000,
                  sortBy=arxiv.SortCriterion.SubmittedDate,
                  sortOrder=arxiv.SortOrder.Ascending):

    '''
    A function to crawl paper using arxiv API

    Parameters
    ----------
    query: str
        Ensure the query is correctly formated from arxiv API
    maxResults: int
        The maximum number of results in a single query
    sortBy: arxiv.SortCriterion
        The feature to sort
    sortOrder: arxiv.SortOrder
        The sort order (Ascending, Descending)

    Return
    ------
    list
        List of crawled papers
    '''
    
    try:
        search = arxiv.Search(query=query,
                        max_results=maxResults,
                        sort_by=sortBy,
                        sort_order=sortOrder)

        
        paperList = list(arxiv.Client().results(search))

    except Exception as e:
        if 'Page of results was unexpectedly empty' in str(e):
            print('\t==>There is no paper on this date')
        else:
            print(f'[EXCEPTION][get_all_paper]: {e}')
        return []

    return paperList


def get_id_from_arxiv_link(url):
    '''
    A function to get id from arxiv url

    Parameter
    ---------
    url: str
        An arxiv url (format: 'http://arxiv.org/abs/xxxx.xxxxxvx', x is a digit from 0 to 9)

    Return
    ------
    str
        paper's ID without version (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    '''
    fullId = url.split('/abs/')[1]
    arxivId = fullId.split('v')[0]
    return arxivId


def filter_papers_in_id_range(paperList, startId=None, endId=None):
    '''
    A function to filter the list of papers in a given date range

    Parameters
    ----------
    paperList: list of arxiv.Result
        a list of paper to filter 
    startId: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    endId: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)

    Return
    ------
    list of arxiv.Result
        a list contains filtered papers
    '''
    if startId is None:
        return [paper for paper in paperList if get_id_from_arxiv_link(paper.entry_id) <= endId]
    
    if endId is None:
        return [paper for paper in paperList if startId <= get_id_from_arxiv_link(paper.entry_id)]

    return [paper for paper in paperList if startId <= get_id_from_arxiv_link(paper.entry_id) <= endId]


def get_date_range_from_id(startId, endId):
    '''
    A function to detect start date and end date from ids

    Parameters
    ----------
    startId: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    endId: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    
    Return
    ------
    tuple of datetime.datetime (format: '%Y-%m-%d %H:%M:%S)
        a tuple with start date and end date
    '''
    search = arxiv.Search(id_list=[startId, endId])
    
    paperList = list(arxiv.Client().results(search))
    
    return(paperList[0].published, paperList[1].published)


def get_version_of_paper(arxivId):
    '''
    A function to get all the versions of a paper's ID

    Parameter
    ---------
    arxivId: str
        newest version's ID of a paper(format: 'http://arxiv.org/abs/xxxx.xxxxxvx', x is a digit from 0 to 9)

    Return
    ------
    list
        a list contains all versions' ID of a paper
    '''
    paperId = arxivId.split('/')[-1]
    numberOfVersion = paperId.split('v')[1]
    basePaperId = paperId.split('v')[0]
    baseUrl = ''.join(arxivId[:len(arxivId) - len(paperId)])

    versions = []

    for version in range(int(numberOfVersion)):
        versions.append(baseUrl + basePaperId + 'v' + str(version + 1))

    return versions


def get_all_papers(startId:str, endId:str):
    '''
    A function to crawl all the papers (all version from each paper) within startID and endID using arxiv API

    Parameters
    ----------
    startId: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    endId: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)

    Return
    ------
    list of arxiv.Result
        a list contains crawled papers
    '''
    (startDate, endDate) = get_date_range_from_id(startId, endId)
    
    def daterange(startDate, endDate):
        for n in range((endDate - startDate).days + 1):
            yield startDate + timedelta(n)

    paperIdList = []
    paperList = []

    for date in daterange(startDate, endDate):
        fmtDate = date.strftime('%Y%m%d')
        query = f'all AND submittedDate:[{fmtDate}0000 TO {fmtDate}2359]'

        print(f'Fetching papers on {date.strftime('%Y-%m-%d')}...')

        dailyPaperList = get_daily_paper_ids(query=query)
        if len(dailyPaperList) != 0:
            print(f'\tNumber of fetched paper\'s ids = {len(dailyPaperList)}')

        paperIdList.extend(dailyPaperList)

    filteredPaperList = filter_papers_in_id_range(paperIdList, startId, endId)
    for paper in filteredPaperList:
        paperList.extend(get_version_of_paper(paper.entry_id))

    print(f'Fetching {len(filteredPaperList)} paper ids')
    print(f'Fetching {len(paperList)} papers')
        
    return paperList

def get_all_id_with_version(
    paper_list: list[arxiv.Result]
) -> list[str]:
    paper_list_id_version = []
    for paper in paper_list:
        paper_list_id_version.append(paper.entry_id.split('/')[-1])
    return paper_list_id_version

def get_all_id_without_version(
    paper_list: list[arxiv.Result]
) -> list[str]:
    paper_list_id = []
    dist = {}
    for paper in paper_list:
        id = paper.entry_id.split('/')[-1][:-2]
        if id not in dist:
            paper_list_id.append(id)
    return paper_list_id

def get_paper_from_id(
    arxiv_id_list: list[str]
) -> list[arxiv.Result]:
    paper = list(arxiv.Client().results(arxiv.Search(id_list=arxiv_id_list)))
    return paper

paperList = get_all_papers(START_ID, END_ID)
paper_id_version = get_all_id_with_version(paperList)
paper_id_without_version = get_all_id_without_version(paperList)