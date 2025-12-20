"""
Creative Response Generator - Connects keywords and creates creative responses
"""
import os
import json
import random

class CreativeResponseGenerator:
    """Generates creative responses by connecting keywords"""
    
    def __init__(self, brain_dir="brain"):
        self.brain_dir = brain_dir
    
    def get_connected_knowledge(self, message):
        """Get knowledge by connecting multiple keywords - filters out common words"""
        message_lower = message.lower()
        words = message_lower.split()
        
        # Filter out common stop words that don't help with matching
        stop_words = {'what', 'is', 'a', 'an', 'the', 'this', 'that', 'these', 'those', 
                     'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 
                     'should', 'would', 'will', 'do', 'does', 'did', 'are', 'was', 
                     'were', 'have', 'has', 'had', 'to', 'of', 'in', 'on', 'at', 'for',
                     'with', 'by', 'from', 'about', 'into', 'onto', 'up', 'down'}
        
        # Only use meaningful words (length > 2, not stop words)
        meaningful_words = [w for w in words if len(w) > 2 and w not in stop_words and w[0].isalpha()]
        
        all_knowledge = []
        seen_titles = set()
        
        # Get knowledge for each meaningful keyword
        for word in meaningful_words:
            letter = word[0].upper()
            keywords_file = os.path.join(self.brain_dir, letter, "keywords.json")
            
            if os.path.exists(keywords_file):
                try:
                    with open(keywords_file, 'r') as f:
                        data = json.load(f)
                    
                    if word in data.get('keywords', []):
                        for knowledge in data.get('knowledge', []):
                            title = knowledge.get('title', '')
                            if title and title not in seen_titles:
                                seen_titles.add(title)
                                all_knowledge.append(knowledge)
                except:
                    continue
        
        return all_knowledge
    
    def generate_creative_response(self, message, base_knowledge):
        """Generate creative response by connecting knowledge - 2-3x longer for think deeper"""
        # Filter out greeting patterns
        filtered_knowledge = [k for k in (base_knowledge or []) 
                             if 'Response pattern' not in k.get('content', '') 
                             and k.get('source') != 'greetings_handler']
        
        if not filtered_knowledge:
            filtered_knowledge = []
        
        # Get connected knowledge
        connected = self.get_connected_knowledge(message)
        # Filter connected knowledge too
        connected = [k for k in connected 
                    if 'Response pattern' not in k.get('content', '') 
                    and k.get('source') != 'greetings_handler']
        
        # Combine all knowledge
        all_knowledge = list({k.get('title', ''): k for k in filtered_knowledge + connected}.values())
        
        if not all_knowledge:
            return None
        
        # Generate 2-3x longer response
        response_parts = []
        
        # Introduction
        intros = [
            "Let me think deeply about this and connect the various aspects I've learned.",
            "This is a fascinating topic. Let me explore it comprehensively by connecting what I know.",
            "I'll provide a thorough analysis by connecting multiple perspectives on this topic.",
            "Let me dive deep and connect the dots across different areas of knowledge."
        ]
        response_parts.append(random.choice(intros))
        
        # Main content - use 3-5 knowledge pieces for longer response
        for i, k in enumerate(all_knowledge[:5]):
            content = k.get('content', '').strip()
            if not content or len(content) < 20:
                continue
            
            # Clean incomplete sentences
            if not content.endswith(('.', '!', '?', '...')):
                last_period = content.rfind('.')
                if last_period > len(content) * 0.5:
                    content = content[:last_period + 1]
            
            if i == 0:
                response_parts.append(f"\n\n{content[:400]}")
            elif i == 1:
                response_parts.append(f"\n\nFurthermore, {content[:350]}")
            elif i == 2:
                response_parts.append(f"\n\nAdditionally, this relates to {content[:300]}")
            else:
                response_parts.append(f"\n\nAnother important aspect: {content[:250]}")
        
        # Conclusion
        if len(all_knowledge) > 1:
            conclusions = [
                "\n\nThese connections show how different concepts interrelate.",
                "\n\nBy connecting these ideas, we can see a more complete picture.",
                "\n\nThese various perspectives help provide a comprehensive understanding."
            ]
            response_parts.append(random.choice(conclusions))
        
        return " ".join(response_parts)
    
    def enhance_with_connections(self, message, base_response):
        """Enhance response with creative keyword connections - but only if relevant"""
        # Don't enhance if base_response looks corrupted
        if base_response:
            words = base_response.lower().split()
            # Check for excessive repetition
            if len(words) > 3:
                for i in range(len(words) - 2):
                    if words[i] == words[i+1] == words[i+2]:
                        # Corrupted response, don't enhance
                        print("[Creative] Detected corrupted base response, skipping enhancement")
                        return base_response
                
                # Check for nonsensical patterns
                for i in range(len(words) - 3):
                    if words[i] == words[i+2] and words[i+1] == words[i+3]:
                        print("[Creative] Detected nonsensical pattern, skipping enhancement")
                        return base_response
        
        # Only enhance if base response is actually answering the question
        if not base_response or len(base_response.strip()) < 30:
            return base_response
        
        # Check if base_response actually answers the question
        message_lower = message.lower()
        # Extract key entity from question (usually the last meaningful word)
        meaningful_words = [w for w in message_lower.split() 
                           if len(w) > 2 and w not in {'what', 'is', 'a', 'an', 'the', 'how', 'why'}]
        if meaningful_words:
            key_entity = meaningful_words[-1]
            # Check if base_response mentions the key entity
            if key_entity not in base_response.lower()[:200]:
                # Response doesn't seem to answer the question, don't add connections
                print(f"[Creative] Base response doesn't mention key entity '{key_entity}', skipping enhancement")
                return base_response
        
        # Don't use get_connected_knowledge here - it pulls in too many unrelated topics
        # Instead, just return the base response without adding unrelated connections
        # The semantic scorer should handle relevance filtering at a higher level
        return base_response


# Global instance
_creative_generator = None

def get_creative_generator():
    """Get or create global creative generator"""
    global _creative_generator
    if _creative_generator is None:
        _creative_generator = CreativeResponseGenerator()
    return _creative_generator

