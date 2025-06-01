from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple
from OntologyDesc import OntologyDesc
from Enumerator import Enumerator

class OntologyChainEnumerator(Enumerator):
    def __init__(self, ont_desc: OntologyDesc):
        super().__init__(ont_desc)
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
    
    def enumerate_chains(self, max_length: int = 10) -> Dict[int, List[List[Tuple[str, str, str]]]]:
        """
        Enumerate all possible chains up to max_length
        Returns: {chain_length: [list of chains]}
        Each chain is represented as [(start_class, property, end_class), ...]
        """
        chains_by_length = defaultdict(list)
        
        # Start from each class
        for start_class in self.classes:
            # Use BFS to find all possible chains
            queue = deque([(start_class, [])])  # (current_class, chain_so_far)
            visited_paths = set()  # To avoid infinite loops
            
            while queue:
                current_class, chain = queue.popleft()
                
                # Add current chain if it's not empty
                if chain:
                    chain_length = len(chain)
                    if chain_length <= max_length:
                        chains_by_length[chain_length].append(chain.copy())
                
                # Continue building chain if we haven't reached max length
                if len(chain) < max_length:
                    # Get all possible next steps from current class
                    if current_class in self.graph:
                        for prop, next_class in self.graph[current_class]:
                            new_chain = chain + [(current_class, prop, next_class)]
                            
                            # Create a path signature to detect cycles
                            path_signature = tuple(new_chain)
                            
                            # Avoid cycles and very long repetitive patterns
                            if path_signature not in visited_paths:
                                visited_paths.add(path_signature)
                                queue.append((next_class, new_chain))
        
        return dict(chains_by_length)
    
    def format_chain(self, chain: List[Tuple[str, str, str]]) -> str:
        """Format a chain for readable output"""
        if not chain:
            return ""
        
        formatted_parts = []
        for i, (start_class, prop, end_class) in enumerate(chain):
            if i == 0:
                formatted_parts.append(f"{start_class} → {prop} → {end_class}")
            else:
                formatted_parts.append(f" → {prop} → {end_class}")
        
        return "".join(formatted_parts)
    
    def generate_sparql_pattern(self, chain: List[Tuple[str, str, str]]) -> str:
        """Generate SPARQL pattern for a chain"""
        if not chain:
            return ""
        
        variables = []
        patterns = []
        
        for i, (start_class, prop, end_class) in enumerate(chain):
            start_var = f"?{start_class.lower()}{i}" if i == 0 else f"?{end_class.lower()}{i-1}"
            end_var = f"?{end_class.lower()}{i}"
            
            # Handle reverse properties
            if prop.endswith('⁻¹'):
                original_prop = prop[:-2]
                patterns.append(f"{end_var} :{original_prop} {start_var}")
            else:
                patterns.append(f"{start_var} :{prop} {end_var}")
            
            if i == 0:
                variables.append(start_var)
            variables.append(end_var)
        
        return " .\n  ".join(patterns)
    
    def print_all_chains(self, max_length: int = 4):
        """Print all enumerated chains organized by length"""
        chains = self.enumerate_chains(max_length)
        
        total_chains = sum(len(chain_list) for chain_list in chains.values())
        print(f"Total number of unique chains found: {total_chains}")
        print(f"Maximum chain length: {max_length}")
        print("=" * 80)
        
        for length in sorted(chains.keys()):
            chain_list = chains[length]
            print(f"\n{length}-hop chains ({len(chain_list)} total):")
            print("-" * 50)
            
            # Remove duplicates and sort for consistent output
            unique_chains = []
            seen = set()
            for chain in chain_list:
                chain_str = self.format_chain(chain)
                if chain_str not in seen:
                    seen.add(chain_str)
                    unique_chains.append(chain)
            
            for i, chain in enumerate(sorted(unique_chains, key=lambda x: self.format_chain(x)), 1):
                print(f"{i:2d}. {self.format_chain(chain)}")
                
                # Generate example query
                start_class = chain[0][0]
                end_class = chain[-1][2]
                print(f"    Example Query: 'What {end_class.lower()}s are related to this {start_class.lower()}?'")
                
                # Generate SPARQL pattern
                sparql_pattern = self.generate_sparql_pattern(chain)
                print(f"    SPARQL: {sparql_pattern}")
                print()
    def enumerate_for_class(self, node_class, max_length) -> List[List[Tuple[str, str, str]]]:
        """Enumerate chains starting from a specific class"""
        return self.get_chains_starting_from(node_class, max_length = 10)
    
    def enumerate_all(self, max_length: int = 4) -> Dict[int, List[List[Tuple[str, str, str]]]]:
        """Run the enumerator on the provided data"""
        return self.enumerate_chains(max_length)
 
    def get_chains_starting_from(self, start_class: str, max_length: int = 4) -> List[List[Tuple[str, str, str]]]:
        """Get all chains starting from a specific class"""
        all_chains = self.enumerate_chains(max_length)
        
        result = []
        for chain_list in all_chains.values():
            for chain in chain_list:
                if chain and chain[0][0] == start_class:
                    result.append(chain)
        
        return result
    
    def get_chains_ending_at(self, end_class: str, max_length: int = 4) -> List[List[Tuple[str, str, str]]]:
        """Get all chains ending at a specific class"""
        all_chains = self.enumerate_chains(max_length)
        
        result = []
        for chain_list in all_chains.values():
            for chain in chain_list:
                if chain and chain[-1][2] == end_class:
                    result.append(chain)
        
        return result


# Example usage
if __name__ == "__main__":
    desc= OntologyDesc() 
    enumerator = OntologyChainEnumerator(desc)
    
    
    print("HEALTHCARE ONTOLOGY CHAIN ENUMERATION")
    print("=" * 80)
    
    # Print all chains up to length 4
    enumerator.print_all_chains(max_length=4)
    
    print("\n" + "=" * 80)
    print("SPECIFIC QUERIES")
    print("=" * 80)
    
    # Example: Get all chains starting from Patient
    print("\nChains starting from Patient:")
    patient_chains = enumerator.get_chains_starting_from('Patient', max_length=3)
    for i, chain in enumerate(patient_chains[:10], 1):  # Show first 10
        print(f"{i}. {enumerator.format_chain(chain)}")
    
    # Example: Get all chains ending at Code
    print(f"\nChains ending at Code:")
    code_chains = enumerator.get_chains_ending_at('Code', max_length=3)
    for i, chain in enumerate(code_chains[:10], 1):  # Show first 10
        print(f"{i}. {enumerator.format_chain(chain)}")