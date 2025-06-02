from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Tuple
from OntologyDesc import OntologyDesc
from Enumerator import Enumerator
class OntologyStarEnumerator(Enumerator):
    """This class enumerates star-shaped queries in an ontology.
    """
    def enumerate_star_queries(self, max_arms: int = 5) -> Dict[str, List[Dict]]:
        """
        Enumerate all possible star-shaped queries
        Returns: {center_class: [list of star queries]}
        Each star query contains: {center: str, arms: [list of (property, target_class)]}
        """
        star_queries = defaultdict(list)
        
        for center_class in self.classes:
            # Get all possible 1-hop connections from this center
            possible_arms = []
            if center_class in self.graph:
                for prop, target_class in self.graph[center_class]:
                    possible_arms.append((prop, target_class))
            
            if not possible_arms:
                continue
            
            # Generate all combinations of arms (from 2 to max_arms)
            
            for num_arms in range(2, min(len(possible_arms) + 1, max_arms + 1)):
                for arm_combination in combinations(possible_arms, num_arms):
                    star_query = {
                        'center': center_class,
                        'arms': list(arm_combination),
                        'num_arms': num_arms
                    }
                    star_queries[center_class].append(star_query)
        
        return dict(star_queries)
    
    def format_star_query(self, star_query: Dict) -> str:
        """Format a star query for readable output"""
        center = star_query['center']
        arms = star_query['arms']
        
        arm_descriptions = []
        for prop, target_class in arms:
            if prop.endswith('⁻¹'):
                original_prop = prop[:-2]
                arm_descriptions.append(f"←{original_prop}← {target_class}")
            else:
                arm_descriptions.append(f"→{prop}→ {target_class}")
        
        return f"{center} {{{', '.join(arm_descriptions)}}}"
    
    def generate_star_sparql(self, star_query: Dict) -> str:
        """Generate SPARQL pattern for a star query"""
        center = star_query['center']
        arms = star_query['arms']
        
        center_var = f"?{center.lower()}"
        patterns = []
        variables = [center_var]
        
        for i, (prop, target_class) in enumerate(arms):
            target_var = f"?{target_class.lower()}{i+1}"
            variables.append(target_var)
            
            if prop.endswith('⁻¹'):
                original_prop = prop[:-2]
                patterns.append(f"{target_var} :{original_prop} {center_var}")
            else:
                patterns.append(f"{center_var} :{prop} {target_var}")
        
        return " .\n  ".join(patterns)
    
    def print_star_queries(self, max_arms: int = 4):
        """Print all enumerated star queries organized by center class"""
        star_queries = self.enumerate_star_queries(max_arms)
        
        total_stars = sum(len(query_list) for query_list in star_queries.values())
        print(f"Total number of star queries found: {total_stars}")
        print(f"Maximum arms per star: {max_arms}")
        print("=" * 80)
        
        for center_class in sorted(star_queries.keys()):
            query_list = star_queries[center_class]
            if not query_list:
                continue
                
            print(f"\nStar queries centered on {center_class} ({len(query_list)} total):")
            print("-" * 50)
            
            # Group by number of arms
            by_arms = defaultdict(list)
            for query in query_list:
                by_arms[query['num_arms']].append(query)
            
            for num_arms in sorted(by_arms.keys()):
                queries = by_arms[num_arms]
                print(f"\n  {num_arms}-arm stars ({len(queries)} queries):")
                
                for i, query in enumerate(queries, 1):
                    print(f"    {i:2d}. {self.format_star_query(query)}")
                    
                    # Generate example natural language query
                    arms = query['arms']
                    arm_descriptions = []
                    for prop, target_class in arms:
                        if prop.endswith('⁻¹'):
                            arm_descriptions.append(f"{target_class.lower()}s")
                        else:
                            arm_descriptions.append(f"{target_class.lower()}s")
                    
                    example_query = f"Get all {', '.join(arm_descriptions)} for this {center_class.lower()}"
                    print(f"        Example: '{example_query}'")
                    
                    # Generate SPARQL
                    sparql = self.generate_star_sparql(query)
                    print(f"        SPARQL: {sparql}")
                    print()
    
    def get_star_queries_for_class(self, center_class: str, max_arms: int = 4) -> List[Dict]:
        """Get all star queries centered on a specific class"""
        all_stars = self.enumerate_star_queries(max_arms)
        return all_stars.get(center_class, [])
    def enumerate_all(self, max_arms: int = 5):
        enumerated_stars = self.enumerate_star_queries(max_arms)
        return enumerated_stars
    def enumerate_for_class(self, center_class: str, max_arms: int = 5):
        """Enumerate star queries for a specific center class"""
        return self.get_star_queries_for_class(center_class, max_arms)
    
if __name__ == "__main__":
    desc = OntologyDesc()
    
    enumerator = OntologyStarEnumerator(desc)
    
    star_queries = enumerator.enumerate_star_queries(max_arms=4)
    print(star_queries['Patient'])