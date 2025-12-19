"""
Conversational Context Analyzer - Advanced context understanding for natural dialogue flow.

This module provides comprehensive analysis of conversational context to distinguish between:
- Literal queries that require search/knowledge retrieval
- Conversational statements that reference previous context
- Follow-up questions that need previous context
- Casual remarks that should be handled conversationally

The goal is to maintain natural conversation flow without hardcoding specific phrases.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set
import re


class ConversationalContextAnalyzer:
    """Analyzes conversational context to understand user intent and maintain dialogue flow."""
    
    def __init__(self):
        # Conversational statement patterns (not questions, not commands)
        self.conversational_indicators = {
            'acknowledgment': ['ok', 'okay', 'got it', 'understood', 'alright', 'sure', 'yes', 'yeah', 'yep'],
            'return_statements': ['came back', 'am back', 'returned', 'here again', 'back again'],
            'continuation': ['and', 'also', 'plus', 'additionally', 'furthermore'],
            'agreement': ['exactly', 'right', 'correct', 'true', 'indeed', 'absolutely'],
            'disagreement': ['no', 'nope', 'wrong', 'incorrect', 'not really'],
            'thanks': ['thanks', 'thank you', 'appreciate it', 'much appreciated'],
            'casual': ['cool', 'nice', 'great', 'awesome', 'wow', 'interesting']
        }
        
        # Semantic relationship patterns between user message and previous assistant message
        self.semantic_relationships = {
            'response_to_invitation': [
                (r'come\s+back', r'(came|come|am|are)\s+back'),
                (r'come\s+back\s+any\s+time', r'(came|come|am|are)\s+back'),
                (r'come\s+back\s+any\s+time', r'i\s+(came|come|am|are)\s+back'),
                (r'welcome\s+back', r'(came|come|am|are)\s+back'),
                (r'feel\s+free\s+to', r'(will|can|should|would)'),
                (r'let\s+me\s+know', r'(will|can|should|would)'),
                (r'any\s+time', r'(came|come|am|are)\s+back'),
            ],
            'response_to_suggestion': [
                (r'you\s+can\s+try', r'(tried|will\s+try|am\s+trying)'),
                (r'you\s+should', r'(will|am|did)'),
                (r'how\s+about', r'(sounds|good|great|ok)'),
            ],
            'response_to_question': [
                (r'what\s+would\s+you\s+like', r'(would\s+like|want|need)'),
                (r'how\s+can\s+i\s+help', r'(help|assist|support)'),
                (r'what\s+can\s+i\s+do', r'(can|will|should)'),
            ],
            'acknowledgment_of_statement': [
                (r'that\'s\s+(right|correct|true)', r'(yes|yeah|exactly|right)'),
                (r'you\'re\s+(right|correct)', r'(yes|yeah|exactly)'),
            ],
        }
        
        # Patterns that indicate literal queries (not conversational)
        self.literal_query_indicators = {
            'question_words': ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'whom'],
            'question_verbs': ['explain', 'define', 'describe', 'tell me about', 'what is', 'what are'],
            'search_triggers': ['search', 'find', 'look up', 'information about', 'details about'],
            'factual_requests': ['capital of', 'population of', 'definition of', 'meaning of'],
        }
        
        # Minimum word count for statements to be considered conversational (not just typos/noise)
        self.min_conversational_length = 2
        
        # Maximum word count for conversational statements (longer = likely a query)
        self.max_conversational_length = 12
    
    def analyze_context(
        self,
        user_message: str,
        conversation_context: List[Dict],
        normalized_message: Optional[str] = None
    ) -> Dict:
        """
        Comprehensive analysis of conversational context.
        
        Returns:
            Dict with keys:
            - is_conversational: bool - Is this a conversational statement vs literal query?
            - is_context_reference: bool - Does this reference previous conversation?
            - context_type: str - Type of context reference (invitation_response, continuation, etc.)
            - related_previous_message: Optional[str] - The previous message this relates to
            - requires_search: bool - Should this trigger search/knowledge retrieval?
            - conversational_response_type: str - Type of conversational response needed
            - confidence: float - Confidence in the analysis
        """
        if not user_message or not user_message.strip():
            return self._default_analysis()
        
        user_lower = (normalized_message or user_message).lower().strip()
        words = user_lower.split()
        word_count = len(words)
        
        result = {
            'is_conversational': False,
            'is_context_reference': False,
            'context_type': None,
            'related_previous_message': None,
            'requires_search': True,  # Default to requiring search unless proven conversational
            'conversational_response_type': None,
            'confidence': 0.0,
        }
        
        # Check if it's clearly a literal query
        if self._is_literal_query(user_message, user_lower, words):
            result['requires_search'] = True
            result['is_conversational'] = False
            result['confidence'] = 0.9
            return result
        
        # Check if it's a conversational statement
        conversational_analysis = self._analyze_conversational_statement(
            user_message, user_lower, words, conversation_context
        )
        
        if conversational_analysis['is_conversational']:
            result.update(conversational_analysis)
            result['requires_search'] = False
            return result
        
        # Check for semantic relationships with previous messages
        semantic_analysis = self._analyze_semantic_relationships(
            user_message, user_lower, conversation_context
        )
        
        if semantic_analysis['is_context_reference']:
            result.update(semantic_analysis)
            result['requires_search'] = False
            result['is_conversational'] = True
            return result
        
        # Default: treat as query if we're not sure
        return result
    
    def _is_literal_query(self, original: str, lower: str, words: List[str]) -> bool:
        """Check if message is clearly a literal query requiring search."""
        # Has question mark
        if '?' in original:
            return True
        
        # Starts with question word
        if words and words[0] in self.literal_query_indicators['question_words']:
            return True
        
        # Contains question phrases
        for phrase in self.literal_query_indicators['question_verbs']:
            if phrase in lower:
                return True
        
        # Contains search triggers
        for trigger in self.literal_query_indicators['search_triggers']:
            if trigger in lower:
                return True
        
        # Contains factual request patterns
        for pattern in self.literal_query_indicators['factual_requests']:
            if pattern in lower:
                return True
        
        # Long messages (>15 words) are likely queries
        if len(words) > 15:
            return True
        
        return False
    
    def _analyze_conversational_statement(
        self,
        original: str,
        lower: str,
        words: List[str],
        context: List[Dict]
    ) -> Dict:
        """Analyze if message is a conversational statement."""
        result = {
            'is_conversational': False,
            'conversational_response_type': None,
            'confidence': 0.0,
        }
        
        word_count = len(words)
        
        # Too short or too long - likely not conversational
        if word_count < self.min_conversational_length or word_count > self.max_conversational_length:
            return result
        
        # Check for acknowledgment patterns
        if any(ack in lower for ack in self.conversational_indicators['acknowledgment']):
            result['is_conversational'] = True
            result['conversational_response_type'] = 'acknowledgment'
            result['confidence'] = 0.8
            return result
        
        # Check for return statements (like "I came back")
        if any(phrase in lower for phrase in self.conversational_indicators['return_statements']):
            # Check if previous assistant message had invitation
            if context:
                for msg in reversed(context):
                    if msg.get('role') == 'assistant':
                        content = msg.get('content', '').lower()
                        # More flexible matching for invitations
                        invitation_patterns = [
                            'come back',
                            'come back any time',
                            'welcome back',
                            'any time',
                            'feel free',
                            'come back anytime',
                        ]
                        if any(inv in content for inv in invitation_patterns):
                            result['is_conversational'] = True
                            result['conversational_response_type'] = 'return_response'
                            result['is_context_reference'] = True
                            result['context_type'] = 'invitation_response'
                            result['related_previous_message'] = msg.get('content')
                            result['confidence'] = 0.95
                            return result
            # Even without explicit invitation, "I came back" is conversational if short
            if word_count <= 5:
                result['is_conversational'] = True
                result['conversational_response_type'] = 'return_response'
                result['confidence'] = 0.8
                return result
        
        # Check for agreement/disagreement
        if any(phrase in lower for phrase in self.conversational_indicators['agreement']):
            result['is_conversational'] = True
            result['conversational_response_type'] = 'agreement'
            result['confidence'] = 0.7
            return result
        
        if any(phrase in lower for phrase in self.conversational_indicators['disagreement']):
            result['is_conversational'] = True
            result['conversational_response_type'] = 'disagreement'
            result['confidence'] = 0.7
            return result
        
        # Check for thanks
        if any(phrase in lower for phrase in self.conversational_indicators['thanks']):
            result['is_conversational'] = True
            result['conversational_response_type'] = 'thanks'
            result['confidence'] = 0.9
            return result
        
        # Check for casual remarks (only if short)
        if word_count <= 4 and any(phrase in lower for phrase in self.conversational_indicators['casual']):
            result['is_conversational'] = True
            result['conversational_response_type'] = 'casual'
            result['confidence'] = 0.6
            return result
        
        return result
    
    def _analyze_semantic_relationships(
        self,
        original: str,
        lower: str,
        context: List[Dict]
    ) -> Dict:
        """Analyze semantic relationships with previous messages."""
        result = {
            'is_context_reference': False,
            'context_type': None,
            'related_previous_message': None,
            'confidence': 0.0,
        }
        
        if not context:
            return result
        
        # Check recent assistant messages for semantic relationships
        for msg in reversed(context[-6:]):  # Check last 6 messages
            if msg.get('role') != 'assistant':
                continue
            
            assistant_content = msg.get('content', '').lower()
            
            # Check each semantic relationship pattern
            for rel_type, patterns in self.semantic_relationships.items():
                for assistant_pattern, user_pattern in patterns:
                    if re.search(assistant_pattern, assistant_content, re.IGNORECASE):
                        if re.search(user_pattern, lower, re.IGNORECASE):
                            result['is_context_reference'] = True
                            result['context_type'] = rel_type
                            result['related_previous_message'] = msg.get('content')
                            result['confidence'] = 0.85
                            return result
            
            # Additional semantic checks: word overlap and context matching
            # If user message has significant word overlap with assistant message, it might be a response
            if len(lower.split()) <= 8:  # Only for short messages
                assistant_words = set(assistant_content.split())
                user_words = set(lower.split())
                # Remove common stopwords
                stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
                assistant_words = assistant_words - stopwords
                user_words = user_words - stopwords
                
                # If there's meaningful overlap (at least 2 words), might be conversational
                overlap = assistant_words.intersection(user_words)
                if len(overlap) >= 2 and len(overlap) >= len(user_words) * 0.3:
                    # Check if it's not a question
                    if not any(q in lower for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which']):
                        result['is_context_reference'] = True
                        result['context_type'] = 'semantic_overlap'
                        result['related_previous_message'] = msg.get('content')
                        result['confidence'] = 0.75
                        return result
        
        # Check for general continuation patterns
        if self._is_continuation(lower, context):
            result['is_context_reference'] = True
            result['context_type'] = 'continuation'
            result['confidence'] = 0.7
            if context:
                for msg in reversed(context):
                    if msg.get('role') == 'assistant':
                        result['related_previous_message'] = msg.get('content')
                        break
        
        return result
    
    def _is_continuation(self, lower: str, context: List[Dict]) -> bool:
        """Check if message is a continuation of previous conversation."""
        # Starts with continuation words
        continuation_starters = ['and', 'also', 'plus', 'additionally', 'furthermore', 'moreover']
        if any(lower.startswith(starter + ' ') for starter in continuation_starters):
            return True
        
        # Short message after a longer conversation
        if len(lower.split()) <= 6 and len(context) >= 2:
            # Check if previous assistant message was substantial
            for msg in reversed(context):
                if msg.get('role') == 'assistant':
                    prev_content = msg.get('content', '')
                    if len(prev_content.split()) > 10:
                        return True
                    break
        
        return False
    
    def _default_analysis(self) -> Dict:
        """Return default analysis for empty/invalid input."""
        return {
            'is_conversational': False,
            'is_context_reference': False,
            'context_type': None,
            'related_previous_message': None,
            'requires_search': True,
            'conversational_response_type': None,
            'confidence': 0.0,
        }
    
    def generate_conversational_response(
        self,
        user_message: str,
        analysis: Dict,
        conversation_context: List[Dict]
    ) -> Optional[str]:
        """Generate appropriate conversational response based on analysis."""
        if not analysis.get('is_conversational'):
            return None
        
        response_type = analysis.get('conversational_response_type')
        context_type = analysis.get('context_type')
        
        # Handle return statements (like "I came back")
        if response_type == 'return_response' or context_type == 'invitation_response':
            return "Welcome back! How can I help you today?"
        
        # Handle acknowledgments
        if response_type == 'acknowledgment':
            return "👍 Got it. What would you like to do next?"
        
        # Handle agreement
        if response_type == 'agreement':
            return "Great! Is there anything else you'd like to know?"
        
        # Handle disagreement
        if response_type == 'disagreement':
            return "I understand. How can I help clarify or assist you?"
        
        # Handle thanks
        if response_type == 'thanks':
            return "You're welcome! Feel free to ask if you need anything else."
        
        # Handle casual remarks
        if response_type == 'casual':
            return "Thanks! What would you like to explore?"
        
        # Handle continuation
        if context_type == 'continuation':
            related_msg = analysis.get('related_previous_message')
            if related_msg:
                # Try to continue the previous topic naturally
                return "I'd be happy to continue. What specific aspect would you like to explore further?"
        
        # Default conversational response
        return "I'm here to help! What would you like to know?"


# Global instance
_conversational_analyzer: Optional[ConversationalContextAnalyzer] = None


def get_conversational_analyzer() -> ConversationalContextAnalyzer:
    """Get or create global conversational context analyzer instance."""
    global _conversational_analyzer
    if _conversational_analyzer is None:
        _conversational_analyzer = ConversationalContextAnalyzer()
    return _conversational_analyzer
