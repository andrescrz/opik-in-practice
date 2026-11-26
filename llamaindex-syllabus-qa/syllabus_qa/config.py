import pathlib

import dotenv

PROJECT_NAME = "llamaindex-syllabus-qa"
DATA_DIR = pathlib.Path(__file__).parents[1] / "data" / "syllabi"

# Walks up from this file to the first .env, so a repo-root .env works too.
dotenv.load_dotenv(dotenv.find_dotenv())

LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 32
TOP_K = 3
