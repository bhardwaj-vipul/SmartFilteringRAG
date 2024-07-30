import json
import logging
import os

from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import MongoDBAtlasVectorSearch

from rag.config_loader import config
from rag.utils.mongodb_helper import get_mongo_collection, create_vector_search_index
from rag.utils.prepare_test_data import get_input_data


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_data():
    """This method will initialize the MongoDB collection with some sample data """
    database_name = config["database_name"]
    collection_name = config["collection_name"]
    vector_index_name = config["vector_index_name"]
    dimensions = config["embedding_model_dimensions"]
    similarity = config["similarity"]

    docs = get_input_data()

    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    openai_api_base = os.getenv("OPEN_API_BASE")

    # default_headers is optional
    default_headers = os.getenv("OPEN_API_DEFAULT_HEADERS")
    default_headers = json.loads(default_headers) if default_headers else None

    embeddings = OpenAIEmbeddings(model=config["embedding_model"], openai_api_key=openai_api_key, openai_api_base=openai_api_base,
                                  default_headers=default_headers)

    collection = get_mongo_collection(db_name=database_name, collection_name=collection_name)

    create_vector_search_index(
        collection=collection,
        index_name=vector_index_name,
        embedded_field_names=["embedding"],
        dimensions=dimensions,
        similarity=similarity,
        filter_fields_with_datatype={
            "rating": "number",
            "release_date": "token",
            "genre": "token"
        }
    )

    MongoDBAtlasVectorSearch.from_documents(docs, embeddings, collection=collection)

    logger.info("Initialization completed successfully")


initialize_data()
