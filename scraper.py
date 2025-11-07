import arxiv
from datetime import timedelta
import time

START_ID = '2306.14505'
END_ID = '2307.11656'
TEST_END_ID = '2307.00140'
BATCH_SIZE = 200
CLIENT = arxiv.Client()

def get_daily_paper_ids(query, maxResults=1000,
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
    list of str
        List of papers'id with format (xxxx.xxxxxvx, x is a digit from 0 to 9)
    '''
    
    try:
        search = arxiv.Search(query=query,
                        max_results=maxResults,
                        sort_by=sortBy,
                        sort_order=sortOrder)

        
        paperList = list(CLIENT.results(search))

    except Exception as e:
        if 'Page of results was unexpectedly empty' in str(e):
            print('\t==>There is no paper on this date')
        else:
            print(f'[EXCEPTION][get_daily_paper_ids]: {e}')
        return []

    return [get_id_from_arxiv_link(paper.entry_id, withVersion=True) for paper in paperList]


def get_id_from_arxiv_link(url, withVersion=True):
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
        fullId = url.split('/abs/')[1]
    else:
        fullId = url

    if withVersion:
        return fullId
    else:
        arxivId = fullId.split('v')[0]
        return arxivId


def filter_papers_in_id_range(paperIdList, startId=None, endId=None):
    '''
    A function to filter the list of papers in a given date range

    Parameters
    ----------
    paperIdList: list of str
        a list of papers' id to filter with format (xxxx.xxxxxvx, x is a digit from 0 to 9)
    startId: str
        paper's start ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)
    endId: str
        paper's end ID (format: 'xxxx.xxxxx', x is a digit from 0 to 9)

    Return
    ------
    list of str
        a list contains filtered papers'id with format (xxxx.xxxxxvx, x is a digit from 0 to 9)
    '''
    if startId is None:
        return [paper for paper in paperIdList if get_id_from_arxiv_link(paper, withVersion=False) <= endId]
    
    if endId is None:
        return [paper for paper in paperIdList if startId <= get_id_from_arxiv_link(paper, withVersion=False)]

    return [paper for paper in paperIdList if startId <= get_id_from_arxiv_link(paper, withVersion=False) <= endId]


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
    
    paperList = list(CLIENT.results(search))
    
    return(paperList[0].published, paperList[1].published)


def get_remaining_versions_of_paper(arxivId):
    '''
    A function to get all the versions of a paper's ID

    Parameter
    ---------
    arxivId: str
        newest version's ID of a paper(format: 'xxxx.xxxxxvx', x is a digit from 0 to 9)

    Return
    ------
    list of str
        a list contains remaining versions'id of a paper (xxxx.xxxxxvx, x is a digit from 0 to 9)
    '''
    numberOfVersion = arxivId.split('v')[1]
    basePaperId = arxivId.split('v')[0]

    versionsId = []

    for version in range(int(numberOfVersion) - 1):
        versionsId.append(basePaperId + 'v' + str(version + 1))

    return versionsId


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
        time.sleep(1) # small delay to avoid server overload
        if len(dailyPaperList) != 0:
            print(f'\tNumber of fetched paper\'s ids = {len(dailyPaperList)}')

        paperIdList.extend(dailyPaperList)

    paperIdList = filter_papers_in_id_range(paperIdList, startId, endId)

    remainingVersionList = []
    for paper in paperIdList:
        remainingVersionList.extend(get_remaining_versions_of_paper(paper))

    paperIdList.extend(remainingVersionList)

    # Debug
    print('=' * 50)
    print(f'Number of papers: {len(paperIdList)}')
    print('Starting to get all the versions...')

    paperIdList = sorted(paperIdList)

    for i in range(0, len(paperIdList), BATCH_SIZE):
        print(f'Fetching batch {int((i + 1) / BATCH_SIZE) + 1}/{int(len(paperIdList) / BATCH_SIZE) + 1}...')
        batch = paperIdList[i:i + BATCH_SIZE]
        search = arxiv.Search(id_list=batch)
        try:
            paperList.extend(list(CLIENT.results(search)))
            time.sleep(1) # small delay to avoid server overload
        except Exception as e:
            print(f"[ERROR][get_all_papers][] Fetching batch {i // BATCH_SIZE + 1}: {e}")

    return paperList



def main_func():
    startTime = time.time()

    paperList = get_all_papers(START_ID, END_ID)

    duration = time.time() - startTime

    print('=' * 50)
    print(f'Duration: {duration:.3f}s')

    # Print for checking
    for i in range(5):
        print(f'{paperList[i].entry_id} - {paperList[i].title}')



main_func()