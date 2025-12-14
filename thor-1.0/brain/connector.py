"""
Brain Connector - Connects Thor's responses to the brain keyword system
"""
import os
import json
from pathlib import Path
from services.query_intent_analyzer import get_query_intent_analyzer
from services.semantic_relevance import get_semantic_scorer

class BrainConnector:
    """Connects AI responses to brain keyword knowledge"""
    
    def __init__(self, brain_dir="brain"):
        self.brain_dir = brain_dir
    
    def get_relevant_knowledge(self, message):
        """Get relevant knowledge from brain based on message keywords"""
        # Use query intent analyzer for better understanding
        intent_analyzer = get_query_intent_analyzer()
        query_intent = intent_analyzer.analyze(message)
        
        # For philosophical queries like "what's life", force web search
        if query_intent.get('should_search_web') or query_intent.get('intent') == 'philosophical':
            # Return empty to force web search
            return []
        
        message_lower = message.lower()
        words = message_lower.split()
        
        # Detect recipe/cooking queries
        recipe_patterns = ['how to make', 'recipe for', 'how do you make', 'how do i make', 
                          'recipe', 'cook', 'cooking', 'dish', 'ingredients']
        is_recipe_query = any(pattern in message_lower for pattern in recipe_patterns)
        
        # Expand abbreviations (js -> javascript, py -> python)
        lang_expansions = {
            'js': 'javascript',
            'py': 'python',
            'ts': 'typescript',
            'rb': 'ruby',
            'cpp': 'c++',
            'cs': 'c#'
        }
        
        # Replace abbreviations with full names
        expanded_words = []
        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:()[]{}')
            if clean_word.lower() in lang_expansions:
                expanded_words.append(lang_expansions[clean_word.lower()])
                expanded_words.append(clean_word)  # Keep original too
            else:
                expanded_words.append(word)
        words = expanded_words
        message_lower = ' '.join(words).lower()
        
        # Filter out very common words that cause false matches
        common_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'who', 'what', 'where', 'when', 'why', 'how', 'which', 'whose',
            'and', 'or', 'but', 'if', 'then', 'else', 'for', 'with', 'from',
            'to', 'of', 'in', 'on', 'at', 'by', 'about', 'into', 'through',
            'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should',
            'now', 'make', 'makes', 'making', 'tell', 'me', 'explain', 'about'  # Added common question words
        }
        
        # Filter words - only use meaningful words (length > 2 and not common)
        meaningful_words = [w.strip('.,!?;:()[]{}') for w in words if len(w.strip('.,!?;:()[]{}')) > 2 and w.strip('.,!?;:()[]{}').lower() not in common_words]
        
        # For queries like "js functions", prioritize finding "javascript functions" not just "javascript"
        # Group related words together
        programming_langs = ['javascript', 'python', 'java', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust']
        tech_keywords = ['functions', 'classes', 'objects', 'arrays', 'variables', 'loops', 'conditions', 
                        'methods', 'constructors', 'prototypes', 'modules', 'packages']
        
        # Build topic phrases - combine language + keyword if both present
        topic_phrases = []
        for lang in programming_langs:
            lang_in_msg = lang in message_lower
            lang_abbrev_in_msg = any(lang.startswith(word) or word == lang[:2] for word in meaningful_words if len(word) <= 3)
            if lang_in_msg or lang_abbrev_in_msg:
                for keyword in tech_keywords:
                    if keyword in message_lower:
                        # Use full language name, not abbreviation
                        topic_phrases.append(f"{lang} {keyword}")
                        break
        
        # Extract the main topic (likely the dish name) - usually the last meaningful word or phrase
        # For "how to make pasta", "pasta" is the main topic
        main_topic = None
        if is_recipe_query and meaningful_words:
            # For recipe queries, prioritize the last meaningful word(s) as the dish name
            # Skip common action words like "make"
            action_words = {'make', 'cook', 'prepare', 'bake', 'fry', 'grill'}
            topic_words = [w for w in meaningful_words if w not in action_words]
            if topic_words:
                main_topic = topic_words[-1]  # Usually the dish name comes last
                # Also try combining last 2 words for multi-word dish names
                if len(topic_words) > 1:
                    main_topic_phrase = ' '.join(topic_words[-2:])
        
        # If message is too short or only has common words, return empty
        if len(meaningful_words) == 0:
            return []
        
        relevant_knowledge = []
        seen_titles = set()
        
        # Priority: search for main topic first, then other meaningful words
        search_order = []
        if main_topic:
            search_order.append(main_topic)
        # Add other meaningful words that aren't the main topic
        for word in meaningful_words:
            if word != main_topic and word not in search_order:
                search_order.append(word)
        
        # If no main topic identified, use original order
        if not search_order:
            search_order = meaningful_words
        
        # Search through brain structure using prioritized words
        for word in search_order:
            if word and word[0].isalpha():
                letter = word[0].upper()
                keywords_file = os.path.join(self.brain_dir, letter, "keywords.json")
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                        
                        # Check if word is a keyword
                        if word in data.get('keywords', []):
                            # Get knowledge for this keyword
                            for knowledge in data.get('knowledge', []):
                                content = knowledge.get('content', '').lower()
                                title = knowledge.get('title', '').lower()
                                source = knowledge.get('source', '')
                                
                                # Filter out greeting patterns and metadata
                                if 'response pattern for greeting' in content:
                                    continue
                                if 'use appropriate greeting' in content:
                                    continue
                                if source == 'greetings_handler':
                                    continue
                                if content.startswith('response pattern'):
                                    continue
                                
                                # For recipe queries, filter out non-cooking content
                                if is_recipe_query:
                                    # Reject if content is clearly about machine learning, programming, etc.
                                    cooking_keywords = ['recipe', 'cook', 'ingredient', 'dish', 'food', 'bake', 
                                                       'fry', 'grill', 'oven', 'stove', 'kitchen', 'serve', 
                                                       'taste', 'flavor', 'meal']
                                    tech_keywords = ['machine learning', 'algorithm', 'programming', 'code', 
                                                    'software', 'computer', 'ai', 'artificial intelligence']
                                    
                                    # If content has tech keywords but no cooking keywords, skip it
                                    has_cooking = any(ck in content for ck in cooking_keywords)
                                    has_tech = any(tk in content for tk in tech_keywords)
                                    
                                    if has_tech and not has_cooking:
                                        continue
                                    
                                    # For recipe queries, require the main topic (dish name) to appear in content or title
                                    if main_topic and main_topic not in content and main_topic not in title:
                                        continue
                                
                                # Check relevance - content should contain at least one meaningful word
                                # For recipe queries, require stronger relevance (main topic must match)
                                if is_recipe_query and main_topic:
                                    # Must contain the main topic
                                    if main_topic not in content and main_topic not in title:
                                        continue
                                else:
                                    # General relevance check - require multiple keyword matches for better precision
                                    matching_words = [mw for mw in meaningful_words[:5] if mw in content or mw in title]
                                    
                                    # For topic phrases (like "javascript functions"), require phrase match
                                    phrase_match = False
                                    if topic_phrases:
                                        for phrase in topic_phrases:
                                            if phrase in content or phrase in title:
                                                phrase_match = True
                                                break
                                    
                                    # Require at least 2 word matches OR a phrase match for better relevance
                                    if not phrase_match and len(matching_words) < 2 and len(meaningful_words) > 1:
                                        continue
                                    
                                    # If only one word, it must be in title or strongly in content
                                    if len(meaningful_words) == 1:
                                        if meaningful_words[0] not in title and meaningful_words[0] not in content[:100]:
                                            continue
                                
                                if title and title not in seen_titles:
                                    seen_titles.add(title)
                                    # Score by relevance - prioritize main topic matches and phrase matches
                                    score = 1
                                    if main_topic and (main_topic in content or main_topic in title):
                                        score = 2
                                    # Boost score for topic phrase matches
                                    if topic_phrases:
                                        for phrase in topic_phrases:
                                            if phrase in content or phrase in title:
                                                score = 3
                                                break
                                    relevant_knowledge.append((score, knowledge))
                    except:
                        continue
        
        # Sort by relevance score (higher first), then return knowledge items
        # Filter out any non-tuple items and ensure we have valid tuples
        valid_knowledge = []
        for item in relevant_knowledge:
            if isinstance(item, tuple) and len(item) >= 2:
                valid_knowledge.append(item)
            elif isinstance(item, dict):
                # If it's a dict, wrap it in a tuple with default score
                valid_knowledge.append((1, item))
        
        valid_knowledge.sort(key=lambda x: x[0], reverse=True)
        # k is already the knowledge dict (second element of tuple), not a tuple itself
        scored_items = [(score, k) for score, k in valid_knowledge]
        
        # Use semantic relevance scorer to filter and re-score for better accuracy
        semantic_scorer = get_semantic_scorer()
        final_scored = semantic_scorer.filter_knowledge_by_relevance(
            message,
            [item[1] for item in scored_items[:10]],  # Top 10 candidates
            query_intent,
            min_score=0.2  # Minimum relevance threshold
        )
        
        # If we have semantic scores, use those; otherwise use original scores
        if final_scored:
            # Combine scores (weighted average: 60% semantic, 40% keyword-based)
            score_map = {id(item[1]): item[0] for item in final_scored}
            result = []
            for orig_score, item in scored_items[:10]:
                item_id = id(item)
                if item_id in score_map:
                    # Weighted: 60% semantic, 40% keyword-based
                    combined_score = (score_map[item_id] * 0.6) + (min(orig_score / 3.0, 1.0) * 0.4)
                    result.append((combined_score, item))
            result.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in result[:5]]  # Return top 5 most relevant
        
        # Fallback to original scoring
        return [k[1] for k in scored_items[:5]]
    
    def enhance_response(self, message, base_response):
        """Enhance response with knowledge from brain"""
        knowledge = self.get_relevant_knowledge(message)
        
        if knowledge:
            # Filter out greeting patterns and metadata - only use actual content
            filtered_knowledge = []
            for k in knowledge:
                content = k.get('content', '')
                title = k.get('title', '')
                source = k.get('source', '')
                
                # Skip greeting patterns and metadata
                if 'Response pattern for greeting' in content or 'Use appropriate greeting' in content:
                    continue
                if source == 'greetings_handler':
                    continue
                if len(content) < 20:  # Skip very short content
                    continue
                
                # Only use actual knowledge content
                if content and not content.startswith('Response pattern'):
                    filtered_knowledge.append(k)
            
            if filtered_knowledge:
                # Add context from brain
                context_parts = []
                for k in filtered_knowledge[:2]:  # Use top 2 relevant pieces
                    content = k.get('content', '').strip()
                    # Clean up content - remove incomplete sentences
                    if content and len(content) > 20:
                        # Ensure complete sentences
                        if not content.endswith(('.', '!', '?', '...')):
                            # Try to find last complete sentence
                            last_period = content.rfind('.')
                            if last_period > len(content) * 0.5:  # If period is in second half
                                content = content[:last_period + 1]
                        context_parts.append(content[:250])  # Limit length
                
                if context_parts:
                    # Join naturally
                    enhanced = base_response
                    if len(context_parts) == 1:
                        enhanced += f"\n\n{context_parts[0]}"
                    else:
                        enhanced += f"\n\n{context_parts[0]} {context_parts[1]}"
                    return enhanced
        
        return base_response
    
    def get_keywords_for_message(self, message):
        """Extract keywords that match brain structure"""
        message_lower = message.lower()
        words = message_lower.split()
        
        matched_keywords = []
        
        for word in words:
            if word and word[0].isalpha():
                letter = word[0].upper()
                keywords_file = os.path.join(self.brain_dir, letter, "keywords.json")
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                        
                        if word in data.get('keywords', []):
                            matched_keywords.append(word)
                    except:
                        continue
        
        return matched_keywords

