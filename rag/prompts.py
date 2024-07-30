from langchain_core.prompts import PromptTemplate


DEFAULT_SCHEMA = """\
<< Structured Request Schema >>
When responding use a markdown code snippet with a JSON object formatted in the following schema:

```json
{{{{
    "query": string \\ rewritten user's query after removing the information handled by the filter
    "filter": string \\ logical condition statement for filtering documents
}}}}
```

The query string should be re-written. Any conditions in the filter should not be mentioned in the query as well.

A logical condition statement is composed of one or more comparison and logical operation statements.

A comparison statement takes the form: `comp(attr, val)`:
- `comp` ({allowed_comparators}): comparator
- `attr` (string):  name of attribute to apply the comparison to
- `val` (string): is the comparison value

A logical operation statement takes the form `op(statement1, statement2, ...)`:
- `op` ({allowed_operators}): logical operator
- `statement1`, `statement2`, ... (comparison statements or logical operation statements): one or more statements to apply the operation to

Make sure that you only use the comparators and logical operators listed above and no others.
Make sure that filters only refer to attributes that exist in the data source.
Make sure that filters only use the attributed names with its function names if there are functions applied on them.
Make sure that filters only use format `YYYY-MM-DD` when handling date data typed values.
Make sure you understand the user's intent while generating a date filter. Use a range comparators such as gt | gte | lt | lte  for partial dates. 
Make sure that filters take into account the descriptions of attributes and only make comparisons that are feasible given the type of data being stored. 
Make sure that filters are only used as needed. If there are no filters that should be applied return "NO_FILTER" for the filter value.\
"""
DEFAULT_SCHEMA_PROMPT = PromptTemplate.from_template(DEFAULT_SCHEMA)

SONG_DATA_SOURCE = """\
```json
{{
    "content": "Lyrics of a song",
    "attributes": {{
        "artist": {{
            "type": "string",
            "description": "Name of the song artist"
        }},
        "length": {{
            "type": "integer",
            "description": "Length of the song in seconds"
        }},
        "genre": {{
            "type": "[string]",
            "description": "The song genre, one or many of [\"pop\", \"rock\" or \"rap\"]"
        }},
        "release_dt": {{
            "type": "string",
            "description": "Release date of the song."
        }}
    }}
}}
```\
"""

MOVIES_DATA_SOURCE = """\
```json
{{
    "content": "Brief summary of a movie",
    "attributes": {{
        "release_date": {{
            "type": "string",
            "description": "The release date of the movie"
        }},
        "genre": {{
            "type": "[string]",
            "description": "Keywords for filtering: ['anime', 'action', 'comedy', 'romance', 'thriller']"
        }}
    }}
}}
```\
"""

KEYWORDS_DATA_SOURCE = """\
```json
{{
    "content": "Documents store",
    "attributes": {{
        "tags": {{
            "type": "[string]",
            "description": "Keywords for filtering: ['rag', 'genai', 'gpt', 'langchain', 'llamaindex']"
        }}
    }}
}}
````\
"""

KEYWORDS_DATA_SOURCE_ANSWER = """\
```json
{{
    "query": "Give me updates",
    "filter": "in(\\"tags\\", [\\"rag\\", \\"langchain\\"])"
}}
````\
"""

KEYWORDS_DATE_DATA_SOURCE_ANSWER = """\
```json
{{
    "query": "Tell me updates on connectors based on the latest documentation",
    "filter": "in(\\"tags\\", [\\"langchain\\", \\"llamaindex\\"])"
}}
````\
"""

FULL_ANSWER = """\
```json
{{
    "query": "songs about teenage romance",
    "filter": "and(or(eq(\\"artist\\", \\"Taylor Swift\\"), eq(\\"artist\\", \\"Katy Perry\\")), lt(\\"length\\", 180), in(\\"genre\\", [\\"pop\\"]), and(gt(\\"release_dt\\", \\"2010-12-31\\"), lt(\\"release_dt\\", \\"2020-01-01\\")))"
}}
```\
"""

DATE_ANSWER = """\
```json
{{
    "query": "Recommend a movie with latest release date",
    "filter": "and(lt(\\"release_date\\", \\"2010-01-01\\"), in(\\"genre\\", [\\"action\\", \\"thriller\\"])"
}}
```\
"""

NO_FILTER_ANSWER = """\
```json
{{
    "query": "",
    "filter": "NO_FILTER"
}}
```\
"""

WITH_LIMIT_ANSWER = """\
```json
{{
    "query": "love",
    "filter": "NO_FILTER",
    "limit": 2
}}
```\
"""

DEFAULT_EXAMPLES = [
    {
        "i": 1,
        "data_source": MOVIES_DATA_SOURCE,
        "user_query": "Recommend an action or thriller genre movie release before 2010 and latest release date",
        "structured_request": DATE_ANSWER,
    },
    {
        "i": 2,
        "data_source": MOVIES_DATA_SOURCE,
        "user_query": "Recommend a latest movie",
        "structured_request": NO_FILTER_ANSWER
    },
    {
        "i": 3,
        "data_source": SONG_DATA_SOURCE,
        "user_query": "What are songs by Taylor Swift or Katy Perry about teenage romance under 3 minutes long in the dance pop genre released before 1 January 2020 and after 31 December, 2010",
        "structured_request": FULL_ANSWER,
    },
    {
        "i": 4,
        "data_source": SONG_DATA_SOURCE,
        "user_query": "What are songs that were not published on Spotify",
        "structured_request": NO_FILTER_ANSWER,
    },
    {
        "i": 5,
        "data_source": KEYWORDS_DATA_SOURCE,
        "user_query": "Give me updates on rag with langchain",
        "structured_request": KEYWORDS_DATA_SOURCE_ANSWER
    },
    {
        "i": 6,
        "data_source": KEYWORDS_DATA_SOURCE,
        "user_query": "Tell me updates on langchain and llamaindex connectors based on the latest documentation",
        "structured_request": KEYWORDS_DATE_DATA_SOURCE_ANSWER
    }
]

EXAMPLES_WITH_LIMIT = [
    {
        "i": 1,
        "data_source": SONG_DATA_SOURCE,
        "user_query": "What are songs by Taylor Swift or Katy Perry about teenage romance under 3 minutes long in the dance pop genre released before 1 January 2020 and after 31 December, 2010",
        "structured_request": FULL_ANSWER,
    },
    {
        "i": 2,
        "data_source": SONG_DATA_SOURCE,
        "user_query": "What are songs that were not published on Spotify",
        "structured_request": NO_FILTER_ANSWER,
    },
    {
        "i": 3,
        "data_source": SONG_DATA_SOURCE,
        "user_query": "What are three songs about love",
        "structured_request": WITH_LIMIT_ANSWER,
    },
]


# System prompt for time based filter
SYSTEM_PROMPT_TEMPLATE = """
Your goal is to structure the user's query to match the request schema provided below.

<< Structured Request Schema >>
When responding use a markdown code snippet with a JSON object formatted in the following schema:

```json
{{{{
    "query": string \\ rewritten user's query after removing the information handled by the filter
    "filter": string \\ logical condition statement for filtering documents with only a date filter
}}}}
```

The query string should be re-written. Any conditions in the filter should not be mentioned in the query as well.

A logical condition statement is composed of one or more comparison and logical operation statements.

A comparison statement takes the form: `comp(attr, val)`:
- `comp` ('eq | ne | gt | gte | lt | lte | in | nin'): comparator
- `attr` (string):  name of attribute to apply the comparison to
- `val` (string): is the comparison value

A logical operation statement takes the form `op(statement1, statement2, ...)`:
- `op` ('and | or'): logical operator
- `statement1`, `statement2`, ... (comparison statements or logical operation statements): one or more statements to apply the operation to

First step is to think about whether the user question mentions anything about date or time related that require a lookup in the MongoDB database. 
A lookup will be required if words like "latest", "recent", "earliest", "first", "last" etc. are present in the query.
If no lookup is required, return "NO_FILTER" for the filter value.
If no output received from the aggregate pipeline then return "NO_FILTER" for the filter value.

If required, create a syntactically correct MongoDB aggregation pipeline using only '$sort' and '$limit' operator to run.
Use projection to only fetch the relevant date columns.
Then look at the results of the aggregation pipeline and generate a date range query that can be used to filter relevant documents from the collection.

Make sure to ONLY generate date-based filters.
Make sure to only generate the query if a user asks about a time based question such as "latest", "most recent" etc and not mention a specific date time.
Make sure that you only use the comparators and logical operators listed above and no others.
Make sure that filters only refer to date/time attributes that exist in the data source.
Make sure that filters only use the attributed names with its function names if there are functions applied on them.
Make sure that filters only use format `YYYY-MM-DD` when handling date data typed values.
Make sure that filters take into account the descriptions of attributes and only make comparisons that are feasible given the type of data being stored.
Make sure that filters are only used as needed. If there are no filters that should be applied return "NO_FILTER" for the filter value.
Make sure the column names in the filter query are in double quotes.

<< Data Source >>
```json
{{{{
    "content": {content_description},
    "attributes": {attribute_info}
}}}}
```
"""


def enforce_constraints(input_json):
    def process_value(value):
        if isinstance(value, (str, int)):
            return value
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
        elif isinstance(value, dict) and 'date' in value and isinstance(value['date'], str):
            return value['date']
        else:
            raise ValueError("Invalid value type")

    def process_dict(d):
        if not isinstance(d, dict):
            return d
        processed_dict = {}
        for k, v in d.items():
            if k.startswith("$") and isinstance(v, list):
                # Handling $and and $or conditions
                processed_dict[k] = [process_dict(item) for item in v]
            elif k.startswith("$"):
                processed_dict[k] = process_value(v)
            else:
                processed_dict[k] = process_dict(v)
        return processed_dict

    return process_dict(input_json)
