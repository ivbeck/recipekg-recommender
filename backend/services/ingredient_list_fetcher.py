import logging

from backend.config import execute_query

query = """
PREFIX food:      <http://purl.org/heals/food/>
PREFIX healsIng:  <http://purl.org/heals/ingredient/>
PREFIX recipeIng: <http://purl.org/recipekg/ingredient/>
PREFIX rdf:       <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT (REPLACE(STR(?ingType), "^.*/", "") AS ?ingredient)
WHERE {
  ?recipe food:hasIngredient ?ing .
  ?ing rdf:type ?ingType .

  FILTER (
    STRSTARTS(STR(?ingType), STR(healsIng:)) ||
    STRSTARTS(STR(?ingType), STR(recipeIng:))
  )
}
ORDER BY ?ingredient
"""


def get_ingredient_list():
    logging.info("Fetching ingredient list...")
    sparql_dict = execute_query(query)

    ingredients = [
        i["ingredient"]["value"]
        for i in sparql_dict["results"]["bindings"]
    ]

    return ingredients
