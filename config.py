import threading
import arxiv

# ========== Rate limit ==========
ARXIV_RATE_LIMIT = 3.4
SEMANTIC_RATE_LIMIT = 1.3
CLIENT = arxiv.Client(delay_seconds=0.2)


# ========== Threading management ==========
ARXIV_DELAY_LOCK = threading.Lock()
arxiv_last_request_time = 0.0

SEMANTIC_DELAY_LOCK = threading.Lock()
semantic_last_request_time = 0.0

NUM_DOWNLOAD_THREADS = 5
NUM_EXTRACT_THREADS = 3
NUM_SAVE_THREADS = 4
NUM_FETCHING_THREADS = 3

FETCHING_BATCH_SIZE = 200
# ========== Paper management ==========
START_ID = '2307.05701'
END_ID = '2307.05705'
ANALYSIS_MODE = True
# TEST_END_ID = '2306.17004'

ID_RANGE = [['2306.14505', '2307.01656'], ['2307.01657', '2307.06656'], ['2307.06657', '2307.11656']]