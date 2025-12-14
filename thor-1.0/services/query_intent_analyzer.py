"""
Query Intent Analyzer - Advanced intelligence module for understanding user queries
Detects intent, extracts entities, and classifies query types
"""
import re
from typing import Dict, List, Tuple, Optional


class QueryIntentAnalyzer:
    """Analyzes user queries to understand intent and extract key information"""
    
    def __init__(self):
        # Define query intent patterns - ORDER MATTERS (more specific first)
        self.intent_patterns = {
            'biographical': [
                # "Who is X" patterns - should match full names
                r'who\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Who is First Last
                r'who\s+is\s+([A-Z][a-z]+)',  # Who is Name
                r'who\'s\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Who's Name
                r'tell\s+me\s+about\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Tell me about Person
                r'who\s+was\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Who was Name (historical)
            ],
            'definition': [
                r'what\s+is\s+([a-z]+(?:\s+[a-z]+)*)\??$',  # what is X (lowercase = concept)
                r'what\s+are\s+([a-z]+(?:\s+[a-z]+)*)\??$',  # what are X
                r'what\'s\s+([a-z]+)\??$',
                r'whats\s+([a-z]+)\??$',
                r'define\s+(\w+)',
                r'definition\s+of\s+(\w+)',
                r'what\s+does\s+(\w+)\s+mean',
                r'meaning\s+of\s+(\w+)'
            ],
            'recipe': [
                r'how\s+to\s+(make|cook|prepare|bake|fry|grill)\s+(.+)',
                r'recipe\s+for\s+(.+)',
                r'how\s+do\s+(you|i)\s+(make|cook)\s+(.+)',
                r'ingredients\s+for\s+(.+)'
            ],
            'philosophical': [
                r'what(\'s|\s+is|s)\s+life\s*\??$',
                r'whats\s+life\s*\??$',
                r'meaning\s+of\s+life',
                r'what\s+is\s+existence',
                r'purpose\s+of\s+life',
                r'what\s+is\s+reality',
                r'what\s+is\s+consciousness',
            ],
            'how_to': [
                r'how\s+to\s+(\w+)',
                r'how\s+do\s+(you|i)\s+(\w+)',
                r'steps\s+to\s+(\w+)',
                r'tutorial\s+on\s+(\w+)'
            ],
            'comparison': [
                r'difference\s+between\s+(\w+)\s+and\s+(\w+)',
                r'compare\s+(\w+)\s+and\s+(\w+)',
                r'(\w+)\s+vs\s+(\w+)',
                r'(\w+)\s+versus\s+(\w+)'
            ],
            'programming': [
                r'(\w+)\s+(function|class|method|variable|array|object)',
                r'how\s+to\s+(\w+)\s+in\s+(javascript|python|java|typescript)',
                r'(\w+)\s+programming',
                r'(\w+)\s+code',
                r'(\w+)\s+syntax'
            ]
        }
        
        # Known person name patterns (helps identify "who is" queries)
        self.person_indicators = [
            'actor', 'actress', 'cricketer', 'player', 'singer', 'politician',
            'scientist', 'writer', 'director', 'producer', 'artist', 'musician',
            'president', 'minister', 'celebrity', 'star', 'legend', 'icon'
        ]
        
        # Common ambiguous words that cause false matches
        self.ambiguous_words = {
            'life': ['lifelong', 'lifetime', 'lifecycle', 'lifecycle'],
            'learning': ['learn', 'learner', 'learned'],
            'make': ['makes', 'making', 'maker'],
            'function': ['functional', 'functionality'],
            'physics': ['game physics', 'physics engine', 'physics simulation', 'physics-based']
        }
        
        # Words that should trigger web search (not brain lookup)
        self.force_web_search = [
            'what is life', 'meaning of life', 'purpose of life',
            'what is existence', 'what is reality', 'what is consciousness',
            'what is happiness', 'what is love', 'what is truth'
        ]
    
    def analyze(self, query: str) -> Dict:
        """Analyze query intent and extract key information"""
        query_lower = query.lower().strip()
        
        result = {
            'original_query': query,
            'intent': 'general',
            'entity': None,
            'entities': [],
            'query_type': 'general',
            'should_search_web': False,
            'confidence': 0.0,
            'expanded_query': query,
            'strict_match_required': False,
            'is_person_query': False,  # NEW: Flag for biographical queries
            'response_priority': 'identity'  # NEW: What to prioritize in response
        }
        
        # Check for force web search queries (exact or partial match)
        for pattern in self.force_web_search:
            if pattern in query_lower:
                result['should_search_web'] = True
                result['query_type'] = 'philosophical'
                result['intent'] = 'philosophical'
                result['strict_match_required'] = True
                result['confidence'] = 1.0
                return result
        
        # Also check for "what's life" variations
        if ('what' in query_lower and 'life' in query_lower and 
            len(query_lower.split()) <= 4):  # Short query like "whats life" or "what is life"
            # Check if it's NOT about "life in X" or "life of X"
            if not any(word in query_lower for word in ['in ', 'of ', 'for ', 'with ', 'about ']):
                result['should_search_web'] = True
                result['query_type'] = 'philosophical'
                result['intent'] = 'philosophical'
                result['strict_match_required'] = True
                result['confidence'] = 1.0
                return result
        
        # PRIORITY CHECK: "Who is X" biographical queries (check FIRST with original case)
        who_is_match = re.search(r'who\s+(?:is|was|\'s)\s+(.+?)\??$', query, re.IGNORECASE)
        if who_is_match:
            person_name = who_is_match.group(1).strip()
            # Check if it looks like a person's name (has capital letters or multiple words)
            if (any(c.isupper() for c in person_name) or 
                len(person_name.split()) >= 2 or
                person_name.lower() not in ['it', 'this', 'that', 'he', 'she', 'they']):
                result['intent'] = 'biographical'
                result['query_type'] = 'biographical'
                result['entity'] = person_name
                result['entities'] = [person_name]
                result['confidence'] = 0.95
                result['is_person_query'] = True
                result['should_search_web'] = True  # Always search for people
                result['response_priority'] = 'identity'  # Prioritize who they ARE, not trivia
                result['strict_match_required'] = True
                result['expanded_query'] = f"{person_name} biography who is {person_name}"
                return result
        
        # Detect intent patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)  # Use original case for names
                if match:
                    result['intent'] = intent_type
                    result['query_type'] = intent_type
                    result['confidence'] = 0.8
                    
                    # Extract entities from match groups
                    groups = match.groups()
                    if groups:
                        entities = [g for g in groups if g and len(g) > 2]
                        if entities:
                            # For biographical, preserve original case
                            if intent_type == 'biographical':
                                result['entity'] = entities[-1] if len(entities) > 1 else entities[0]
                                result['is_person_query'] = True
                                result['should_search_web'] = True
                                result['response_priority'] = 'identity'
                            else:
                                result['entity'] = entities[0]
                            result['entities'] = entities
                    
                    break
        
        # Extract main topic/entity
        if not result['entity']:
            words = query_lower.split()
            # Filter out common words
            common_words = {'what', 'is', 'are', 'the', 'a', 'an', 'how', 'to', 'do', 'you', 'tell', 'me', 'about', 'who', 'was'}
            meaningful_words = [w for w in words if w not in common_words and len(w) > 2]
            if meaningful_words:
                result['entity'] = meaningful_words[0]
                result['entities'] = meaningful_words[:3]
        
        # Build expanded query for better matching
        expanded = query_lower
        if result['entity']:
            # For specific queries, add context
            if result['intent'] == 'definition' and result['entity']:
                expanded = f"definition of {result['entity']} what is {result['entity']}"
            elif result['intent'] == 'biographical' and result['entity']:
                expanded = f"{result['entity']} biography who is {result['entity']}"
            elif result['intent'] == 'programming' and result['entity']:
                # Keep original programming context
                expanded = query_lower
        
        result['expanded_query'] = expanded
        
        # Determine if strict matching is required
        if result['intent'] in ['philosophical', 'definition', 'biographical']:
            result['strict_match_required'] = True
        
        # For biographical queries, always search web for accurate info
        if result['intent'] == 'biographical' or result['is_person_query']:
            result['should_search_web'] = True
        
        # For definition queries about general scientific/academic topics, force web search
        # to avoid matching specialized/technical variants
        if result['intent'] == 'definition' and result['entity']:
            general_science_topics = ['physics', 'chemistry', 'biology', 'mathematics', 'science', 
                                     'philosophy', 'history', 'geography', 'astronomy', 'geology',
                                     'cricket', 'football', 'tennis', 'basketball']  # Added sports
            if result['entity'].lower() in general_science_topics:
                # Check if query is general (not specific like "game physics" or "quantum physics")
                query_words = query_lower.split()
                if len(query_words) <= 4:  # Short, general query like "what is physics"
                    # Only force search if it's truly general (no modifiers)
                    modifiers = ['game', 'quantum', 'classical', 'modern', 'applied', 'theoretical']
                    if not any(mod in query_lower for mod in modifiers):
                        result['should_search_web'] = True
                        result['strict_match_required'] = True
        
        return result
    
    def is_ambiguous_match(self, query: str, knowledge_content: str) -> bool:
        """Check if a knowledge match might be ambiguous/wrong"""
        query_lower = query.lower()
        content_lower = knowledge_content.lower()
        
        # Special case: "what is physics" should NOT match "game physics"
        if 'physics' in query_lower and 'what' in query_lower and len(query_lower.split()) <= 4:
            # If query is about general physics but content is about game physics
            if any(variant in content_lower for variant in ['game physics', 'physics engine', 'physics simulation', 'physics-based']):
                # Only reject if the query doesn't mention games/simulation
                if not any(word in query_lower for word in ['game', 'simulation', 'engine', 'video', 'computer']):
                    return True  # Wrong match - general physics vs game physics
        
        # Check for ambiguous word overlaps
        for ambiguous, variants in self.ambiguous_words.items():
            if ambiguous in query_lower:
                # If query has "life" but content has "lifelong" or "lifetime", might be wrong match
                for variant in variants:
                    if variant in content_lower and ambiguous not in content_lower:
                        # Check if context makes sense
                        if variant not in query_lower:
                            return True  # Possible ambiguous match
        
        # Check for very different topics
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        # Calculate overlap
        common_words = query_words.intersection(content_words)
        # Remove very common words
        common_words = {w for w in common_words if len(w) > 3}
        
        # If very few common words, might be wrong match
        if len(common_words) < 2 and len(query_words) > 3:
            return True
        
        return False
    
    def calculate_relevance_score(self, query: str, knowledge_title: str, knowledge_content: str) -> float:
        """Calculate relevance score between query and knowledge item"""
        query_lower = query.lower()
        title_lower = knowledge_title.lower()
        content_lower = knowledge_content.lower()
        
        score = 0.0
        
        # Title matches are very important
        if title_lower in query_lower or query_lower in title_lower:
            score += 0.5
        
        # Check word overlap
        query_words = set(w for w in query_lower.split() if len(w) > 2)
        title_words = set(w for w in title_lower.split() if len(w) > 2)
        content_words = set(w for w in content_lower.split() if len(w) > 2)
        
        # Title word matches
        title_overlap = query_words.intersection(title_words)
        score += len(title_overlap) * 0.2
        
        # Content word matches (weighted less)
        content_overlap = query_words.intersection(content_words)
        score += len(content_overlap) * 0.1
        
        # Check for exact phrase matches
        query_phrases = [query_lower]
        if ' ' in query_lower:
            # Add individual meaningful words
            meaningful = [w for w in query_lower.split() if len(w) > 3]
            query_phrases.extend(meaningful)
        
        for phrase in query_phrases:
            if phrase in title_lower:
                score += 0.3
            if phrase in content_lower[:200]:  # First 200 chars
                score += 0.2
        
        # Penalize ambiguous matches
        if self.is_ambiguous_match(query, knowledge_content):
            score *= 0.3  # Heavily penalize
        
        return min(score, 1.0)  # Cap at 1.0


# Global instance
_query_intent_analyzer = None

def get_query_intent_analyzer():
    """Get or create global query intent analyzer instance"""
    global _query_intent_analyzer
    if _query_intent_analyzer is None:
        _query_intent_analyzer = QueryIntentAnalyzer()
    return _query_intent_analyzer

