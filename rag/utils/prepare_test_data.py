from langchain_core.documents import Document
from langchain.chains.query_constructor.base import AttributeInfo


def get_input_data():
    docs = [
        Document(
            page_content="A bunch of scientists bring back dinosaurs and mayhem breaks loose",
            metadata={"release_date": "1994-04-15", "rating": 7.7, "genre": ["action", "scifi", "adventure"]},
        ),
        Document(
            page_content="Leo DiCaprio gets lost in a dream within a dream within a dream within a ...",
            metadata={"release_date": "2010-07-16", "director": "Christopher Nolan", "rating": 8.2,
                      "genre": ["action", "thriller"]},
        ),
        Document(
            page_content="A psychologist / detective gets lost in a series of dreams within dreams within dreams and Inception reused the idea",
            metadata={"release_date": "2006-11-25", "director": "Satoshi Kon", "rating": 8.6,
                      "genre": ["anime", "thriller", "scifi"]},
        ),
        Document(
            page_content="A bunch of normal-sized women are supremely wholesome and some men pine after them",
            metadata={"release_date": "2019-12-25", "director": "Greta Gerwig", "rating": 8.3,
                      "genre": ["romance", "drama", "comedy"]},
        ),
        Document(
            page_content="Toys come alive and have a blast doing so",
            metadata={"release_date": "1995-11-22", "genre": ["anime", "fantasy"]},
        )
    ]

    return docs


def get_docs_metadata():
    metadata_field_info = [
        AttributeInfo(
            name="genre",
            description="Keywords for filtering: ['anime', 'action', 'comedy', 'romance', 'thriller']",
            type="[string]",
        ),
        AttributeInfo(
            name="release_date",
            description="The date the movie was released on",
            type="string",
        ),
        AttributeInfo(
            name="rating", description="A 1-10 rating for the movie", type="float"
        ),
    ]
    document_content_description = "Brief summary of a movie"

    return document_content_description, metadata_field_info