"""
Semantic Relevance Scorer - Advanced intelligence for scoring knowledge relevance
Uses multiple factors to determine how relevant knowledge is to a query
"""
from typing import Dict, List, Tuple, Optional
import re


class SemanticRelevanceScorer:
    """Scores knowledge items based on semantic relevance to queries"""
    
    def __init__(self):
        # Topic categories and their keywords
        self.topic_categories = {
            'philosophy': ['life', 'existence', 'reality', 'consciousness', 'meaning', 'purpose', 
                          'truth', 'ethics', 'morality', 'philosophy', 'wisdom', 'enlightenment'],
            'programming': ['code', 'function', 'class', 'variable', 'syntax', 'programming', 
                           'javascript', 'python', 'java', 'typescript', 'algorithm', 'software'],
            'cooking': ['recipe', 'cook', 'ingredient', 'dish', 'food', 'bake', 'fry', 'grill', 
                       'kitchen', 'cuisine', 'meal', 'taste', 'flavor'],
            'science': ['science', 'research', 'experiment', 'hypothesis', 'theory', 'discovery',
                       'physics', 'chemistry', 'biology', 'mathematics'],
            'learning': ['learning', 'education', 'study', 'knowledge', 'teach', 'lesson', 
                        'course', 'tutorial', 'learn', 'student']
        }
        
        # Word similarity mappings (for common confusions)
        self.similarity_map = {
            'life': ['existence', 'being', 'living'],
            'learning': ['education', 'studying', 'teaching'],
            'make': ['create', 'build', 'construct']
        }
    
    def classify_topic(self, text: str) -> List[str]:
        """Classify text into topic categories"""
        text_lower = text.lower()
        categories = []
        
        for category, keywords in self.topic_categories.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                categories.append((category, matches))
        
        # Sort by number of matches
        categories.sort(key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in categories[:3]]  # Top 3 categories
    
    def calculate_semantic_score(
        self, 
        query: str, 
        knowledge_item: Dict,
        query_intent: Optional[Dict] = None
    ) -> float:
        """Calculate semantic relevance score"""
        title = knowledge_item.get('title', '').lower()
        content = knowledge_item.get('content', '').lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # 1. Exact phrase match in title (highest weight)
        if query_lower in title or title in query_lower:
            score += 0.5
        
        # 2. Topic category matching
        query_categories = self.classify_topic(query)
        knowledge_categories = self.classify_topic(f"{title} {content[:200]}")
        
        category_overlap = set(query_categories).intersection(set(knowledge_categories))
        if category_overlap:
            score += 0.3
        
        # 3. Word-level matching
        query_words = set(w for w in query_lower.split() if len(w) > 2)
        title_words = set(w for w in title.split() if len(w) > 2)
        content_words = set(w for w in content[:500].split() if len(w) > 2)
        
        # Title word matches
        title_matches = query_words.intersection(title_words)
        score += len(title_matches) * 0.15
        
        # Content word matches (weighted less)
        content_matches = query_words.intersection(content_words)
        score += len(content_matches) * 0.05
        
        # 4. Intent-based scoring
        if query_intent:
            intent = query_intent.get('intent', 'general')
            entity = query_intent.get('entity', '')
            is_person_query = query_intent.get('is_person_query', False)
            response_priority = query_intent.get('response_priority', 'general')
            
            # For biographical queries (Who is X?), prioritize identity over trivia
            if intent == 'biographical' or is_person_query:
                entity_lower = entity.lower() if entity else ''
                # Check if person's name is prominent
                if entity_lower:
                    name_parts = entity_lower.split()
                    last_name = name_parts[-1] if name_parts else entity_lower
                    
                    # Name must appear in title or first 100 chars
                    if last_name in title or last_name in content[:100]:
                        score += 0.3
                        
                        # BOOST for identity information (who they ARE)
                        identity_patterns = [
                            r'\b(is|was)\s+(an?\s+)?(indian|american|british|[\w]+)\s+',
                            r'\b(actor|actress|cricketer|player|singer|politician|scientist|writer|musician|director)',
                            r'\bborn\s+\d',
                            r'\bknown\s+for\b',
                            r'\bfamous\s+for\b',
                        ]
                        for pattern in identity_patterns:
                            if re.search(pattern, content[:300]):
                                score += 0.2
                                break
                        
                        # PENALIZE trivia/anecdotes if identity info is required
                        if response_priority == 'identity':
                            trivia_patterns = [
                                r'\b(once|anecdote|story|revealed|shared|failed|exam)\b',
                                r'\bdid\s+you\s+know\b',
                                r'\binteresting\s+fact\b',
                            ]
                            for pattern in trivia_patterns:
                                if re.search(pattern, content[:200]):
                                    score *= 0.4  # Heavily penalize trivia
                                    break
                    else:
                        score *= 0.3  # Penalize if person not mentioned early
            
            # For definition queries, entity must be in title or start of content
            elif intent == 'definition' and entity:
                if entity in title or entity in content[:100]:
                    score += 0.2
                else:
                    score *= 0.5  # Penalize if entity not found
            
            # For philosophical queries, require strict topic match
            elif intent == 'philosophical':
                if 'life' in query_lower:
                    # Content must be about life/philosophy, not learning/education
                    if any(word in content[:200] for word in ['life', 'existence', 'meaning', 'purpose', 'reality']):
                        score += 0.3
                    else:
                        # Heavy penalty for off-topic content
                        if any(word in content[:200] for word in ['learning', 'education', 'study', 'teach']):
                            score *= 0.1  # Almost completely reject
        
        # 5. Position-based scoring (earlier mentions are more relevant)
        query_meaningful = [w for w in query_lower.split() if len(w) > 3]
        for word in query_meaningful[:3]:  # Top 3 words
            if word in title:
                score += 0.1
            elif word in content[:100]:
                score += 0.05
            elif word in content:
                score += 0.02
        
        # 6. Penalize music/video content for non-music queries
        if self._is_music_video_content(query, title, content, query_intent):
            score *= 0.1  # Heavy penalty for music/video content

        # 7. Reject obviously wrong matches
        if self._is_wrong_match(query_lower, title, content):
            return 0.0

        return min(score, 1.0)
    
    def _is_wrong_match(self, query: str, title: str, content: str) -> bool:
        """Check if this is clearly a wrong match"""
        # Check for promotional/ad copy content - reject it
        promotional_indicators = [
            'learn everything you need to know',
            'discover everything about',
            'find out everything about',
            'get started with',
            'click here',
            'visit our website',
            'sign up',
            'subscribe',
            'join us'
        ]
        
        content_lower = content[:200].lower()
        if any(indicator in content_lower for indicator in promotional_indicators):
            # If it's mostly promotional, reject it
            if any(indicator in content_lower[:100] for indicator in promotional_indicators):
                return True
        
        # Check for "what is physics" matching "game physics"
        if 'physics' in query.lower() and 'what' in query.lower() and len(query.split()) <= 4:
            # General physics query
            if any(term in content.lower() for term in ['game physics', 'physics engine', 'physics simulation']):
                # Only reject if query doesn't mention games
                if not any(word in query.lower() for word in ['game', 'simulation', 'engine', 'video', 'computer']):
                    return True
        
        # Check for philosophical query but learning content
        if 'life' in query and ('life' not in title and 'life' not in content[:200]):
            if any(word in content[:200] for word in ['learning', 'education', 'study', 'teach', 'student']):
                if 'life' not in content[:500]:  # Life not mentioned at all
                    return True
        
        # Check for very different topics
        query_cats = self.classify_topic(query)
        knowledge_cats = self.classify_topic(f"{title} {content[:300]}")

        if query_cats and knowledge_cats:
            # If completely different categories
            if not set(query_cats).intersection(set(knowledge_cats)):
                # But allow if it's a general query
                if len(query.split()) < 4:  # Short queries might match different topics
                    return False
                return True

        # Check for music/video content when query isn't about music
        if self._is_music_video_content(query, title, content, query_intent):
            return True

        return False

    def _is_music_video_content(self, query: str, title: str, content: str, query_intent: dict = None) -> bool:
        """Comprehensive detection of music/video content with enhanced filtering"""
        title_lower = title.lower()
        content_lower = content.lower()

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
            content_lower[:200],      # Beginning of content (most important)
            content_lower[200:500],   # Middle section
            content_lower[-200:] if len(content_lower) > 200 else content_lower,  # End of content
            title_lower              # Title is very important
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

        # Scoring thresholds for filtering
        # Higher threshold for title (title is more important)
        title_music_threshold = 2
        title_video_threshold = 2
        content_music_threshold = 3
        content_video_threshold = 3

        title_music_count = sum(1 for indicator in music_indicators if indicator in title_lower)
        title_video_count = sum(1 for indicator in video_indicators if indicator in title_lower)

        # Filter if content shows strong music/video/entertainment signals
        is_music_content = (
            title_music_count >= title_music_threshold or
            music_score >= content_music_threshold
        )

        is_video_content = (
            title_video_count >= title_video_threshold or
            video_score >= content_video_threshold
        )

        # Filter out music/video content unless explicitly requested
        return is_music_content or is_video_content
    
    def filter_knowledge_by_relevance(
        self,
        query: str,
        knowledge_items: List[Dict],
        query_intent: Optional[Dict] = None,
        min_score: float = 0.3
    ) -> List[Tuple[float, Dict]]:
        """Filter and score knowledge items by relevance"""
        scored_items = []
        
        for item in knowledge_items:
            score = self.calculate_semantic_score(query, item, query_intent)
            if score >= min_score:
                scored_items.append((score, item))
        
        # Sort by score (highest first)
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return scored_items


# Global instance
_semantic_scorer = None

def get_semantic_scorer():
    """Get or create global semantic relevance scorer instance"""
    global _semantic_scorer
    if _semantic_scorer is None:
        _semantic_scorer = SemanticRelevanceScorer()
    return _semantic_scorer

