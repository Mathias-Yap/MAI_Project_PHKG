from abc import ABC, abstractmethod
from typing import Dict, List
import OntologyDesc
from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple

class Enumerator(ABC):
    """
    Abstract base class for enumerators.
    """
    def __init__(self, desc: OntologyDesc, name=None):
        """
        Initialize the enumerator with an optional name.
        """
        self.name = name
        if self.name is None:
            self.name = self.__class__.__name__
        self.classes = desc.classes
        self.properties = desc.properties
        self.reverse_properties = {} 
        self.reverse_properties = {}
        for prop, constraints in self.properties.items():
            reverse_prop = f"{prop}⁻¹"
            self.reverse_properties[reverse_prop] = {
                'domain': constraints['range'],
                'range': constraints['domain']
            }
        # Combine forward and reverse properties
        self.all_properties = {**self.properties, **self.reverse_properties}
        # Build adjacency graph for efficient traversal
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build adjacency list representation of the ontology graph"""
        graph = defaultdict(list)
        
        for prop, constraints in self.all_properties.items():
            for domain_class in constraints['domain']:
                for range_class in constraints['range']:
                    graph[domain_class].append((prop, range_class))
        
        return dict(graph)

    @abstractmethod
    def enumerate_all(self, **kwargs):
        """
        Run the enumerator on the provided data.
        """
        pass
    @abstractmethod
    def enumerate_for_class(self, class_name, **kwargs):
        """
        Enumerate for a specific class.
        """
