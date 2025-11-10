import arxiv
import os

def download_one_paper(
    paper: arxiv.Result, 
    save_dir: str = "./tex"
):
    '''
    A helper function to download one paper and save to tex folder

    Parameters
    ----------
    paper: arxiv.Result
       paper
    Return
    ------
    '''
    os.makedirs(save_dir, exist_ok=True)
    paper.download_source(dirpath=save_dir, filename=f"{paper.entry_id.split('/')[-1]}.tar.gz")

def download_all_paper(
    paper_list: list[arxiv.Result], 
    save_dir: str = "./tex"
):
    '''
    A function to download all papers and save to tex folder

    Parameters
    ----------
    paper_list: list[arxiv.Result]
       list of papers
    Return
    ------
    '''
    os.makedirs(save_dir, exist_ok=True)
    for paper in paper_list:
        download_one_paper(paper=paper, save_dir=save_dir)

# download_all_paper([paperList[0]])



