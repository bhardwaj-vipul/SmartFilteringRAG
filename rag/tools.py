import json
import logging
import traceback
from typing import Dict, Optional, Type, Union, List

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBClient:
    """Data helper for querying MongoDB Vector Indexes."""

    def __init__(self, collection):
        self.collection = collection

    def run_aggregate_pipeline(self, pipeline: List[Dict]) -> List[Dict]:
        documents = list(self.collection.aggregate(pipeline))
        return documents


class BaseMongoDBTool(BaseModel):
    """Base tool for interacting with MongoDB."""

    client: MongoDBClient = Field(exclude=True)
    match_filter: dict = Field(exclude=True)

    class Config(BaseTool.Config):
        pass


class _QueryExecutorMongoDBToolInput(BaseModel):
    pipeline: str = Field(..., description="A valid MongoDB pipeline in JSON string format")


class QueryExecutorMongoDBTool(BaseMongoDBTool, BaseTool):
    name: str = "mongo_db_executor"
    description: str = """
    Input to this tool is a mongodb pipeline, output is a list of documents.
    If the pipeline is not correct, an error message will be returned.
    If an error is returned, report back to the user the issue and stop.
    """
    args_schema: Type[BaseModel] = _QueryExecutorMongoDBToolInput

    def _run(
            self,
            pipeline: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[List[Dict], str]:
        """Get the result for the mongodb pipeline."""
        try:
            logger.info(f"Pipeline: {pipeline}/")
            logger.info(f"Match filter: {self.match_filter}/")
            pipeline = json.loads(pipeline)
            # Remove the match operator if already exists
            pipeline = [op for op in pipeline if "$match" not in op]
            if self.match_filter:
                pipeline = [{"$match": self.match_filter}] + pipeline
            logger.info(f"Updated pipeline: {pipeline}/")
            documents = self.client.run_aggregate_pipeline(pipeline)
            return documents
        except Exception as e:
            """Format the error message"""
            return f"Error: {e}\n{traceback.format_exc()}"
