import logging
from typing import Dict, Tuple

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.chains.query_constructor.base import AttributeInfo, _format_attribute_info, StructuredQueryOutputParser
from langchain.chains.query_constructor.base import load_query_constructor_runnable
from langchain_community.query_constructors.mongodb_atlas import MongoDBAtlasTranslator
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate, HumanMessagePromptTemplate, \
    SystemMessagePromptTemplate

from rag.prompts import enforce_constraints, EXAMPLES_WITH_LIMIT, DEFAULT_EXAMPLES, SYSTEM_PROMPT_TEMPLATE, \
    DEFAULT_SCHEMA_PROMPT
from rag.tools import MongoDBClient, QueryExecutorMongoDBTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataFilter:
    """
    MetadataFilter is responsible for generating a MongoDB pre-filter query based on the user query.
    """

    def __init__(self, collection, llm, metadata_field_info, document_content_description):
        """
        Initialize the MetadataFilter with a pymongo collection
        :param llm
        :param metadata_field_info: Dict of attribute_info and content_description
        :param document_content_description: Description of data
        """
        self.collection = collection
        self.llm = llm
        self.dataset_query_constructor = {}
        self.translator = MongoDBAtlasTranslator()
        self.metadata_field_info = metadata_field_info
        self.document_content_description = document_content_description

    def create_query_constructor(self):
        """
        This method will create query constructor for the collection.
        The query constructor is a chain with a prompt created using collection's metadata and content description.
        This query constructor will be used to generate pre-filter for a user's query.
        """
        query_constructor_run_name = "query_constructor"

        chain_kwargs = {}
        translator = MongoDBAtlasTranslator()
        chain_kwargs["allowed_operators"] = translator.allowed_operators
        chain_kwargs["allowed_comparators"] = translator.allowed_comparators
        enable_limit = False

        query_constructor = load_query_constructor_runnable(
            llm=self.llm,
            document_contents=self.document_content_description,
            attribute_info=self.metadata_field_info,
            enable_limit=enable_limit,
            schema_prompt=DEFAULT_SCHEMA_PROMPT,
            examples=EXAMPLES_WITH_LIMIT if enable_limit else DEFAULT_EXAMPLES,
            **chain_kwargs,
        )

        query_constructor = query_constructor.with_config(
            run_name=query_constructor_run_name
        )

        return query_constructor

    def generate_metadata_filter(self, query: str) -> Dict:
        """
        This method will use the query constructor and generate the pre-filters for a list of datasets.
        :param query: User's query
        :return (dict): Returns pre-filter and new query for each dataset.
        """
        query = f"""Answer the below question:\n
                Question: {query}
                """
        query_constructor = self.create_query_constructor()

        structured_query = {}
        try:
            structured_query = query_constructor.invoke(query)
            logger.info(f"Structured query: {structured_query}")
            new_query, new_kwargs = self.translator.visit_structured_query(structured_query)
            pre_filter = enforce_constraints(new_kwargs)
            logger.info(f"Generated pre-filter query: {pre_filter}")
            logger.info(f"Generated new query: {query} -> {new_query}")
            if pre_filter:
                time_based_pre_filter, new_query = self.generate_time_based_filter(pre_filter, new_query)
                if time_based_pre_filter:
                    logger.info(f"Merging metadata filter: {pre_filter}, and\n\t{time_based_pre_filter}")
                    pre_filter["pre_filter"] = {
                        "$and": [pre_filter["pre_filter"], time_based_pre_filter["pre_filter"]]}
            logger.info(f"Final pre-filter query: {pre_filter}")
            pre_filter = pre_filter["pre_filter"] if pre_filter else {}
            new_query = new_query if new_query else query
        except Exception as ex:
            logger.error(f"Failed while creating pre-filter: {ex}")
            raise ex
        return pre_filter, new_query

    def generate_time_based_filter(self, pre_filter: Dict, query: str) -> Tuple[str, Dict]:
        """
        This method is responsible for generating filter query for "most recent", "latest", "earliest" type of user
        questions.
        :param pre_filter: (Dict) metadata pre-filter query
        :param query: (str) user query
        :param dataset: (str) MongoDB collection name
        :return: (Tuple[str, Dict]) Rewritten user question and time-based filter query
        """
        client = MongoDBClient(collection=self.collection)
        executor_tool = QueryExecutorMongoDBTool(client=client, match_filter=pre_filter["pre_filter"])
        tools = [executor_tool]
        attribute_str = _format_attribute_info(self.metadata_field_info)
        system_prompt_template = SYSTEM_PROMPT_TEMPLATE.format(attribute_info=attribute_str,
                                                               content_description=self.document_content_description)

        prompt = ChatPromptTemplate(input_variables=["agent_scratchpad", "input"],
                                    messages=[SystemMessagePromptTemplate(
                                        prompt=PromptTemplate(input_variables=[], template=system_prompt_template)),
                                        MessagesPlaceholder(variable_name="chat_history", optional=True),
                                        HumanMessagePromptTemplate(
                                            prompt=PromptTemplate(input_variables=["input"],
                                                                  template="{input}")),
                                        MessagesPlaceholder(variable_name="agent_scratchpad")])

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        structured_query = agent_executor.invoke({"input": query})
        allowed_attributes = []
        for ainfo in self.metadata_field_info:
            allowed_attributes.append(
                ainfo.name if isinstance(ainfo, AttributeInfo) else ainfo["name"]
            )

        output_parser = StructuredQueryOutputParser.from_components(
            allowed_comparators=self.translator.allowed_comparators,
            allowed_operators=self.translator.allowed_operators,
            allowed_attributes=allowed_attributes
        )
        structured_query = output_parser.parse(structured_query["output"])
        logger.info(f"Structured query: {structured_query}")
        new_query, new_kwargs = self.translator.visit_structured_query(structured_query)
        time_based_pre_filter = enforce_constraints(new_kwargs)
        logger.info(f"Generated time based pre-filter query: {time_based_pre_filter}")
        logger.info(f"Generated new query after time based filtering: {query} -> {new_query}")
        return time_based_pre_filter, new_query
