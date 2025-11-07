from ..config import execute_query

# ! TODO: implement this
query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <https://schema.org/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX recipeKG:<http://purl.org/recipekg/>
    PREFIX ingredient: <http://purl.org/heals/ingredient/> 
    PREFIX categories: <http://purl.org/heals/categories/> 
    PREFIX food: <http://purl.org/heals/food/> 
    
    SELECT ?recipe 
    WHERE {
        ?recipe recipeKG:belongsTo ?category.
        ?category rdfs:subClassOf* <http://purl.org/recipekg/categories/main-dish/>.
        ?recipe food:hasIngredient ?x.
        ?x a ingredient:Tomato.
        ?recipe recipeKG:hasNutritionalInformation ?y.
       ?y recipeKG:hasSugarData ?z.
       ?z recipeKG:hasFSAColor recipeKG:FSAGreen.
    } 
"""


def fetch_test_data():
    return execute_query(query)
