"""
Query Classifier Package

A zero-shot query classification system using LLMs to identify and extract components
from chain queries, star queries, and other query types.

Classes:
    - ChainQuery: Represents queries asking for connections between two entities
    - StarQuery: Represents queries asking for multiple items around a central concept
    - OtherQuery: Represents queries that don't fit chain or star patterns
    - QueryExample: Container for training examples
    - LLMQueryClassifier: Main classifier using HuggingFace transformers
"""
from .query_types import (
    ChainQuery,
    StarQuery, 
    OtherQuery,
    QueryExample
)

from .classifier import LLMQueryClassifier