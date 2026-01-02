"""
Brain Connector - Connects Thor's responses to the brain keyword system
"""
import os
import json
from pathlib import Path
from services.query_intent_analyzer import get_query_intent_analyzer
from services.semantic_relevance import get_semantic_scorer
import re
from collections import defaultdict

class BrainConnector:
    """Connects AI responses to brain keyword knowledge"""

    def __init__(self, brain_dir="brain"):
        self.brain_dir = brain_dir
        self.semantic_scorer = get_semantic_scorer()

    def _enhanced_semantic_search(self, query: str, query_intent: dict) -> list:
        """
        Enhanced semantic search that goes beyond exact keyword matching.
        Uses semantic similarity and query expansion.
        """
        query_lower = query.lower()
        expanded_terms = self._expand_search_terms(query, query_intent)

        all_knowledge = []
        relevance_scores = []

        # Search through all brain files
        for letter_dir in os.listdir(self.brain_dir):
            letter_path = os.path.join(self.brain_dir, letter_dir)
            if os.path.isdir(letter_path):
                keywords_file = os.path.join(letter_path, "keywords.json")
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)

                        for knowledge in data.get('knowledge', []):
                            content = knowledge.get('content', '')
                            title = knowledge.get('title', '')

                            # Calculate semantic relevance
                            semantic_score = self.semantic_scorer.calculate_semantic_score(
                                query, knowledge, query_intent
                            )

                            # Calculate keyword relevance
                            keyword_score = self._calculate_keyword_relevance(
                                query_lower, expanded_terms, data.get('keywords', [])
                            )

                            # Calculate content relevance
                            content_relevance = self._calculate_content_relevance(
                                query_lower, expanded_terms, content, title
                            )

                            # Combined score
                            total_score = (semantic_score * 0.5 +
                                         keyword_score * 0.3 +
                                         content_relevance * 0.2)

                            if total_score > 0.1:  # Threshold for relevance
                                relevance_scores.append((total_score, knowledge))

                    except Exception as e:
                        print(f"[Brain Connector] Error reading {keywords_file}: {e}")

        # Sort by relevance and return top results
        relevance_scores.sort(key=lambda x: x[0], reverse=True)

        # Filter out music/video content unless explicitly requested
        filtered_results = []
        for score, knowledge in relevance_scores[:10]:
            if not self._is_music_video_content(knowledge, query, query_intent):
                filtered_results.append(knowledge)

        return filtered_results

    def _expand_search_terms(self, query: str, query_intent: dict) -> list:
        """Expand search terms based on query type and intent."""
        expanded = [query]
        query_lower = query.lower()

        # Add synonyms and related terms
        synonyms = {
            'python': ['programming', 'code', 'script', 'language'],
            'javascript': ['js', 'web development', 'frontend', 'scripting'],
            'machine learning': ['ml', 'ai', 'artificial intelligence', 'algorithms'],
            'database': ['data', 'storage', 'sql', 'mongodb'],
            'api': ['interface', 'rest', 'web service', 'integration']
        }

        for term, related in synonyms.items():
            if term in query_lower:
                expanded.extend(related)
                break

        # Add query-type specific expansions
        intent = query_intent.get('intent', '')
        if intent == 'biographical':
            expanded.extend(['person', 'life', 'career', 'background'])
        elif intent == 'technical':
            expanded.extend(['implementation', 'usage', 'example', 'guide'])
        elif intent == 'definition':
            expanded.extend(['meaning', 'explanation', 'concept'])

        return list(set(expanded))  # Remove duplicates

    def _calculate_keyword_relevance(self, query: str, expanded_terms: list, keywords: list) -> float:
        """Calculate relevance based on keyword matches."""
        score = 0.0
        query_words = set(query.split())
        keyword_set = set(k.lower() for k in keywords)

        # Exact matches get highest score
        exact_matches = query_words & keyword_set
        score += len(exact_matches) * 0.8

        # Partial matches (expanded terms)
        for term in expanded_terms:
            term_words = set(term.split())
            partial_matches = term_words & keyword_set
            score += len(partial_matches) * 0.4

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_content_relevance(self, query: str, expanded_terms: list, content: str, title: str) -> float:
        """Calculate relevance based on content similarity."""
        score = 0.0
        text_to_check = (content + ' ' + title).lower()

        # Count term occurrences in content
        for term in expanded_terms:
            if term.lower() in text_to_check:
                score += 0.3

        # Bonus for query terms appearing multiple times
        query_words = query.split()
        for word in query_words:
            count = text_to_check.count(word.lower())
            score += min(count * 0.1, 0.3)  # Cap per word

        return min(score, 1.0)  # Cap at 1.0

    def _multi_hop_reasoning(self, initial_knowledge: list, query: str) -> list:
        """
        Perform multi-hop reasoning by following related topics in the brain.
        """
        if not initial_knowledge:
            return initial_knowledge

        extended_knowledge = initial_knowledge.copy()
        visited_topics = set()

        # Extract related topics from initial knowledge
        for item in initial_knowledge:
            content = item.get('content', '')
            title = item.get('title', '')

            # Find related terms/concepts in the content
            related_terms = self._extract_related_terms(content + ' ' + title)

            for term in related_terms:
                if term not in visited_topics and len(term) > 3:
                    visited_topics.add(term)

                    # Search for knowledge related to this term
                    related_knowledge = self.get_relevant_knowledge(f"tell me about {term}")
                    extended_knowledge.extend(related_knowledge[:2])  # Limit per term

        # Remove duplicates and limit total results
        seen_titles = set()
        deduplicated = []
        for item in extended_knowledge:
            title = item.get('title', '')
            if title not in seen_titles:
                seen_titles.add(title)
                deduplicated.append(item)

        return deduplicated[:15]  # Reasonable limit

    def _extract_related_terms(self, text: str) -> list:
        """Extract potentially related terms from text."""
        # Simple extraction of noun phrases and important terms
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

        # Filter out common words
        common_words = {
            'that', 'this', 'with', 'from', 'they', 'have', 'been', 'were',
            'their', 'there', 'these', 'those', 'which', 'where', 'when',
            'would', 'could', 'should', 'about', 'after', 'before'
        }

        filtered_words = [w for w in words if w not in common_words]

        # Return most frequent terms as potentially related
        word_freq = defaultdict(int)
        for word in filtered_words:
            word_freq[word] += 1

        return [word for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]]

    def _is_music_video_content(self, knowledge_item: dict, query: str, query_intent: dict = None) -> bool:
        """Comprehensive detection of music/video content with enhanced filtering"""
        title = knowledge_item.get('title', '').lower()
        content = knowledge_item.get('content', '').lower()
        source = knowledge_item.get('source', '').lower()

        # Comprehensive music indicators (expanded)
        music_indicators = [
            # Direct music terms
            'music video', 'song', 'youtube', 'spotify', 'official music',
            'lyrics', 'album', 'artist', 'musical', 'singer', 'band',
            'concert', 'live performance', 'music festival', 'playlist',
            'track', 'single', 'ep', 'lp', 'vinyl', 'cd', 'mp3', 'wav',
            'guitar', 'piano', 'drums', 'bass', 'orchestra', 'chorus',
            'melody', 'harmony', 'rhythm', 'beat', 'tempo', 'genre',
            'rock', 'pop', 'jazz', 'classical', 'hip hop', 'rap', 'country',
            'blues', 'reggae', 'electronic', 'dance', 'folk', 'indie',

            # Artist/performer terms
            'grammy', 'billboard', 'mtv', 'vmas', 'american idol',
            'the voice', 'eurovision', 'brit awards', 'oscars',

            # Music-related activities
            'karaoke', 'dj', 'remix', 'cover', 'original', 'feat.',
            'featuring', 'produced by', 'written by', 'composed by'
        ]

        # Comprehensive video indicators (expanded)
        video_indicators = [
            # Video platforms and terms
            'video', 'youtube video', 'vimeo', 'tiktok', 'instagram reels',
            'snapchat', 'twitch', 'stream', 'streaming', 'channel',
            'subscribe', 'views', 'likes', 'comments', 'viral',

            # Video content types
            'vlog', 'tutorial video', 'video content', 'film', 'movie',
            'cinema', 'theater', 'documentary', 'short film', 'trailer',
            'clip', 'episode', 'season', 'series', 'netflix', 'hulu',
            'amazon prime', 'disney+', 'hbo', 'showtime', 'cbs', 'nbc',
            'abc', 'fox', 'cnn', 'bbc', 'espn', 'mtv', 'vh1',

            # Entertainment industry
            'hollywood', 'bollywood', 'tollywood', 'award', 'nomination',
            'red carpet', 'premiere', 'festival', 'cannes', 'sundance',
            'tiff', 'venice', 'berlin', 'oscar', 'golden globe', 'emmy',

            # Video production terms
            'director', 'producer', 'actor', 'actress', 'casting',
            'screenplay', 'script', 'filming', 'editing', 'post-production'
        ]

        # Check if query explicitly asks about music/video/entertainment
        is_music_video_intent = False
        if query_intent and query_intent.get('hints'):
            is_music_video_intent = query_intent['hints'].get('is_music_video_intent', False)

        # Enhanced query analysis for explicit music/video intent
        query_lower = query.lower()
        direct_music_video_query = any(term in query_lower for term in [
            # Music terms
            'song', 'music', 'youtube', 'listen', 'play', 'sing', 'musical',
            'artist', 'album', 'concert', 'band', 'singer', 'lyrics', 'track',
            'playlist', 'spotify', 'melody', 'harmony', 'rhythm', 'genre',
            'rock', 'pop', 'jazz', 'classical', 'hip hop', 'rap', 'country',

            # Video terms
            'video', 'watch', 'stream', 'movie', 'film', 'cinema', 'tv show',
            'series', 'episode', 'netflix', 'hulu', 'youtube', 'tiktok',
            'instagram', 'vlog', 'trailer', 'clip', 'channel', 'subscribe'
        ])

        # Check for entertainment/media intent words
        entertainment_intent_words = [
            'recommend', 'suggest', 'what should i', 'best', 'favorite',
            'tell me about', 'show me', 'play me', 'listen to', 'watch'
        ]
        has_entertainment_intent = any(intent_word in query_lower for intent_word in entertainment_intent_words)

        # If query shows clear music/video/entertainment intent, allow content
        if is_music_video_intent or direct_music_video_query or (has_entertainment_intent and direct_music_video_query):
            return False  # Not filtering, allow it

        # Enhanced content analysis - check multiple sections of content
        content_sections = [
            content[:200],      # Beginning of content (most important)
            content[200:500],   # Middle section
            content[-200:] if len(content) > 200 else content,  # End of content
            title,              # Title is very important
            source              # Source can indicate entertainment focus
        ]

        # Check for strong music/video signals in content
        music_score = 0
        video_score = 0

        for section in content_sections:
            if not section:
                continue

            # Count music indicators in this section
            section_music_count = sum(1 for indicator in music_indicators if indicator in section)
            music_score += section_music_count

            # Count video indicators in this section
            section_video_count = sum(1 for indicator in video_indicators if indicator in section)
            video_score += section_video_count

        # Additional checks for entertainment-focused content
        is_entertainment_focused = (
            'entertainment' in title or
            'celebrity' in title or
            'hollywood' in title or
            'music industry' in title or
            'film industry' in title or
            source in ['youtube', 'spotify', 'netflix', 'tiktok', 'instagram'] or
            any(platform in content[:100] for platform in ['youtube.com', 'spotify.com', 'netflix.com'])
        )

        # Scoring thresholds for filtering
        # Higher threshold for title (title is more important)
        title_music_threshold = 2
        title_video_threshold = 2
        content_music_threshold = 3
        content_video_threshold = 3

        title_music_count = sum(1 for indicator in music_indicators if indicator in title)
        title_video_count = sum(1 for indicator in video_indicators if indicator in title)

        # Filter if content shows strong music/video/entertainment signals
        is_music_content = (
            title_music_count >= title_music_threshold or
            music_score >= content_music_threshold or
            is_entertainment_focused
        )

        is_video_content = (
            title_video_count >= title_video_threshold or
            video_score >= content_video_threshold or
            is_entertainment_focused
        )

        # Filter out music/video/entertainment content unless explicitly requested
        return is_music_content or is_video_content

    def get_relevant_knowledge(self, message):
        """Enhanced knowledge retrieval with semantic search and multi-hop reasoning"""
        # Use query intent analyzer for better understanding
        intent_analyzer = get_query_intent_analyzer()
        query_intent = intent_analyzer.analyze(message)

        # For philosophical queries like "what's life", force web search
        if query_intent.get('should_search_web') or query_intent.get('intent') == 'philosophical':
            # Return empty to force web search
            return []

        # Try enhanced semantic search first
        semantic_results = self._enhanced_semantic_search(message, query_intent)

        # Apply multi-hop reasoning to find related knowledge
        enhanced_results = self._multi_hop_reasoning(semantic_results, message)

        # If we got good semantic results, use them; otherwise fall back to keyword search
        if enhanced_results and len(enhanced_results) >= 3:
            return enhanced_results
        else:
        # Fall back to original keyword-based search
        return self._keyword_based_search(message)

    def _keyword_based_search(self, message):
        """Original keyword-based search method (fallback)."""
        # Use query intent analyzer for better understanding
        intent_analyzer = get_query_intent_analyzer()
        query_intent = intent_analyzer.analyze(message)

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
            # Filter out music/video content unless explicitly requested
            filtered_result = [(score, item) for score, item in result[:5]
                              if not self._is_music_video_content(item, message, query_intent)]
            return [item for _, item in filtered_result]  # Return top 5 most relevant

        # Fallback to original scoring
        # Filter out music/video content unless explicitly requested
        filtered_items = [(k[0], k[1]) for k in scored_items[:5]
                         if not self._is_music_video_content(k[1], message, query_intent)]
        return [item for _, item in filtered_items]
    
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

