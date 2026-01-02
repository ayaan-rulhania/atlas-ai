"""
Common Sense Handler for Atlas AI
Detects compliments, praise, casual conversation, and responds with common sense
without triggering unnecessary web searches
"""
import re
from typing import Optional, List, Dict
from chatbot.refinement.personalization import get_personalization_engine


class CommonSenseHandler:
    """Handles common sense responses for compliments, praise, and casual conversation"""
    
    def __init__(self):
        self.compliment_patterns = [
            r'\b(you|u)\s+(are|r)\s+(so|really|very|pretty|quite|extremely|super|incredibly)\s+(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect|smart|intelligent|helpful|nice|cool|badass|the best)\b',
            r'\b(you|u)\s+(are|r)\s+(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect|smart|intelligent|helpful|nice|cool|the best)\b',
            r'\b(that|this)\s+(is|was|s)\s+(so|really|very|pretty|quite|extremely|super|incredibly)\s+(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect|smart|intelligent|helpful|nice|cool)\b',
            r'\b(well\s+)?(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect)\s+job\b',
            r'\b(thank\s+you|thanks)\s+(so\s+)?(much|a lot|for everything)\b',
            r'\b(you|u)\s+(saved|helped)\s+(me|my|the)\s+(day|butt|life|time)\b',
            r'\b(you|u)\s+(rock|are the best|are awesome|are amazing)\b',
            r'\b(that|this)\s+(is|was|s)\s+(exactly|precisely|perfect|just)\s+(what|what I needed)\b',
        ]
        
        self.compliment_responses = [
            "Thank you so much! I really appreciate that. I'm here to help!",
            "Aww, thanks! That means a lot. I'm always here to assist you.",
            "Thank you! I'm glad I could help. Feel free to ask me anything!",
            "You're very welcome! I'm happy to be of assistance.",
            "Thanks! It's my pleasure to help. What else can I do for you?",
            "Thank you for the kind words! I'm here whenever you need me.",
            "I appreciate that! Let me know if there's anything else you'd like help with.",
        ]
        
        self.casual_patterns = [
            # Greetings and basic interactions
            r'\b(hi|hello|hey|hiya)\s+(there|again|back)\b',
            r'\b(good\s+)?(morning|afternoon|evening|night)\b',
            r'\b(bye|goodbye|see\s+you|later|cya|ttyl)\b',

            # Status inquiries
            r'\b(how\s+)?(are\s+)?(you|u)\s+(doing|today|feeling)\b',
            r'\b(what\s+)?(are\s+)?(you|u)\s+(up to|doing)\b',
            r'\b(how\s+)?(is\s+)?(your|ur)\s+(day|week|morning|afternoon|evening)\s+(going|been)\b',
            r'\b(hows|how\'s)\s+(your|ur)\s+(day|week|morning|afternoon|evening)\s*(going|been)?\b',
            r'\b(what\s+)?(is\s+)?(new|good|up|happening)\b',

            # Reactions and acknowledgments
            r'\b(thats|that\'s|this is)\s+(interesting|cool|nice|awesome|great|amazing|weird|strange|funny)\b',
            r'\b(i\s+)?(see|understand|get it|got it)\b',
            r'\b(makes|that makes)\s+sense\b',
            r'\b(oh\s+)?(really|wow|neat|cool|interesting)\b',
            r'\b(thanks|thank you)\s+(anyway|though)\b',
            r'\b(you\'re|you are)\s+(right|correct|amazing|awesome)\b',

            # Agreement and understanding
            r'\b(i\s+)?(agree|disagree|understand|see)\s+(your|the)\s+point\b',
            r'\b(that\'s|this is|it\'s)\s+(true|correct|right|exactly)\b',
            r'\b(you\'re|you are)\s+(making|totally)\s+sense\b',

            # Conversational fillers and transitions
            r'\b(anyway|so|well|okay|alright)\b',
            r'\b(what\s+else|anything\s+else)\b',
            r'\b(by\s+the\s+way|btw)\b',

            # Time and date related
            r'\b(what\s+time|what\s+day)\s+(is\s+it|is\s+today)\b',
            r'\b(what\'s|what is)\s+(the\s+time|the\s+date|today)\b',

            # Simple personal statements
            r'\b(i\'m|i am)\s+(fine|good|okay|alright|great)\b',
            r'\b(i\'m|i am)\s+(tired|busy|working|learning|thinking)\b',
            r'\b(that\'s|this is)\s+(good|nice|cool|awesome)\b',

            # Questions about AI capabilities
            r'\b(what\s+can|what\s+do)\s+you\s+(do|help with)\b',
            r'\b(how\s+can|how\s+do)\s+you\s+help\b',
            r'\b(tell\s+me\s+about|who\s+are)\s+you\b',

            # Simple acknowledgments
            r'\b(ok|okay|sure|alright|got it|understood)\b',
            r'\b(yes|no|maybe|perhaps)\b',

            # Emotional expressions
            r'\b(that\'s\s+)?awesome\b',
            r'\b(that\'s\s+)?amazing\b',
            r'\b(cool|neat|sweet)\b',
        ]
        
    def is_compliment(self, message: str) -> bool:
        """Check if message is a compliment or praise"""
        message_lower = message.lower().strip()
        
        # Check against compliment patterns
        for pattern in self.compliment_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        return False
    
    def is_casual_conversation(self, message: str) -> bool:
        """Check if message is casual conversation that doesn't need web search"""
        message_lower = message.lower().strip()
        
        for pattern in self.casual_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        return False
    
    def should_skip_search(self, message: str) -> bool:
        """Determine if we should skip web search for this message"""
        if self.is_compliment(message) or self.is_casual_conversation(message):
            return True
        
        # Add more common sense patterns that don't need web search
        message_lower = message.lower().strip()
        
        # Common sense questions that can be answered without search
        common_sense_patterns = [
            r'\b(?:what|how|why)\s+is\s+(?:2\s*\+\s*2|the\s+time|today|the\s+date)',
            r'\b(?:what|which)\s+is\s+(?:better|best)\s+(?:python|javascript|java)\s+(?:or|vs)',
            r'\b(?:can|should|do)\s+you\s+(?:help|remember|save)',
            r'\b(?:tell|show)\s+me\s+(?:about\s+)?yourself',
            r'\b(?:what|who)\s+are\s+you',
            r'\b(?:how|what)\s+(?:do|does)\s+(?:you|this|it)\s+work',
            r'\b(?:is|are)\s+(?:this|that|it)\s+(?:good|bad|right|wrong|correct)',
            r'\b(?:should|can)\s+i\s+(?:use|try|do)',
            r'\b(?:what|which)\s+(?:should|can)\s+i\s+(?:use|choose|pick)',
            # New conversational patterns
            r'\b(?:what|how)\s+(?:do|does)\s+you\s+think\b',
            r'\b(?:what\'s|what is)\s+your\s+(opinion|thought|take)\b',
            r'\b(?:do|did)\s+you\s+(like|enjoy|think)\b',
            r'\b(?:i\'m|i am)\s+(working on|learning|trying to|thinking about)\b',
            r'\b(?:i\s+)?feel\s+(like|that)\b',
            r'\b(?:i\'m|i am)\s+(feeling|thinking|wondering)\b',
            r'\b(?:that\'s|this is|it\'s)\s+(strange|weird|odd|interesting|cool)\b',
            r'\b(?:sounds?|seems?)\s+(good|great|awesome|interesting|cool)\b',
            r'\b(?:i\s+)?(?:agree|disagree|understand|see)\s+(your|the)\s+point\b',
            r'\b(?:that\'s|this is)\s+(exactly|precisely|just)\s+what\s+i\s+(thought|meant|wanted)\b',

            # Additional conversational patterns
            r'\b(?:what|how)\s+(?:do|does)\s+you\s+(feel|think)\s+about\b',
            r'\b(?:i\s+)?(?:think|believe|feel)\s+(that|this is)\b',
            r'\b(?:that\'s|this is)\s+(what\s+i|exactly)\s+(thought|meant|wanted)\b',
            r'\b(?:i\s+)?(?:wonder|curious)\s+(what|how|why|if)\b',
            r'\b(?:tell|show)\s+me\s+(more|something)\s+(about|on)\b',
            r'\b(?:i\'m|i am)\s+(not\s+sure|confused|lost)\b',
            r'\b(?:can|could)\s+you\s+(explain|clarify|help\s+me)\s+(with|about)\b',
            r'\b(?:what|how)\s+(?:would|should)\s+i\s+(know|find out|learn)\b',
            r'\b(?:i\s+)?(?:need|want)\s+(help|advice|information)\s+(with|about|on)\b',
            r'\b(?:that\'s|this is)\s+(helpful|useful|great|awesome)\b',
            r'\b(?:thanks?|thank\s+you)\s+(for|so\s+much|a\s+lot)\b',

            # Simple acknowledgments and transitions
            r'\b(?:ok|okay|sure|alright|got\s+it|understood)\b',
            r'\b(?:yes|no|maybe|perhaps)\b',
            r'\b(?:anyway|so|well|okay|alright)\b',
            r'\b(?:what\s+else|anything\s+else)\b',
            r'\b(?:by\s+the\s+way|btw)\b',
        ]
        
        for pattern in common_sense_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        # Mathematical questions (simple arithmetic)
        math_pattern = r'^\s*(?:what\s+is|calculate|compute)\s+[\d\+\-\*\/\s\(\)]+\s*\?*\s*$'
        if re.match(math_pattern, message_lower):
            return True
        
        # Very short questions that are likely conversational
        if len(message.split()) <= 3 and not any(word in message_lower for word in ['who', 'what', 'when', 'where', 'why', 'how']):
            return True
        
        return False
    
    def get_common_sense_response(self, message: str, context: Optional[List[dict]] = None) -> Optional[str]:
        """Get common sense response for questions that don't need web search"""
        message_lower = message.lower().strip()
        
        # Mathematical questions
        math_pattern = r'^\s*(?:what\s+is|calculate|compute)\s+([\d\+\-\*\/\s\(\)]+)\s*\?*\s*$'
        math_match = re.match(math_pattern, message_lower)
        if math_match:
            try:
                expression = math_match.group(1).strip()
                # Simple evaluation (be careful with eval in production)
                result = eval(expression.replace(' ', ''))
                return f"The answer is **{result}**."
            except:
                pass
        
        # Questions about the assistant
        if re.search(r'\b(?:what|who)\s+are\s+you\b', message_lower):
            return "I'm Atlas, an AI assistant powered by Thor models. I'm here to help you with questions, tasks, and information. How can I assist you today?"
        
        if re.search(r'\b(?:tell|show)\s+me\s+(?:about\s+)?yourself\b', message_lower):
            return "I'm Atlas, an AI assistant. I can help you with a wide range of tasks including answering questions, generating content, writing code, creating images, and much more. What would you like to know or work on?"
        
        # Questions about capabilities
        if re.search(r'\b(?:what|what can)\s+(?:can|do)\s+you\s+(?:do|help)|\b(?:how)\s+can\s+you\s+help', message_lower):
            return "I can help you with:\n- Answering questions and providing information\n- Writing and debugging code\n- Creating images\n- Generating creative content\n- And much more! What would you like to do?"
        
        # Time/date questions
        if re.search(r'\b(?:what|what\'s)\s+(?:is\s+)?(?:the\s+)?(?:time|date|today)\b', message_lower):
            from datetime import datetime
            now = datetime.now()
            return f"Today is **{now.strftime('%B %d, %Y')}** and the current time is **{now.strftime('%I:%M %p')}**."

        # Opinion/thought questions
        if re.search(r'\b(?:what|how)\s+(?:do|does)\s+you\s+think\b', message_lower):
            return "I think it depends on the context! I'd need more details to give you a better answer. What specifically are you wondering about?"

        if re.search(r'\b(?:what\'s|what is)\s+your\s+(opinion|thought|take)\b', message_lower):
            return "I don't have personal opinions like humans do, but I can help you analyze different perspectives on the topic. What would you like to explore?"

        # Personal statements about user activities
        if re.search(r'\b(?:i\'m|i am)\s+(working on|learning|trying to|thinking about)\b', message_lower):
            return "That sounds productive! I'm here if you need any help or have questions about what you're working on."

        # Feeling/thinking statements
        if re.search(r'\b(?:i\s+)?feel\s+(like|that)\b', message_lower):
            return "I understand how you feel. If you'd like to talk about it or need any advice, I'm here to listen."

        if re.search(r'\b(?:i\'m|i am)\s+(feeling|thinking|wondering)\b', message_lower):
            return "I'm here to help with whatever you're thinking about. What's on your mind?"

        # Observations and agreements
        if re.search(r'\b(?:that\'s|this is|it\'s)\s+(strange|weird|odd|interesting|cool)\b', message_lower):
            return "Interesting observation! Sometimes things can be surprising. Is there something specific you'd like to know more about?"

        if re.search(r'\b(?:sounds?|seems?)\s+(good|great|awesome|interesting|cool)\b', message_lower):
            return "Glad you think so! If you need help with anything related to that, just let me know."

        # Agreement patterns
        if re.search(r'\b(?:i\s+)?(?:agree|disagree|understand|see)\s+(your|the)\s+point\b', message_lower):
            return "Great to hear we agree on that! Is there anything else you'd like to discuss or work on?"

        # Additional conversational responses
        if re.search(r'\b(?:what|how)\s+(?:do|does)\s+you\s+(feel|think)\s+about\b', message_lower):
            return "As an AI, I don't have personal feelings or opinions, but I can help you explore different perspectives on topics. What would you like to discuss?"

        if re.search(r'\b(?:i\s+)?(?:think|believe|feel)\s+(that|this is)\b', message_lower):
            return "Interesting! I'd love to hear more about your thoughts. What makes you feel that way?"

        if re.search(r'\b(?:that\'s|this is)\s+(what\s+i|exactly)\s+(thought|meant|wanted)\b', message_lower):
            return "Great minds think alike! It's always nice to find common ground. What else is on your mind?"

        if re.search(r'\b(?:i\s+)?(?:wonder|curious)\s+(what|how|why|if)\b', message_lower):
            return "Curiosity is a wonderful thing! I'm here to help satisfy that curiosity. What would you like to know?"

        if re.search(r'\b(?:tell|show)\s+me\s+(more|something)\s+(about|on)\b', message_lower):
            return "I'd be happy to share more information! What specific aspect interests you most?"

        if re.search(r'\b(?:i\'m|i am)\s+(not\s+sure|confused|lost)\b', message_lower):
            return "That's completely understandable - sometimes things can be confusing. Let me help clarify. What specifically are you unsure about?"

        if re.search(r'\b(?:can|could)\s+you\s+(explain|clarify|help\s+me)\s+(with|about)\b', message_lower):
            return "Absolutely! I'm here to help explain and clarify things. What would you like me to explain?"

        if re.search(r'\b(?:what|how)\s+(?:would|should)\s+i\s+(know|find out|learn)\b', message_lower):
            return "That's a great question! There are many ways to learn and discover. What topic are you interested in exploring?"

        if re.search(r'\b(?:i\s+)?(?:need|want)\s+(help|advice|information)\s+(with|about|on)\b', message_lower):
            return "I'm here to help! Tell me more about what you need assistance with, and I'll do my best to support you."

        if re.search(r'\b(?:that\'s|this is)\s+(helpful|useful|great|awesome)\b', message_lower):
            return "I'm glad I could be helpful! Is there anything else you'd like assistance with?"

        if re.search(r'\b(?:thanks?|thank\s+you)\s+(for|so\s+much|a\s+lot)\b', message_lower):
            return "You're very welcome! I'm always happy to help. What else can I assist you with?"

        # Simple acknowledgments
        if re.search(r'\b(?:ok|okay|sure|alright|got\s+it|understood)\b', message_lower):
            return "Great! What would you like to do next?"

        if re.search(r'\b(?:yes|no|maybe|perhaps)\b', message_lower):
            return "Thanks for letting me know. Is there anything specific you'd like to work on or discuss?"

        # Transitions
        if re.search(r'\b(?:anyway|so|well|okay|alright)\b', message_lower):
            return "Alright, let's continue. What would you like to talk about?"

        if re.search(r'\b(?:what\s+else|anything\s+else)\b', message_lower):
            return "I'm here to help with whatever you need! What else is on your mind?"

        if re.search(r'\b(?:by\s+the\s+way|btw)\b', message_lower):
            return "Sure, what's on your mind?"

        return None
    
    def get_response(self, message: str, context: Optional[List[dict]] = None, conversation_context: Optional[dict] = None) -> str:
        """Get appropriate response for compliment or casual conversation with context awareness"""
        import random

        # Analyze conversation context if provided
        context_aware = False
        emotional_state = 'neutral'
        response_preference = 'balanced'
        conversation_flow = 'general'

        if conversation_context:
            context_aware = conversation_context.get('context_available', False)
            emotional_state = conversation_context.get('emotional_state', 'neutral')
            response_preference = conversation_context.get('response_preference', 'balanced')
            conversation_flow = conversation_context.get('conversation_flow', 'general')

        # First check common sense responses
        common_sense = self.get_common_sense_response(message, context)
        if common_sense:
            # Modify response based on context if needed
            if context_aware:
                common_sense = self._adapt_response_to_context(common_sense, emotional_state, response_preference, conversation_flow)
            return common_sense
        
        if self.is_compliment(message):
            response = random.choice(self.compliment_responses)
            # Personalize based on context if available
            if context and len(context) > 0:
                # Check if user mentioned something specific we helped with
                last_assistant_msg = None
                for msg in reversed(context):
                    if msg.get('role') == 'assistant':
                        last_assistant_msg = msg.get('content', '')
                        break
                
                if last_assistant_msg:
                    response += " I'm glad I could assist you!"
            
            return response
        
        elif self.is_casual_conversation(message):
            message_lower = message.lower().strip()

            # Get base responses based on message type
            casual_responses = self._get_contextual_casual_responses(message_lower)

            # Apply personalization for response variety if context available
            if context_aware and conversation_context and conversation_context.get('context_available'):
                # Get user key from conversation context (assuming it's passed in context_analysis)
                user_key = conversation_context.get('user_key')
                if user_key:
                    personalization_engine = get_personalization_engine()
                    casual_responses = personalization_engine.generate_response_variations(
                        user_key, casual_responses, 'casual'
                    )

            # Select response based on context
            selected_response = random.choice(casual_responses)

            # Adapt response based on conversation context if available
            if context_aware:
                selected_response = self._adapt_response_to_context(
                    selected_response, emotional_state, response_preference, conversation_flow
                )

            return selected_response
        
        return None

    def should_fallback_to_research(self, message: str, context: Optional[List[dict]] = None) -> bool:
        """
        Determine if common sense response is insufficient and should fall back to research/brain lookup.

        Returns True if fallback is recommended.
        """
        message_lower = message.lower().strip()

        # Fallback indicators - queries that need external knowledge
        fallback_indicators = [
            # Current events and news
            'what\'s happening', 'what happened', 'current events', 'latest news',
            'today\'s news', 'breaking news', 'in the news',

            # Specific factual queries
            'who is', 'what is', 'when was', 'where is', 'how much', 'how many',
            'what are the', 'what does', 'how does', 'why does',

            # Technical/programming questions
            'how to', 'how do i', 'how can i', 'tutorial', 'guide', 'documentation',

            # Comparisons and lists
            'vs', 'versus', 'better than', 'best', 'top', 'list of', 'examples of',

            # Recent developments
            'new', 'latest', 'recent', 'update', 'version', 'release',

            # Specific domains that need research
            'price', 'cost', 'how much does', 'where can i buy', 'reviews of',
        ]

        # Check for fallback indicators
        has_fallback_indicators = any(indicator in message_lower for indicator in fallback_indicators)

        # Check for question marks (factual questions often need research)
        has_question_mark = '?' in message

        # Check message length (longer messages often need more context)
        word_count = len(message.split())
        is_long_message = word_count > 12

        # Check for specific terms that suggest research is needed
        specific_terms = ['quantum', 'ai', 'machine learning', 'blockchain', 'cryptocurrency',
                         'politics', 'government', 'law', 'medical', 'health', 'science']

        has_specific_terms = any(term in message_lower for term in specific_terms)

        # Fallback if the message seems too complex for common sense alone
        should_fallback = (
            has_fallback_indicators or
            (has_question_mark and is_long_message) or
            has_specific_terms or
            (word_count > 8 and not any(word in message_lower for word in [
                'i feel', 'i think', 'i\'m', 'i am', 'thank', 'thanks', 'hi', 'hello',
                'good morning', 'good afternoon', 'good evening', 'bye', 'goodbye'
            ]))
        )

        return should_fallback

    def get_fallback_suggestion(self, message: str) -> Optional[str]:
        """
        Provide a helpful suggestion when falling back to research/brain lookup.
        """
        message_lower = message.lower()

        # Provide contextual suggestions based on query type
        if any(term in message_lower for term in ['how to', 'how do i', 'tutorial', 'guide']):
            return "I'll look up the best resources and guides for that."

        if any(term in message_lower for term in ['what is', 'explain', 'what does']):
            return "Let me find the most accurate and up-to-date information for you."

        if any(term in message_lower for term in ['best', 'top', 'recommend']):
            return "I'll search for the most highly-rated options and current recommendations."

        if any(term in message_lower for term in ['news', 'happening', 'latest']):
            return "Let me check the most recent and reliable sources for current information."

        # Generic fallback
        return "I'll search for the most relevant and accurate information to help you with that."

    def get_partial_response(self, message: str) -> Optional[str]:
        """
        Provide a partial response or clarification for complex queries that need research.

        This helps bridge the gap between common sense and research by providing
        immediate helpful information while research is being conducted.
        """
        message_lower = message.lower().strip()

        # Programming-related queries
        if any(term in message_lower for term in ['python', 'javascript', 'code', 'programming']):
            if 'how to' in message_lower or 'how do i' in message_lower:
                return "That's a great programming question! While I search for specific examples and best practices, remember that good code follows principles like readability, error handling, and documentation."

        # Learning/study queries
        if any(term in message_lower for term in ['learn', 'study', 'understand', 'tutorial']):
            return "Learning is a journey! I'll find you the best resources and approaches. In the meantime, remember that consistent practice and breaking down complex topics into smaller parts is key to effective learning."

        # Technical setup queries
        if any(term in message_lower for term in ['install', 'setup', 'configure', 'deploy']):
            return "Technical setups can be tricky! I'll find you the most current and reliable instructions. Remember to check system requirements and follow official documentation when possible."

        # Career/job queries
        if any(term in message_lower for term in ['career', 'job', 'salary', 'interview']):
            return "Career decisions are important! I'll research current trends and advice. Meanwhile, focus on building practical skills and networking - these are often more valuable than theoretical knowledge alone."

        # Health/medical queries (be careful with disclaimers)
        if any(term in message_lower for term in ['health', 'medical', 'symptom', 'treatment']):
            return "For health-related questions, it's always best to consult qualified medical professionals. I'll search for reliable general information, but this should not replace professional medical advice."

        # No partial response available
        return None

    def _get_contextual_casual_responses(self, message_lower: str) -> List[str]:
        """Get contextual casual responses based on message type"""
        # More varied and contextual responses based on the type of casual message
        if any(word in message_lower for word in ['morning', 'good morning']):
            return [
                "Good morning! Hope you're having a great start to your day. What can I help you with?",
                "Morning! Ready to tackle the day. How can I assist you?",
                "Good morning! I'm here and energized. What's on your agenda today?",
                "Morning! Fresh and ready to help. What's first on your list?"
            ]
        elif any(word in message_lower for word in ['afternoon', 'good afternoon']):
            return [
                "Good afternoon! How's your day going so far?",
                "Afternoon! Hope you're having a productive day. How can I help?",
                "Good afternoon! I'm here whenever you need assistance.",
                "Afternoon! Ready to assist with whatever you need."
            ]
        elif any(word in message_lower for word in ['evening', 'good evening']):
            return [
                "Good evening! Hope you're winding down nicely. What can I do for you?",
                "Evening! I'm here if you need any assistance before you rest.",
                "Good evening! Ready to help with whatever you need.",
                "Evening! How can I assist you this evening?"
            ]
        elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'later', 'cya', 'ttyl']):
            return [
                "Goodbye! It was great chatting with you. Come back anytime!",
                "See you later! Feel free to reach out whenever you need help.",
                "Take care! I'm here whenever you need assistance.",
                "Farewell! Don't hesitate to return if you need anything."
            ]
        elif any(word in message_lower for word in ['how are you', 'how do you do', 'how is your day']):
            return [
                "I'm doing well, thank you for asking! I'm here and ready to help with whatever you need.",
                "I'm functioning optimally! How about you? What can I assist you with today?",
                "I'm great, thanks! Always happy to help. What's on your mind?",
                "I'm doing well! How are you doing? Ready to help with anything you need."
            ]
        elif any(word in message_lower for word in ['what are you up to', 'what are you doing']):
            return [
                "Just here waiting to help you with whatever you need! What's up?",
                "Standing by and ready to assist! What can I do for you?",
                "I'm here and attentive, ready for your next request. How can I help?",
                "Prepared and waiting! What would you like assistance with?"
            ]
        else:
            # General casual responses
            return [
                "I'm doing great, thanks for asking! How can I help you today?",
                "I'm here and ready to help! What can I do for you?",
                "Doing well! What would you like to know or work on?",
                "I'm good! How can I assist you?",
                "All set and ready! What's on your mind?",
                "I'm doing well, thank you! Ready to help with whatever you need.",
                "Great, thanks! How can I be of assistance today?",
                "I'm good! What would you like to work on or discuss?",
                "Doing fantastic! How can I help you today?",
                "I'm here and attentive. What can I do for you?"
            ]

    def _adapt_response_to_context(self, response: str, emotional_state: str,
                                 response_preference: str, conversation_flow: str) -> str:
        """Adapt response based on conversation context"""

        # Adjust tone based on user's emotional state
        if emotional_state == 'frustrated':
            # Be more empathetic and helpful
            if 'how can i help' in response.lower():
                response = response.replace('How can I help', 'I understand that can be frustrating. How can I help')
            elif 'what can i do' in response.lower():
                response = response.replace('What can I do', 'I hear you - let me help with that. What can I do')

        elif emotional_state == 'excited':
            # Match enthusiasm
            if 'great' in response.lower() or 'good' in response.lower():
                response += " Your enthusiasm is contagious!"

        elif emotional_state == 'tired':
            # Be gentle and understanding
            if 'ready to help' in response.lower():
                response = response.replace('ready to help', 'here when you\'re ready')

        elif emotional_state == 'confused':
            # Be patient and clear
            response += " Take your time - I'm here to help clarify things."

        # Adjust length based on response preference
        if response_preference == 'concise':
            # Make response shorter
            sentences = response.split('. ')
            if len(sentences) > 2:
                response = '. '.join(sentences[:2]) + '.'
        elif response_preference == 'detailed':
            # Could add more detail, but for casual responses, keep them natural
            pass

        # Adjust based on conversation flow
        if conversation_flow == 'continuing_topic':
            # Add continuity phrases
            if random.random() < 0.3:  # 30% chance to add continuity
                continuity_phrases = [
                    "Continuing on that topic...",
                    "Building on what we were discussing...",
                    "Following up on that..."
                ]
                response = random.choice(continuity_phrases) + " " + response

        elif conversation_flow == 'topic_shift':
            # Add transition phrases
            if random.random() < 0.2:  # 20% chance for smooth transition
                transition_phrases = [
                    "Speaking of something different...",
                    "On another note...",
                    "That reminds me..."
                ]
                response = random.choice(transition_phrases) + " " + response

        return response


# Global instance
_common_sense_handler = None

def get_common_sense_handler():
    """Get or create the global common sense handler instance"""
    global _common_sense_handler
    if _common_sense_handler is None:
        _common_sense_handler = CommonSenseHandler()
    return _common_sense_handler

