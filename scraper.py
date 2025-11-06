import arxiv
from datetime import timedelta

START_ID = '2306.14505'
END_ID = '2307.11656'

def get_daily_papers(query='all', maxResults=1000,
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

    paperList = []

    for date in daterange(startDate, endDate):
        fmtDate = date.strftime('%Y%m%d')
        query = f'all AND submittedDate:[{fmtDate}0000 TO {fmtDate}2359]'

        print(f'Fetching papers on {date.strftime('%Y-%m-%d')}...')

        dailyPaperList = get_daily_papers(query=query)
        if len(dailyPaperList) != 0:
            print(f'\tNumber of fetched papers = {len(dailyPaperList)}')

        paperList.extend(dailyPaperList)

    return filter_papers_in_id_range(paperList, startId, endId)

paperList = get_all_papers(START_ID, END_ID)
print(f'Fetching {len(paperList)} papers')
