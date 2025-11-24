# arXiv Paper Scraper
This project automatically downloads metadata, references, and LaTeX source files from arXiv papers.  
It supports parallel scraping, configurable ID ranges, and adjustable scraping rates.

---

## 🧩 Environment Setup
### Requirements
- Python >= 3.10
- pip (latest version recommended)
- Libraries listed in `requirements.txt`

### Create virtual environment
- Windows:
```bash
python -m venv venv
venv\Scripts\activate         
```

- Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate  
```

### Install required libraries
pip install -r requirements.txt

## How to run the code
- Command line to run the code:
python main.py

- Change ID range:
Change START_ID and END_ID in `config.py`

- How to get statistics for analysis:
In `config.py`, assign `ANALYSIS_MODE = True`, then run the code using the command line above. The statistics will be printed on the console after the program finishes downloading.
Otherwise, assign `ANALYSIS_MODE = False` if you just want to scrape wihout printing statistics. 