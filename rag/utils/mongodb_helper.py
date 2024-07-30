import os
from typing import List, Dict

from pymongo import MongoClient
from pymongo.collection import Collection

MONGO_URI = os.environ["MONGO_URI"]


def get_mongo_collection(db_name: str, collection_name: str,
                         create_collection_if_not_exists: bool = True) -> Collection:
    """
    This function will create a pymongo client to access the mongo db collection
    :param db_name: MongoDB database name
    :param collection_name: MongoDB collection name
    :param create_collection_if_not_exists: bool flag to create collection if not exists. default to True
    :return: Returns pymongo collection object
    """
    client = MongoClient(MONGO_URI)
    db = client[db_name]
    colz = [c.get("name") for c in db.list_collections() if c is not None]
    if collection_name not in colz:
        if create_collection_if_not_exists:
            db.create_collection(collection_name)
    collection = client[db_name][collection_name]
    return collection


def create_vector_search_index(collection: Collection, index_name: str, embedded_field_names: List[str],
                               dimensions: int, similarity: str, filter_fields_with_datatype: Dict[str, str]) -> None:
    """
    This function will create vector search index on a mongo db collection
    :param collection: pymongo collection object
    :param index_name: name of the index
    :param embedded_field_names: list fields to be embedded
    :param dimensions: embeddings model output dimension
    :param similarity: similarity type cosine/sine
    :param filter_fields_with_datatype: additional fields can be used for pre-filtering with vector search
                                        e.g: {"field_name": "field_datatype"}
    :return:
    """
    fields = {}
    for field in embedded_field_names:
        fields[field] = {
            "type": "knnVector",
            "dimensions": dimensions,
            "similarity": similarity
        }

    for field_name, field_type in filter_fields_with_datatype.items():
        fields[field_name] = {
            "type": field_type
        }

    vector_index_definition = {
        "analyzer": "lucene.standard",
        "searchAnalyzer": "lucene.standard",
        "mappings": {
            "dynamic": True,
            "fields": fields
        }
    }

    collection.create_search_index(
        model={"name": index_name,
               "definition": vector_index_definition}
    )
