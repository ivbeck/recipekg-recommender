import logging
from typing import List, Optional

from ..config import execute_query

logger = logging.getLogger(__name__)


class RecipeQueryBuilder:
    PREFIXES = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX recipeKG: <http://purl.org/recipekg/>
        PREFIX ingredient: <http://purl.org/recipekg/ingredient/>
        PREFIX categories: <http://purl.org/recipekg/categories/>
        PREFIX food: <http://purl.org/heals/food/>
    """

    DIETARY_PREFERENCES = {
        'vegan': 'recipeKG:Vegan',
        'vegetarian': 'recipeKG:Vegetarian',
        'gluten-free': 'recipeKG:GlutenFree',
        'dairy-free': 'recipeKG:DairyFree',
        'low-carb': 'recipeKG:LowCarb',
    }

    @staticmethod
    def build_ingredient_filters(ingredient_groups: List[List[str]]) -> str:
        """
        Build ingredient filters where each group represents alternatives (OR logic).
        Groups are combined with AND logic.
        
        Args:
            ingredient_groups: List of lists, where each inner list contains alternative
                             ingredient names that should be combined with OR.
                             Example: [['Chickpea', 'Chickpeas'], ['Tomato']]
                             means: (Chickpea OR Chickpeas) AND (Tomato)
        """
        if not ingredient_groups:
            return ""

        filters = []
        for group_idx, ingredient_group in enumerate(ingredient_groups):
            if not ingredient_group:
                continue
                
            if len(ingredient_group) == 1:
                # Single ingredient - no OR needed
                ingredient_var = f"?ing{group_idx}"
                filters.append(f"""
        ?recipe food:hasIngredient {ingredient_var} .
        {ingredient_var} a ingredient:{ingredient_group[0]} .
        """)
            else:
                # Multiple alternatives - use UNION for OR logic
                union_parts = []
                for alt_idx, ingredient in enumerate(ingredient_group):
                    ingredient_var = f"?ing{group_idx}_{alt_idx}"
                    union_parts.append(f"""            {{
                ?recipe food:hasIngredient {ingredient_var} .
                {ingredient_var} a ingredient:{ingredient} .
            }}""")
                
                filters.append(f"""
        {{
            {' UNION '.join(union_parts)}
        }}
        """)

        return "".join(filters)

    @staticmethod
    def build_dietary_filter(preference: Optional[str]) -> str:
        if not preference or preference.lower() not in RecipeQueryBuilder.DIETARY_PREFERENCES:
            return ""

        dietary_type = RecipeQueryBuilder.DIETARY_PREFERENCES[preference.lower()]
        return f"\n        ?recipe recipeKG:hasDietaryRestriction {dietary_type}."

    @staticmethod
    def build_query(ingredient_groups: List[List[str]], dietary_preference: Optional[str] = None) -> str:
        """
        Build query with ingredient groups.
        
        Args:
            ingredient_groups: List of lists, where each inner list contains alternative
                             ingredient names (OR logic within group, AND logic between groups)
            dietary_preference: Optional dietary preference filter
        """
        ingredient_filters = RecipeQueryBuilder.build_ingredient_filters(ingredient_groups)
        dietary_filter = RecipeQueryBuilder.build_dietary_filter(dietary_preference)

        query = f"""{RecipeQueryBuilder.PREFIXES}
    SELECT DISTINCT ?recipe ?name ?usdascore ?calAmount
    WHERE {{
        ?recipe a   schema:Recipe ;
                    schema:name ?name ;
                    recipeKG:hasUSDAScore ?usdascore . 
        

        ?recipe recipeKG:hasNutritionalInformation ?nut .
        ?nut recipeKG:hasCalorificData ?cal .
        ?cal recipeKG:hasAmount ?calAmount .
        
        {ingredient_filters}{dietary_filter}    
    }}
    ORDER BY DESC(?usdascore)
    LIMIT 1000
        """

        return query


def fetch_recipes_by_ingredients(
        ingredient_groups: List[List[str]],
        dietary_preference: Optional[str] = None
):
    """
    Fetch recipes by ingredient groups.
    
    Args:
        ingredient_groups: List of lists, where each inner list contains alternative
                         ingredient names (OR logic within group, AND logic between groups)
                         Example: [['Chickpea', 'Chickpeas'], ['Tomato']]
        dietary_preference: Optional dietary preference filter
    """
    logger.info("Fetching recipes for ingredient groups: %s", ingredient_groups)
    query = RecipeQueryBuilder.build_query(ingredient_groups, dietary_preference)
    logger.debug("SPARQL query: %s", query)
    res = execute_query(query)
    logger.debug("Query returned %d results", len(res.get("results", {}).get("bindings", [])))
    return res
