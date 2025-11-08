from typing import List, Optional

from ..config import execute_query


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
    def build_ingredient_filters(ingredients: List[str]) -> str:
        if not ingredients:
            return ""

        filters = []
        for idx, ingredient in enumerate(ingredients):
            ingredient_var = f"?ing{idx}"
            filters.append(f"""
        ?recipe food:hasIngredient {ingredient_var} .
        {ingredient_var} a ingredient:{ingredient} .
        """)

        return "".join(filters)

    @staticmethod
    def build_dietary_filter(preference: Optional[str]) -> str:
        if not preference or preference.lower() not in RecipeQueryBuilder.DIETARY_PREFERENCES:
            return ""

        dietary_type = RecipeQueryBuilder.DIETARY_PREFERENCES[preference.lower()]
        return f"\n        ?recipe recipeKG:hasDietaryRestriction {dietary_type}."

    @staticmethod
    def build_query(ingredients: List[str], dietary_preference: Optional[str] = None) -> str:
        ingredient_filters = RecipeQueryBuilder.build_ingredient_filters(ingredients)
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
        ingredients: List[str],
        dietary_preference: Optional[str] = None
):
    print(ingredients)
    query = RecipeQueryBuilder.build_query(ingredients, dietary_preference)
    print(query)
    res = execute_query(query)
    print(res)
    return res
