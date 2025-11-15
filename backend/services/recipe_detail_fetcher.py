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
        ?fsascore
        ?calAmount 
        ?description
        ?recipeYield
        ?prepTime
        ?cookTime
        ?totalTime
        ?datePublished
        ?ingredientName
        ?ingredientType
        ?ingredientQuantity
        ?ingredientUnit
        ?dietaryRestriction
        ?nutritionalProperty
        ?nutritionalAmount
        ?nutritionalUnit
        ?servingSize
        ?servingSizeUnit
        ?ratingValue
        ?ratingCount
        ?bestRating
        ?worstRating
        ?category
    WHERE {{
        <{recipe_uri_escaped}> a schema:Recipe .
        
        OPTIONAL {{ <{recipe_uri_escaped}> schema:name ?name . }}
        OPTIONAL {{ <{recipe_uri_escaped}> recipeKG:hasUSDAScore ?usdascore . }}
        OPTIONAL {{ <{recipe_uri_escaped}> recipeKG:hasFSAScore ?fsascore . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:description ?description . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:recipeYield ?recipeYield . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:prepTime ?prepTime . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:cookTime ?cookTime . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:totalTime ?totalTime . }}
        OPTIONAL {{ <{recipe_uri_escaped}> schema:datePublished ?datePublished . }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> food:hasIngredient ?ingredient .
            ?ingredient rdf:type ?ingredientType .
            OPTIONAL {{
                ?ingredient recipeKG:ingredientName ?ingredientName .
            }}
            OPTIONAL {{
                ?ingredient recipeKG:hasQuantity ?ingredientQuantity .
            }}
            OPTIONAL {{
                ?ingredient recipeKG:hasUnit ?ingredientUnit .
            }}
        }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> recipeKG:hasDietaryRestriction ?dietaryRestriction .
        }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> recipeKG:belongsTo ?category .
        }}
        
        OPTIONAL {{
            <{recipe_uri_escaped}> schema:aggregateRating ?rating .
            ?rating schema:ratingValue ?ratingValue .
            OPTIONAL {{ ?rating schema:ratingCount ?ratingCount . }}
            OPTIONAL {{ ?rating schema:bestRating ?bestRating . }}
            OPTIONAL {{ ?rating schema:worstRating ?worstRating . }}
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
            "fsa_score": None,
            "calories": None,
            "recipe_yield": [],
            "prep_time": None,
            "cook_time": None,
            "total_time": None,
            "date_published": None,
            "ingredients": [],
            "dietary_restrictions": [],
            "categories": [],
            "rating": None,
            "nutritional_info": {},
            "serving_size": None,
            "serving_size_unit": None
        }
        
        seen_ingredients = {}  # Changed to dict to track by name and aggregate quantities
        seen_dietary = set()
        seen_nutritional = set()
        seen_yields = set()
        seen_categories = set()
        seen_ratings = set()
        
        for binding in bindings:
            if not recipe_data["name"] and "name" in binding:
                recipe_data["name"] = binding["name"]["value"]
            
            if not recipe_data["description"] and "description" in binding:
                recipe_data["description"] = binding["description"]["value"]
            
            if not recipe_data["usda_score"] and "usdascore" in binding:
                recipe_data["usda_score"] = binding["usdascore"]["value"]
            
            if "fsascore" in binding:
                fsa_value = binding["fsascore"]["value"]
                if not recipe_data["fsa_score"]:
                    recipe_data["fsa_score"] = fsa_value
                elif isinstance(recipe_data["fsa_score"], list):
                    if fsa_value not in recipe_data["fsa_score"]:
                        recipe_data["fsa_score"].append(fsa_value)
                elif recipe_data["fsa_score"] != fsa_value:
                    recipe_data["fsa_score"] = [recipe_data["fsa_score"], fsa_value]
            
            if not recipe_data["calories"] and "calAmount" in binding:
                recipe_data["calories"] = binding["calAmount"]["value"]
            
            if "recipeYield" in binding:
                yield_value = binding["recipeYield"]["value"]
                if yield_value not in seen_yields:
                    seen_yields.add(yield_value)
                    recipe_data["recipe_yield"].append(yield_value)
            
            if not recipe_data["prep_time"] and "prepTime" in binding:
                recipe_data["prep_time"] = binding["prepTime"]["value"]
            
            if not recipe_data["cook_time"] and "cookTime" in binding:
                recipe_data["cook_time"] = binding["cookTime"]["value"]
            
            if not recipe_data["total_time"] and "totalTime" in binding:
                recipe_data["total_time"] = binding["totalTime"]["value"]
            
            if not recipe_data["date_published"] and "datePublished" in binding:
                recipe_data["date_published"] = binding["datePublished"]["value"]
            
            if not recipe_data["serving_size"] and "servingSize" in binding:
                recipe_data["serving_size"] = binding["servingSize"]["value"]
            
            if not recipe_data["serving_size_unit"] and "servingSizeUnit" in binding:
                unit_value = binding["servingSizeUnit"]["value"]
                if unit_value.startswith("http://") or unit_value.startswith("https://"):
                    recipe_data["serving_size_unit"] = unit_value.split("/")[-1] if "/" in unit_value else unit_value
                else:
                    recipe_data["serving_size_unit"] = unit_value
            
            if "ingredientName" in binding or "ingredientType" in binding:
                ing_name = None
                ing_type = None
                ing_quantity = None
                ing_unit = None
                
                if "ingredientName" in binding:
                    ing_name = binding["ingredientName"]["value"]
                elif "ingredientType" in binding:
                    ing_type = binding["ingredientType"]["value"]
                    ing_name = ing_type.split("/")[-1] if "/" in ing_type else ing_type
                
                if "ingredientType" in binding:
                    ing_type = binding["ingredientType"]["value"]
                
                if "ingredientQuantity" in binding:
                    ing_quantity = binding["ingredientQuantity"]["value"]
                
                if "ingredientUnit" in binding:
                    ing_unit = binding["ingredientUnit"]["value"]
                
                if ing_name:
                    # Build ingredient display string
                    parts = []
                    if ing_quantity:
                        parts.append(ing_quantity)
                    if ing_unit:
                        parts.append(ing_unit)
                    if ing_name:
                        parts.append(ing_name)
                    
                    display_name = " ".join(parts) if parts else ing_name
                    
                    # Use ingredient name as key for aggregation
                    if ing_name not in seen_ingredients:
                        seen_ingredients[ing_name] = {
                            "name": ing_name,
                            "type": ing_type,
                            "display": display_name,
                            "quantities": []
                        }
                        if ing_quantity:
                            seen_ingredients[ing_name]["quantities"].append({
                                "quantity": ing_quantity,
                                "unit": ing_unit
                            })
                    elif ing_quantity:
                        # Check if this quantity/unit combo is new
                        qty_info = {"quantity": ing_quantity, "unit": ing_unit}
                        if qty_info not in seen_ingredients[ing_name]["quantities"]:
                            seen_ingredients[ing_name]["quantities"].append(qty_info)
                            # Update display to show multiple quantities
                            if len(seen_ingredients[ing_name]["quantities"]) > 1:
                                qty_strs = []
                                for q in seen_ingredients[ing_name]["quantities"]:
                                    qty_parts = [q["quantity"]]
                                    if q["unit"]:
                                        qty_parts.append(q["unit"])
                                    qty_strs.append(" ".join(qty_parts))
                                seen_ingredients[ing_name]["display"] = f"{', '.join(qty_strs)} {ing_name}"
                            else:
                                # Single quantity, update display
                                seen_ingredients[ing_name]["display"] = display_name
            
            if "dietaryRestriction" in binding:
                dietary = binding["dietaryRestriction"]["value"]
                dietary_name = dietary.split("/")[-1] if "/" in dietary else dietary
                if dietary_name not in seen_dietary:
                    seen_dietary.add(dietary_name)
                    recipe_data["dietary_restrictions"].append(dietary_name)
            
            if "category" in binding:
                category = binding["category"]["value"]
                category_name = category.split("/")[-1] if "/" in category else category
                # Clean up category name (remove trailing slashes, replace hyphens with spaces)
                category_name = category_name.rstrip("/").replace("-", " ").title()
                if category_name and category_name not in seen_categories:
                    seen_categories.add(category_name)
                    recipe_data["categories"].append(category_name)
            
            if "ratingValue" in binding:
                rating_key = binding["ratingValue"]["value"]
                if rating_key not in seen_ratings:
                    seen_ratings.add(rating_key)
                    rating_data = {
                        "value": float(binding["ratingValue"]["value"]),
                        "count": None,
                        "best": None,
                        "worst": None
                    }
                    if "ratingCount" in binding:
                        rating_data["count"] = int(binding["ratingCount"]["value"])
                    if "bestRating" in binding:
                        rating_data["best"] = float(binding["bestRating"]["value"])
                    if "worstRating" in binding:
                        rating_data["worst"] = float(binding["worstRating"]["value"])
                    recipe_data["rating"] = rating_data
            
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
        
        # Convert ingredients dict to list
        recipe_data["ingredients"] = [
            {
                "name": ing["name"],
                "type": ing["type"],
                "display": ing["display"]
            }
            for ing in seen_ingredients.values()
        ]
        
        # Format recipe yield - join multiple yields or use single value
        if recipe_data["recipe_yield"]:
            if len(recipe_data["recipe_yield"]) == 1:
                recipe_data["recipe_yield"] = recipe_data["recipe_yield"][0]
            else:
                recipe_data["recipe_yield"] = " or ".join(recipe_data["recipe_yield"])
        else:
            recipe_data["recipe_yield"] = None
        
        # Format FSA score - join multiple scores or use single value
        if isinstance(recipe_data["fsa_score"], list):
            if len(recipe_data["fsa_score"]) == 1:
                recipe_data["fsa_score"] = recipe_data["fsa_score"][0]
            else:
                recipe_data["fsa_score"] = ", ".join(map(str, recipe_data["fsa_score"]))
        
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

