import logging
from typing import Dict, Optional, List, Any
from urllib.parse import quote

from ..config import execute_query

logger = logging.getLogger(__name__)


class RecipeDetailQueryBuilder:
    PREFIXES = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX recipeKG: <http://purl.org/recipekg/>
        PREFIX healsIng: <http://purl.org/heals/ingredient/>
        PREFIX recipeIng: <http://purl.org/recipekg/ingredient/>
        PREFIX categories: <http://purl.org/recipekg/categories/>
        PREFIX food: <http://purl.org/heals/food/>
    """

    @staticmethod
    def build_query(recipe_uri: str) -> str:
        """Build a comprehensive SPARQL query to fetch all available recipe information."""
        recipe_uri_escaped = recipe_uri.replace('"', '\\"')
        
        query = f"""{RecipeDetailQueryBuilder.PREFIXES}
    SELECT DISTINCT 
        ?name 
        ?usdascore 
        ?calAmount 
        ?description
        ?recipeYield
        ?prepTime
        ?cookTime
        ?totalTime
        ?ingredientName
        ?ingredientType
        ?dietaryRestriction
        ?nutritionalProperty
        ?nutritionalAmount
        ?nutritionalUnit
        ?servingSize
        ?servingSizeUnit
    WHERE {{
        <{recipe_uri_escaped}> a schema:Recipe .
        
        OPTIONAL {{ <{recipe_uri_escaped}> schema:name ?name . }}
        OPTIONAL {{ <{recipe_uri_escaped}> recipeKG:hasUSDAScore ?usdascore . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:description ?description . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:recipeYield ?recipeYield . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:prepTime ?prepTime . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:cookTime ?cookTime . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:totalTime ?totalTime . }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> food:hasIngredient ?ingredient .
            ?ingredient rdf:type ?ingredientType .
            OPTIONAL {{
                ?ingredient schema:name ?ingredientName .
            }}
        }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> recipeKG:hasDietaryRestriction ?dietaryRestriction .
        }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> recipeKG:hasNutritionalInformation ?nut .
            ?nut recipeKG:hasCalorificData ?cal .
            ?cal recipeKG:hasAmount ?calAmount .
            OPTIONAL {{
                ?nut recipeKG:hasServingSize ?servingSize .
            }}
            OPTIONAL {{
                ?nut recipeKG:hasServingSizeUnit ?servingSizeUnit .
            }}
        }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> recipeKG:hasNutritionalInformation ?nutInfo .
            ?nutInfo ?nutritionalProperty ?nutritionalDataNode .
            FILTER (
                STRSTARTS(STR(?nutritionalProperty), STR(recipeKG:)) &&
                ?nutritionalProperty != recipeKG:hasCalorificData &&
                ?nutritionalProperty != recipeKG:hasNutritionalInformation &&
                (
                    ?nutritionalProperty = recipeKG:hasCarbohydrateData ||
                    ?nutritionalProperty = recipeKG:hasFatData ||
                    ?nutritionalProperty = recipeKG:hasProteinData ||
                    ?nutritionalProperty = recipeKG:hasFiberData ||
                    ?nutritionalProperty = recipeKG:hasSugarData ||
                    ?nutritionalProperty = recipeKG:hasSodiumData ||
                    ?nutritionalProperty = recipeKG:hasCholesterolData ||
                    ?nutritionalProperty = recipeKG:hasSaturatedFatData ||
                    ?nutritionalProperty = recipeKG:hasVitaminAData ||
                    ?nutritionalProperty = recipeKG:hasVitaminCData ||
                    ?nutritionalProperty = recipeKG:hasCalciumData ||
                    ?nutritionalProperty = recipeKG:hasIronData ||
                    ?nutritionalProperty = recipeKG:hasZincData ||
                    ?nutritionalProperty = recipeKG:hasPotassiumData ||
                    ?nutritionalProperty = recipeKG:hasMagnesiumData
                )
            )
            ?nutritionalDataNode recipeKG:hasAmount ?nutritionalAmount .
            OPTIONAL {{
                ?nutritionalDataNode recipeKG:hasUnit ?nutritionalUnit .
            }}
        }}
    }}
    ORDER BY ?ingredientName
        """
        return query


def fetch_recipe_details(recipe_uri: str) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive details for a single recipe.
    
    Args:
        recipe_uri: The URI of the recipe to fetch
        
    Returns:
        Dictionary containing all recipe information, or None if recipe not found
    """
    logger.info("Fetching recipe details for URI: %s", recipe_uri)
        
    query = RecipeDetailQueryBuilder.build_query(recipe_uri)
    logger.debug("SPARQL query: %s", query)
    
    try:
        result = execute_query(query)
        bindings = result.get("results", {}).get("bindings", [])
        
        if not bindings:
            logger.warning("No results found for recipe URI: %s", recipe_uri)
            return None
        
        nutritional_props_found = set()
        for binding in bindings:
            if "nutritionalProperty" in binding:
                prop = binding["nutritionalProperty"]["value"]
                prop_name = prop.split("/")[-1] if "/" in prop else prop
                nutritional_props_found.add(prop_name)
        if nutritional_props_found:
            logger.info("Found nutritional properties in query results: %s", sorted(nutritional_props_found))
        
        recipe_data = {
            "uri": recipe_uri,
            "name": None,
            "description": None,
            "usda_score": None,
            "calories": None,
            "recipe_yield": None,
            "prep_time": None,
            "cook_time": None,
            "total_time": None,
            "ingredients": [],
            "dietary_restrictions": [],
            "nutritional_info": {},
            "serving_size": None,
            "serving_size_unit": None
        }
        
        seen_ingredients = set()
        seen_dietary = set()
        seen_nutritional = set()
        
        for binding in bindings:
            if not recipe_data["name"] and "name" in binding:
                recipe_data["name"] = binding["name"]["value"]
            
            if not recipe_data["description"] and "description" in binding:
                recipe_data["description"] = binding["description"]["value"]
            
            if not recipe_data["usda_score"] and "usdascore" in binding:
                recipe_data["usda_score"] = binding["usdascore"]["value"]
            
            if not recipe_data["calories"] and "calAmount" in binding:
                recipe_data["calories"] = binding["calAmount"]["value"]
            
            if not recipe_data["recipe_yield"] and "recipeYield" in binding:
                recipe_data["recipe_yield"] = binding["recipeYield"]["value"]
            
            if not recipe_data["prep_time"] and "prepTime" in binding:
                recipe_data["prep_time"] = binding["prepTime"]["value"]
            
            if not recipe_data["cook_time"] and "cookTime" in binding:
                recipe_data["cook_time"] = binding["cookTime"]["value"]
            
            if not recipe_data["total_time"] and "totalTime" in binding:
                recipe_data["total_time"] = binding["totalTime"]["value"]
            
            if not recipe_data["serving_size"] and "servingSize" in binding:
                recipe_data["serving_size"] = binding["servingSize"]["value"]
            
            if not recipe_data["serving_size_unit"] and "servingSizeUnit" in binding:
                unit_value = binding["servingSizeUnit"]["value"]
                if unit_value.startswith("http://") or unit_value.startswith("https://"):
                    recipe_data["serving_size_unit"] = unit_value.split("/")[-1] if "/" in unit_value else unit_value
                else:
                    recipe_data["serving_size_unit"] = unit_value
            
            if "ingredientType" in binding:
                ing_type = binding["ingredientType"]["value"]
                if "ingredientName" in binding:
                    ing_name = binding["ingredientName"]["value"]
                else:
                    ing_name = ing_type.split("/")[-1] if "/" in ing_type else ing_type
                
                ing_key = (ing_type, ing_name)
                if ing_key not in seen_ingredients:
                    seen_ingredients.add(ing_key)
                    recipe_data["ingredients"].append({
                        "name": ing_name,
                        "type": ing_type
                    })
            
            if "dietaryRestriction" in binding:
                dietary = binding["dietaryRestriction"]["value"]
                dietary_name = dietary.split("/")[-1] if "/" in dietary else dietary
                if dietary_name not in seen_dietary:
                    seen_dietary.add(dietary_name)
                    recipe_data["dietary_restrictions"].append(dietary_name)
            
            if "nutritionalProperty" in binding and "nutritionalAmount" in binding:
                prop = binding["nutritionalProperty"]["value"]
                prop_name = prop.split("/")[-1] if "/" in prop else prop
                amount_value = binding["nutritionalAmount"]["value"]
                
                nutritional_key = (prop_name, amount_value)
                
                if nutritional_key not in seen_nutritional:
                    seen_nutritional.add(nutritional_key)
                    
                    display_name = prop_name.replace("has", "").replace("Data", "")
                    if not display_name:
                        display_name = prop_name
                    
                    logger.debug("Processing nutritional property: %s -> display_name: %s, amount: %s", 
                                prop_name, display_name, amount_value)
                    
                    unit = None
                    if "nutritionalUnit" in binding:
                        unit_value = binding["nutritionalUnit"]["value"]
                        if unit_value.startswith("http://") or unit_value.startswith("https://"):
                            unit = unit_value.split("/")[-1] if "/" in unit_value else unit_value
                        else:
                            unit = unit_value
                    
                    if not unit:
                        unit_map = {
                            "Carbohydrate": "g",
                            "Fat": "g",
                            "Protein": "g",
                            "Fiber": "g",
                            "Sugar": "g",
                            "SaturatedFat": "g",
                            "Sodium": "mg",
                            "Cholesterol": "mg",
                            "VitaminA": "µg",
                            "VitaminC": "mg",
                            "Calcium": "mg",
                            "Iron": "mg",
                            "Zinc": "mg",
                            "Potassium": "mg",
                            "Magnesium": "mg"
                        }
                        unit = unit_map.get(display_name, "")
                    
                    if unit:
                        formatted_value = f"{amount_value} {unit}"
                    else:
                        formatted_value = amount_value
                    
                    if display_name not in recipe_data["nutritional_info"]:
                        recipe_data["nutritional_info"][display_name] = formatted_value
                        logger.debug("Added nutritional info: %s = %s", display_name, formatted_value)
                    else:
                        logger.debug("Skipping duplicate nutritional info: %s (already have: %s)", 
                                    display_name, recipe_data["nutritional_info"][display_name])
        
        if recipe_data["serving_size"] and recipe_data["serving_size_unit"]:
            recipe_data["nutritional_context"] = f"per {recipe_data['serving_size']} {recipe_data['serving_size_unit']}"
        elif recipe_data["recipe_yield"]:
            recipe_data["nutritional_context"] = f"per serving (recipe yields {recipe_data['recipe_yield']})"
        else:
            recipe_data["nutritional_context"] = "per serving"
        
        if recipe_data["nutritional_info"]:
            logger.info("Final nutritional info to display: %s", sorted(recipe_data["nutritional_info"].keys()))
        else:
            logger.warning("No nutritional info found for recipe: %s", recipe_uri)
        
        logger.debug("Recipe data aggregated: %s", recipe_data)
        return recipe_data
        
    except Exception as e:
        logger.error("Error fetching recipe details: %s", e, exc_info=True)
        return None

