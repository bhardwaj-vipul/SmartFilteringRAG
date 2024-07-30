import json
import logging
import os

import fire
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from rag.config_loader import config
from rag.metadata_filter import MetadataFilter

from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.vectorstores import MongoDBAtlasVectorSearch

from rag.utils.mongodb_helper import get_mongo_collection
from rag.utils.prepare_test_data import get_docs_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_response(queries):
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    openai_api_base = os.getenv("OPEN_API_BASE")

    # default_headers is optional
    default_headers = os.getenv("OPEN_API_DEFAULT_HEADERS")
    default_headers = json.loads(default_headers) if default_headers else None

    llm = ChatOpenAI(model=config["model"], openai_api_key=openai_api_key, openai_api_base=openai_api_base,
                     default_headers=default_headers)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, openai_api_base=openai_api_base,
                                      default_headers=default_headers)

    system_prompt = """Use the following pieces of context to answer the user question in subsequent messages.
    The context was retrieved from a knowledge database and you should use only the facts from the context to answer.
    If you don't know the answer, just say that you don't know, don't try to make up an answer, use the context.
    Don't address the context directly, but use it to answer the user question like it's your own knowledge.
    Context: ```{context}```
    """

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{query}"),
        ]
    )

    logger.info(f"Input list of queries: {queries}")

    for query in queries:
        logger.info(f"Query: {query}")

        database_name = config["database_name"]
        collection_name = config["collection_name"]

        collection = get_mongo_collection(db_name=database_name, collection_name=collection_name)

        document_content_description, metadata_field_info = get_docs_metadata()

        metadata_filter = MetadataFilter(collection=collection,
                                         llm=llm,
                                         metadata_field_info=metadata_field_info,
                                         document_content_description=document_content_description)

        pre_filter, new_query = metadata_filter.generate_metadata_filter(query)

        logger.info(f"Original Query: {query}")
        logger.info(f"Generated pre-filter: {pre_filter}")
        logger.info(f"Generated new query: {new_query}")

        query = new_query

        vectorstore = MongoDBAtlasVectorSearch(collection, embeddings)
        retriever = vectorstore.as_retriever(
            search_kwargs={'pre_filter': pre_filter}
        )

        def format_docs(docs):
            return "\n\n".join([d.page_content for d in docs])

        chain = (
                {"context": retriever | format_docs, "query": RunnablePassthrough()}
                | qa_prompt
                | llm
                | StrOutputParser()
        )

        result = chain.invoke(query)

        logger.info(result)


def main():
    fire.Fire(generate_response)


if __name__ == '__main__':
    main()
