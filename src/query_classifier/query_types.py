from dataclasses import dataclass
from typing import List, Union
@dataclass
class ChainQuery:
    """Represents a chain query with start, end, and retrieval target."""
    start: str
    end: str
    retrieve: str
    query_type: str = "chain"

@dataclass
class StarQuery:
    """Represents a star query with center and arms."""
    center: str
    arms: List[str]
    query_type: str = "star"

@dataclass 
class StarChainQuery:
    center: str
    arms: List[str]
@dataclass
class OtherQuery:
    """Represents a query that is neither chain nor star."""
    query_type: str = "other"

@dataclass
class QueryExample:
    """Example for few-shot learning context."""
    query: str
    classification: Union[ChainQuery, StarQuery, OtherQuery]