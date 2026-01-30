"""Response cleaner (lite copy).

This is a dependency-light copy of Thor's response cleaner so that
`chatbot/refinement` can run in serverless deployments where `thor-1.0/`
is not deployed.
"""

from __future__ import annotations

import re
from typing import Optional, Dict, List


class ResponseCleaner:
    """Cleans and validates AI responses to ensure quality output."""

    def __init__(self):
        self.corruption_patterns = [
            r'(\b\w+\b)\s+\1\s+\1',
            r'(i\s+understand\s+i\s+)+',
            r'(\bwhat\s+is\s+)+\s*\1',
            r'(\b\w{2,8}\b\s+){4,}\1',
            r'^(i\s+)+',
            r'(\s+is){3,}',
        ]

        self.wiki_artifacts = [
            r'\([^)]*pronunciation[^)]*\)',
            r'\([^)]*ⓘ[^)]*\)',
            r'\[[\d,]+\]',
            r'\(listen\)',
            r'ⓘ',
            r'\([^)]*Hindi[^)]*:.*?\)',
            r'\([^)]*born[^)]*\)',
            r'/[^/]+/',
            r'\[[a-z]\]',
            r'⟨[^⟩]+⟩',
            r'\u02C8[^\s]*',
            r'[\u0250-\u02AF]+',
        ]

        self.promotional_patterns = [
            r'^(Official|Welcome to|Visit|Click|Shop|Buy|Get|Subscribe|Join)\b.*?(website|now|here|us)\b.*?[-–—]',
            r'- (live|breaking|latest|official|free)',
            r'\b(click here|sign up|subscribe|join now|free trial|buy now)\b',
            r'(Official .* website)',
        ]

    def is_corrupted(self, text: str) -> bool:
        if not text:
            return True
        text_lower = text.lower()
        for pattern in self.corruption_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        words = text_lower.split()
        if len(words) > 5:
            word_counts: Dict[str, int] = {}
            for w in words:
                word_counts[w] = word_counts.get(w, 0) + 1
            common = {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'to', 'of', 'in', 'for', 'with'}
            for w, c in word_counts.items():
                if w not in common and c > len(words) * 0.3:
                    return True
        meaningful = [w for w in words if len(w) > 2]
        if meaningful and len(meaningful) < len(words) * 0.3:
            return True
        return False

    def clean_wikipedia_artifacts(self, text: str) -> str:
        if not text:
            return text
        cleaned = text
        for pattern in self.wiki_artifacts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        cleaned = re.sub(r'\(\s*\)', '', cleaned)
        cleaned = re.sub(r'\[\s*\]', '', cleaned)
        return cleaned.strip()

    def clean_promotional_content(self, text: str) -> str:
        if not text:
            return text
        cleaned = text
        for pattern in self.promotional_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def fix_grammar_issues(self, text: str) -> str:
        if not text:
            return text
        words = text.split()
        if len(words) >= 2 and words[0].lower() == words[1].lower():
            text = ' '.join(words[1:])
        text = re.sub(r'\b(is|are|was|were)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(the)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'^([A-Z][a-z]+)\s+\1\b', r'\1', text)
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        text = re.sub(r'\.{2,}', '.', text)
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        return text.strip()

    def fix_incomplete_sentences(self, text: str) -> str:
        if not text:
            return text
        if not text.rstrip().endswith(('.', '!', '?', '...')):
            last_good_end = -1
            for match in re.finditer(r'[.!?](?:\s|$)', text):
                last_good_end = match.end()
            if last_good_end > len(text) * 0.5:
                text = text[:last_good_end].strip()
            else:
                text = text.rstrip() + '...'
        return text

    def clean_response(self, text: str, query: Optional[str] = None) -> str:
        if not text:
            return text
        if self.is_corrupted(text):
            return ""
        text = self.clean_wikipedia_artifacts(text)
        text = self.clean_promotional_content(text)
        text = self.fix_grammar_issues(text)
        text = self.fix_incomplete_sentences(text)
        text = re.sub(r'\s{2,}', ' ', text).strip()
        return text

    def format_factual_response(self, content: str, entity: Optional[str] = None) -> str:
        if not content:
            return ""
        content = self.clean_response(content)
        content = re.sub(r'^Official\s+\w+.*?website\s*[-–—]?\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^\w+\s+Official.*?[-–—]\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^.*?(live\s+matches|scores|news|highlights|rankings|videos).*?[-–—,]', '', content, flags=re.IGNORECASE)
        if len(content.strip()) < 20:
            return ""
        content = content.strip()
        if content and content[0].islower():
            content = content[0].upper() + content[1:]
        return self.fix_incomplete_sentences(content)


_instance: Optional[ResponseCleaner] = None


def get_response_cleaner() -> ResponseCleaner:
    global _instance
    if _instance is None:
        _instance = ResponseCleaner()
    return _instance
