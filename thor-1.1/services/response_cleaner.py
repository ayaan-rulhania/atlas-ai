"""
Response Cleaner - Cleans, validates, and fixes AI-generated responses
Handles: grammar issues, duplications, Wikipedia artifacts, corrupted output, etc.
"""
import re
from typing import Optional, Tuple, Dict, List


class ResponseCleaner:
    """Cleans and validates AI responses to ensure quality output"""
    
    def __init__(self):
        # Patterns indicating corrupted/garbled output
        self.corruption_patterns = [
            # Repetitive phrases
            r'(\b\w+\b)\s+\1\s+\1',  # Same word 3+ times
            r'(i\s+understand\s+i\s+)+',  # "i understand i" repetition
            r'(\bwhat\s+is\s+)+\s*\1',  # "what is what is" pattern
            r'(\b\w{2,8}\b\s+){4,}\1',  # Any word repeated 4+ times
            r'^(i\s+)+',  # Starting with repeated "i"
            r'(\s+is){3,}',  # Multiple "is" in a row
        ]
        
        # Wikipedia formatting artifacts to remove
        self.wiki_artifacts = [
            r'\([^)]*pronunciation[^)]*\)',  # (pronunciation: ...)
            r'\([^)]*ⓘ[^)]*\)',  # Info symbols
            r'\[[\d,]+\]',  # [1], [2], [1,2] citation markers
            r'\(listen\)',  # (listen) audio links
            r'ⓘ',  # Info symbol standalone
            r'\([^)]*Hindi[^)]*:.*?\)',  # Hindi pronunciation
            r'\([^)]*born[^)]*\)',  # (born ...) - we'll handle dates separately
            r'/[^/]+/',  # /pronunciation guides/
            r'\[[a-z]\]',  # [a], [b] footnote markers
            r'⟨[^⟩]+⟩',  # ⟨phonetic⟩ markers
            r'\u02C8[^\s]*',  # IPA stress marks and following phonetics
            r'[\u0250-\u02AF]+',  # IPA characters
        ]
        
        # Promotional/ad copy patterns
        self.promotional_patterns = [
            r'^(Official|Welcome to|Visit|Click|Shop|Buy|Get|Subscribe|Join)\b.*?(website|now|here|us)\b.*?[-–—]',
            r'- (live|breaking|latest|official|free)',
            r'\b(click here|sign up|subscribe|join now|free trial|buy now)\b',
            r'(Official .* website)',
        ]
        
        # Patterns for extracting clean biographical info
        self.bio_patterns = {
            'person_is': r'^([A-Z][^.]+)\s+(is|was)\s+(an?\s+)?(\w+)',
            'born': r'born\s+(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4})',
            'occupation': r'is\s+(an?\s+)?([A-Z][\w\s]+(?:actor|cricketer|politician|singer|writer|scientist|player|engineer|doctor|artist|musician))',
        }
    
    def is_corrupted(self, text: str) -> bool:
        """Check if text appears corrupted/garbled"""
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Check for corruption patterns
        for pattern in self.corruption_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Check for excessive repetition of any word
        words = text_lower.split()
        if len(words) > 5:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # If any non-common word appears more than 30% of the time, likely corrupted
            common_words = {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'to', 'of', 'in', 'for', 'with'}
            for word, count in word_counts.items():
                if word not in common_words and count > len(words) * 0.3:
                    return True
        
        # Check if mostly nonsensical (too few real words)
        meaningful_words = [w for w in words if len(w) > 2]
        if len(meaningful_words) < len(words) * 0.3:
            return True
        
        return False
    
    def clean_wikipedia_artifacts(self, text: str) -> str:
        """Remove Wikipedia-specific formatting and artifacts"""
        if not text:
            return text
        
        cleaned = text
        
        # Remove wiki artifacts
        for pattern in self.wiki_artifacts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up resulting double spaces
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        
        # Clean up orphaned parentheses
        cleaned = re.sub(r'\(\s*\)', '', cleaned)
        cleaned = re.sub(r'\[\s*\]', '', cleaned)
        
        return cleaned.strip()
    
    def clean_promotional_content(self, text: str) -> str:
        """Remove promotional/ad copy content"""
        if not text:
            return text
        
        cleaned = text
        
        for pattern in self.promotional_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def fix_grammar_issues(self, text: str) -> str:
        """Fix common grammar issues in generated text"""
        if not text:
            return text
        
        # Fix duplicate words at start
        # "Physics Physics is" -> "Physics is"
        words = text.split()
        if len(words) >= 2 and words[0].lower() == words[1].lower():
            text = ' '.join(words[1:])
        
        # Fix "X is is" -> "X is"
        text = re.sub(r'\b(is|are|was|were)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        
        # Fix multiple consecutive "the"
        text = re.sub(r'\b(the)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        
        # Fix "He he" or "She she" at sentence start
        text = re.sub(r'^([A-Z][a-z]+)\s+\1\b', r'\1', text)
        
        # Fix sentence starting with lowercase after punctuation
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Fix multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        # Ensure first letter is capitalized
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text.strip()
    
    def fix_incomplete_sentences(self, text: str) -> str:
        """Fix incomplete or cut-off sentences"""
        if not text:
            return text
        
        # If text doesn't end with proper punctuation, try to find last complete sentence
        if not text.rstrip().endswith(('.', '!', '?', '...')):
            # Find last period that's not in abbreviation
            last_good_end = -1
            for match in re.finditer(r'[.!?](?:\s|$)', text):
                last_good_end = match.end()
            
            if last_good_end > len(text) * 0.5:  # If we have at least half the text
                text = text[:last_good_end].strip()
            else:
                # Add ellipsis if we can't find good ending
                text = text.rstrip() + '...'
        
        return text
    
    def extract_biographical_info(self, text: str, person_name: str) -> Optional[str]:
        """Extract clean biographical information for 'who is X' questions"""
        if not text or not person_name:
            return None
        
        # Look for "Person is..." pattern
        name_pattern = re.escape(person_name.split()[-1])  # Use last name
        bio_match = re.search(
            rf'{name_pattern}[^.]*\s+(is|was)\s+[^.]+\.', 
            text, 
            re.IGNORECASE
        )
        
        if bio_match:
            return bio_match.group(0)
        
        return None
    
    def clean_response(self, text: str, query: Optional[str] = None) -> str:
        """
        Main cleaning function - applies all cleaning steps.
        
        Args:
            text: The response text to clean
            query: Optional original query for context-aware cleaning
        
        Returns:
            Cleaned response text
        """
        if not text:
            return text
        
        # Step 1: Check for corruption
        if self.is_corrupted(text):
            # If corrupted, we can't use this response
            return ""
        
        # Step 2: Clean Wikipedia artifacts
        text = self.clean_wikipedia_artifacts(text)
        
        # Step 3: Clean promotional content
        text = self.clean_promotional_content(text)
        
        # Step 4: Fix grammar issues
        text = self.fix_grammar_issues(text)
        
        # Step 5: Fix incomplete sentences
        text = self.fix_incomplete_sentences(text)
        
        # Step 6: Final cleanup
        text = re.sub(r'\s{2,}', ' ', text)  # Multiple spaces
        text = text.strip()
        
        return text
    
    def synthesize_definition_response(
        self, 
        entity: str, 
        knowledge_items: List[Dict],
        query_intent: Optional[Dict] = None
    ) -> str:
        """
        Synthesize a proper definition response from knowledge items.
        Handles "What is X?" questions properly.
        """
        if not knowledge_items:
            return ""
        
        # Collect and clean all content
        cleaned_contents = []
        for item in knowledge_items[:3]:  # Use top 3
            content = item.get('content', '')
            cleaned = self.clean_response(content)
            if cleaned and len(cleaned) > 20:
                cleaned_contents.append(cleaned)
        
        if not cleaned_contents:
            return ""
        
        # Build definition response
        main_content = cleaned_contents[0]
        
        # Check if content already starts with entity name or definition
        entity_lower = entity.lower()
        content_lower = main_content.lower()
        
        # Avoid "Physics is Physics is..." duplication
        if content_lower.startswith(entity_lower):
            # Content already has the entity name
            response = main_content
        elif 'is ' in content_lower[:50] or 'are ' in content_lower[:50]:
            # Content has a definition structure
            response = f"**{entity.title()}** {main_content}"
        else:
            # Need to add definition structure
            response = f"**{entity.title()}** is {main_content}"
        
        # Clean up "X is is" type errors
        response = re.sub(rf'\*\*{re.escape(entity.title())}\*\*\s+is\s+{re.escape(entity.lower())}\s+is\s+', 
                         f'**{entity.title()}** is ', response, flags=re.IGNORECASE)
        
        # Add example if we have more content
        if len(cleaned_contents) > 1:
            additional = cleaned_contents[1]
            # Only add if it adds new information
            if len(additional) > 30 and additional[:50].lower() not in content_lower:
                response += f" {additional[:200]}"
        
        return self.fix_grammar_issues(response)
    
    def synthesize_biographical_response(
        self, 
        person_name: str, 
        knowledge_items: List[Dict]
    ) -> str:
        """
        Synthesize a proper biographical response for 'Who is X?' questions.
        Prioritizes identity/profession over trivia.
        """
        if not knowledge_items:
            return ""
        
        # Categories of information to extract
        identity_info = []  # Who they are (profession, nationality)
        career_info = []    # What they do/did
        trivia_info = []    # Other facts
        
        person_lower = person_name.lower()
        last_name_lower = person_name.split()[-1].lower() if person_name.split() else person_lower
        
        for item in knowledge_items:
            content = item.get('content', '')
            content_lower = content.lower()
            cleaned = self.clean_response(content)
            
            if not cleaned or len(cleaned) < 20:
                continue
            
            # Check if content is about the person (not just mentions them)
            is_about_person = (
                person_lower in content_lower[:100] or 
                last_name_lower in content_lower[:50]
            )
            
            if not is_about_person:
                continue
            
            # Categorize content
            # Identity: "X is a [profession]" or "X was born"
            if re.search(rf'{last_name_lower}\s+(is|was)\s+(an?\s+)?[\w\s]+(actor|cricketer|player|singer|politician|scientist|writer|artist|musician|director|producer|businessman)', 
                        content_lower):
                identity_info.append(cleaned)
            # Career: achievements, roles, work
            elif any(word in content_lower for word in ['played', 'starred', 'won', 'award', 'career', 'known for', 'famous for']):
                career_info.append(cleaned)
            # Trivia: anecdotes, stories
            elif any(word in content_lower for word in ['once', 'anecdote', 'story', 'failed', 'revealed', 'shared']):
                trivia_info.append(cleaned)
            else:
                # Default to identity if starts with person's name
                if content_lower.strip().startswith(last_name_lower) or content_lower.strip().startswith(person_lower):
                    identity_info.append(cleaned)
                else:
                    trivia_info.append(cleaned)
        
        # Build response prioritizing identity > career > trivia
        response_parts = []
        
        # Always start with identity
        if identity_info:
            main_identity = identity_info[0]
            # Clean up and format
            if not main_identity.lower().startswith(person_lower):
                main_identity = f"**{person_name}** {main_identity}"
            else:
                # Bold the name
                main_identity = re.sub(
                    rf'^({re.escape(person_name)})', 
                    rf'**{person_name}**', 
                    main_identity, 
                    flags=re.IGNORECASE
                )
            response_parts.append(main_identity)
        
        # Add career info if space allows
        if career_info and len(' '.join(response_parts)) < 400:
            response_parts.append(career_info[0][:200])
        
        # Only add trivia if we don't have better info
        if not identity_info and not career_info and trivia_info:
            # For trivia, provide context
            response_parts.append(f"About {person_name}: {trivia_info[0][:200]}")
        
        if not response_parts:
            return ""
        
        response = ' '.join(response_parts)
        return self.fix_grammar_issues(response)
    
    def format_factual_response(self, content: str, entity: Optional[str] = None) -> str:
        """
        Format a factual response with proper structure.
        Removes website descriptions and focuses on actual content.
        """
        if not content:
            return ""
        
        # Clean the content first
        content = self.clean_response(content)
        
        # Remove website descriptions like "Official ICC Cricket website - live matches, scores..."
        content = re.sub(r'^Official\s+\w+.*?website\s*[-–—]?\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^\w+\s+Official.*?[-–—]\s*', '', content, flags=re.IGNORECASE)
        
        # Remove list-style website content
        content = re.sub(r'^.*?(live\s+matches|scores|news|highlights|rankings|videos).*?[-–—,]', '', content, flags=re.IGNORECASE)
        
        # If content is now too short, it was probably just a website description
        if len(content.strip()) < 20:
            return ""
        
        # Clean up and return
        content = content.strip()
        if content and content[0].islower():
            content = content[0].upper() + content[1:]
        
        return self.fix_incomplete_sentences(content)


# Global instance
_response_cleaner = None

def get_response_cleaner():
    """Get or create global response cleaner instance"""
    global _response_cleaner
    if _response_cleaner is None:
        _response_cleaner = ResponseCleaner()
    return _response_cleaner

