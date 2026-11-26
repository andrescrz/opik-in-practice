import pathlib

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from . import config, pdfgen


def build_index(data_dir: pathlib.Path = config.DATA_DIR) -> VectorStoreIndex:
    if not list(data_dir.glob("*.pdf")):
        pdfgen.generate_all(data_dir)
    Settings.llm = OpenAI(model=config.LLM_MODEL, temperature=0.0)
    Settings.embed_model = OpenAIEmbedding(model=config.EMBED_MODEL)
    # Small chunks so a policy section is its own chunk and retrieval has to pick the right course.
    Settings.node_parser = SentenceSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    documents = SimpleDirectoryReader(input_files=sorted(data_dir.glob("*.pdf"))).load_data()
    return VectorStoreIndex.from_documents(documents)
