import logging
from typing import List, Tuple, Optional
from difflib import SequenceMatcher, get_close_matches

logger = logging.getLogger(__name__)


def _calculate_similarity(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, s1, s2).ratio()


def _normalize_plural(word: str) -> List[str]:
    """
    Generate normalized forms of a word for pluralization matching.
    Returns a list of possible forms: original, singular, plural.
    """
    word = word.lower().strip()
    forms = [word]
    
    # Try to get singular form (remove common plural endings)
    if word.endswith('ies'):
        forms.append(word[:-3] + 'y')
    elif word.endswith('es') and len(word) > 3:
        if word[-3] not in 'aeiou':
            forms.append(word[:-2])
            forms.append(word[:-1])
    elif word.endswith('s') and len(word) > 1:
        forms.append(word[:-1])
    
    # Try to get plural forms
    if not word.endswith('s'):
        forms.append(word + 's')
    if word.endswith('y') and len(word) > 1:
        forms.append(word[:-1] + 'ies')
    elif word.endswith('o') or (word.endswith('ch') or word.endswith('sh') or word.endswith('x')):
        if not word.endswith('es'):
            forms.append(word + 'es')
    
    return list(set(forms))


def match_ingredients(
    input_ingredients: List[str],
    available_ingredients: List[str],
    cutoff: float = 0.6,
    high_similarity_threshold: float = 0.6,
    max_matches: int = 10
) -> List[Tuple[str, List[str]]]:
    """
    Match input ingredients to available ingredients in the knowledge graph.
    Returns multiple matches when similarity is high.
    
    Args:
        input_ingredients: List of user-provided ingredient names (may contain typos/variations)
        available_ingredients: List of valid ingredients from the knowledge graph
        cutoff: Minimum similarity threshold (0.0 to 1.0). Matches below this are ignored.
        high_similarity_threshold: Threshold for high similarity (0.0 to 1.0). 
                                   When matches are above this, all high-similarity matches are returned.
        max_matches: Maximum number of matches to consider per input ingredient
    
    Returns:
        List of tuples (input_ingredient, [matched_ingredients]), where matched_ingredients
        is a list of matched ingredient names (empty list if no match found).
        If multiple matches have similarity >= high_similarity_threshold, all such matches are returned.
        Otherwise, only the best match is returned (if above cutoff).
    """
    # Normalize available ingredients for case-insensitive matching
    normalized_available = {ing.lower(): ing for ing in available_ingredients}
    available_lower = list(normalized_available.keys())
    
    matches = []
    
    for input_ingredient in input_ingredients:
        input_lower = input_ingredient.lower().strip()
        
        logger.debug("Processing input ingredient: '%s' (lower: '%s')", input_ingredient, input_lower)
        
        input_variants = _normalize_plural(input_ingredient)
        matched_ingredients_set = set()
        
        # First, try exact match (case-insensitive)
        if input_lower in normalized_available:
            matched_ing = normalized_available[input_lower]
            matched_ingredients_set.add(matched_ing)
            logger.debug("Found direct exact match for '%s' -> '%s'", input_ingredient, matched_ing)
            
            # Also check for plural/singular variants of the matched ingredient in KG
            matched_variants = _normalize_plural(matched_ing)
            for variant in matched_variants:
                if variant in normalized_available:
                    matched_ingredients_set.add(normalized_available[variant])
            logger.debug("Including variants of matched ingredient: %s", matched_ingredients_set)
        
        # Try pluralization variants for exact match
        if not matched_ingredients_set:
            logger.debug("Generated variants for '%s': %s", input_ingredient, input_variants)
            for variant in input_variants:
                if variant in normalized_available:
                    matched_ing = normalized_available[variant]
                    matched_ingredients_set.add(matched_ing)
                    logger.debug("Found exact match via variant - input '%s' -> variant '%s' -> KG '%s'", 
                                input_ingredient, variant, matched_ing)
                    
                    # Also check for plural/singular variants of the matched ingredient in KG
                    matched_variants = _normalize_plural(matched_ing)
                    for matched_variant in matched_variants:
                        if matched_variant in normalized_available:
                            matched_ingredients_set.add(normalized_available[matched_variant])
                    break
        
        if matched_ingredients_set:
            matches.append((input_ingredient, list(matched_ingredients_set)))
            continue
        
        # Get potential matches with fuzzy matching
        all_candidates = set()
        for variant in input_variants:
            close_matches = get_close_matches(
                variant,
                available_lower,
                n=max_matches,
                cutoff=cutoff
            )
            all_candidates.update(close_matches)
        
        direct_matches = get_close_matches(
            input_lower,
            available_lower,
            n=max_matches,
            cutoff=cutoff
        )
        all_candidates.update(direct_matches)

        logger.debug("Close matches for '%s': %s", input_ingredient, list(all_candidates))
        
        if not all_candidates:
            matches.append((input_ingredient, []))
            continue
        
        # Calculate similarity for each candidate match
        match_similarities = []
        for candidate_lower in all_candidates:
            best_similarity = max(
                _calculate_similarity(input_lower, candidate_lower),
                *[_calculate_similarity(variant, candidate_lower) for variant in input_variants]
            )
            match_similarities.append((candidate_lower, best_similarity))
        
        match_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Check if we have high similarity matches
        high_similarity_matches = [
            normalized_available[matched_lower]
            for matched_lower, similarity in match_similarities
            if similarity >= high_similarity_threshold
        ]
        
        if high_similarity_matches:
            matches.append((input_ingredient, high_similarity_matches))
        else:
            best_match = normalized_available[match_similarities[0][0]]
            matches.append((input_ingredient, [best_match]))
    
    return matches


def get_matched_ingredients_only(
    input_ingredients: List[str],
    available_ingredients: List[str],
    cutoff: float = 0.6,
    high_similarity_threshold: float = 0.6
) -> List[str]:
    """
    Get only the successfully matched ingredients (flattens all matches).
    If multiple high-similarity matches exist, all are included.
    
    Args:
        input_ingredients: List of user-provided ingredient names
        available_ingredients: List of valid ingredients from the knowledge graph
        cutoff: Minimum similarity threshold (0.0 to 1.0)
        high_similarity_threshold: Threshold for high similarity (0.0 to 1.0)
    
    Returns:
        List of matched ingredient names (all successful matches, flattened)
    """
    matches = match_ingredients(
        input_ingredients, 
        available_ingredients, 
        cutoff, 
        high_similarity_threshold
    )
    matched = []
    for _, matched_list in matches:
        matched.extend(matched_list)
    return matched

