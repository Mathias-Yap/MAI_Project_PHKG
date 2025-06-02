"""This module contains a helper functions for graph importing."""

import os

from rdflib import Graph


def load_graph(
    file_name: str | None = None,
) -> Graph:
    """
    Load a specific graph from the dataset.

    Args:
        file_name (str | None): The name of the ttl file without the extension.

    Returns:
        Graph: The graph object.
    """
    if file_name is None:
        raise ValueError("Either 'file_name' or 'dataset' must be provided.")

    # Get the graph
    graph = Graph()
    graph.parse(
        os.path.join(
            "data",
            f"{file_name}.ttl",
        ),
        format="turtle",
    )

    return graph
