"""
Response Formatter - Handles rich text formatting for Atlas AI responses.
Provides utilities for formatting responses with headers, bold, lists, code blocks, etc.
"""

import re
from typing import Optional, Dict, List, Any


class ResponseFormatter:
    """
    Formats model responses with rich text styling.
    Converts plain text responses into well-structured markdown.
    """
    
    def __init__(self):
        self.formatting_rules = {
            'auto_headers': True,
            'auto_lists': True,
            'auto_bold_keywords': True,
            'auto_code_blocks': True,
        }
    
    def format_response(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Apply rich formatting to a response.
        
        Args:
            text: Raw response text
            context: Optional context dict with hints (e.g., response_type)
            
        Returns:
            Formatted response with markdown styling
        """
        if not text:
            return text
        
        context = context or {}
        response_type = context.get('response_type', 'general')
        
        # Apply formatters based on response type
        if response_type == 'explanation':
            text = self._format_explanation(text)
        elif response_type == 'list':
            text = self._format_list_response(text)
        elif response_type == 'code':
            text = self._format_code_response(text)
        elif response_type == 'image':
            # Image responses handled separately
            pass
        else:
            # General formatting
            text = self._format_general(text)
        
        return text
    
    def _format_general(self, text: str) -> str:
        """Apply general formatting improvements."""
        # Bold important keywords
        text = self._auto_bold_keywords(text)
        
        # Convert numbered items to proper lists
        text = self._auto_format_lists(text)
        
        # Add headers for sections
        text = self._auto_add_headers(text)
        
        return text
    
    def _format_explanation(self, text: str) -> str:
        """Format explanatory content with structure."""
        lines = text.split('\n')
        formatted = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                formatted.append('')
                continue
            
            # Add header styling for first substantial line
            if i == 0 and len(line) < 100 and not line.startswith('#'):
                # Check if it looks like a title
                if not any(p in line.lower() for p in ['is a', 'are', 'the', 'this is']):
                    formatted.append(f"## {line}")
                    continue
            
            formatted.append(line)
        
        text = '\n'.join(formatted)
        text = self._auto_bold_keywords(text)
        return text
    
    def _format_list_response(self, text: str) -> str:
        """Format list-type responses."""
        lines = text.split('\n')
        formatted = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # Detect list patterns
            if re.match(r'^(\d+[\.\)]\s|[-•*]\s)', stripped):
                in_list = True
                # Normalize bullet points
                stripped = re.sub(r'^(\d+)[\.\)]\s', r'\1. ', stripped)
                stripped = re.sub(r'^[-•]\s', '- ', stripped)
                formatted.append(stripped)
            elif in_list and stripped and not stripped.endswith(':'):
                # Continue as list item if indented
                formatted.append(f"  {stripped}")
            else:
                in_list = False
                formatted.append(stripped)
        
        return '\n'.join(formatted)
    
    def _format_code_response(self, text: str) -> str:
        """Format code-related responses."""
        # Ensure code blocks are properly formatted
        if '```' not in text and self._contains_code(text):
            # Wrap detected code in code blocks
            text = self._auto_wrap_code(text)
        
        return text
    
    def _auto_bold_keywords(self, text: str) -> str:
        """Automatically bold important keywords and phrases."""
        # Keywords to emphasize
        keywords = [
            'important', 'note', 'warning', 'tip', 'remember',
            'key', 'essential', 'critical', 'example', 'summary'
        ]
        
        for keyword in keywords:
            # Case-insensitive match, preserve original case
            pattern = rf'\b({keyword})\b'
            text = re.sub(pattern, r'**\1**', text, flags=re.IGNORECASE)
        
        # Bold phrases after ":" that look like key terms
        text = re.sub(r':\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', r': **\1**', text)
        
        return text
    
    def _auto_format_lists(self, text: str) -> str:
        """Convert implicit lists to proper markdown lists."""
        lines = text.split('\n')
        formatted = []
        
        for line in lines:
            stripped = line.strip()
            
            # Convert "1)" or "1." at start to proper numbered list
            if re.match(r'^\d+[\)\.](?!\d)', stripped):
                stripped = re.sub(r'^(\d+)[\)\.]', r'\1.', stripped)
            
            # Convert "- " style bullets
            if stripped.startswith('- ') or stripped.startswith('* '):
                stripped = '- ' + stripped[2:]
            
            formatted.append(stripped)
        
        return '\n'.join(formatted)
    
    def _auto_add_headers(self, text: str) -> str:
        """Add markdown headers to section titles."""
        lines = text.split('\n')
        formatted = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect section-like headers (short lines ending with ":")
            if (stripped.endswith(':') and 
                len(stripped) < 50 and 
                not stripped.startswith('-') and
                not stripped.startswith('#')):
                
                # Remove trailing colon and make it a header
                header_text = stripped[:-1].strip()
                if header_text and not any(c.isdigit() for c in header_text[:2]):
                    formatted.append(f"\n### {header_text}")
                    continue
            
            formatted.append(line)
        
        return '\n'.join(formatted)
    
    def _contains_code(self, text: str) -> bool:
        """Check if text contains code-like content."""
        code_indicators = [
            r'function\s+\w+',
            r'def\s+\w+',
            r'class\s+\w+',
            r'import\s+\w+',
            r'const\s+\w+',
            r'let\s+\w+',
            r'var\s+\w+',
            r'\{[\s\S]*\}',
            r'return\s+',
            r'if\s*\(',
            r'for\s*\(',
            r'while\s*\(',
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, text):
                return True
        return False
    
    def _auto_wrap_code(self, text: str) -> str:
        """Wrap detected code blocks in markdown code fences."""
        # Simple heuristic: wrap lines that look like code
        lines = text.split('\n')
        formatted = []
        in_code = False
        code_block = []
        
        for line in lines:
            looks_like_code = bool(re.match(
                r'^\s*(def |class |function |import |const |let |var |if\s*\(|for\s*\(|while\s*\(|\{|\}|return )',
                line
            ))
            
            if looks_like_code:
                if not in_code:
                    in_code = True
                    formatted.append('```')
                code_block.append(line)
            else:
                if in_code:
                    formatted.extend(code_block)
                    formatted.append('```')
                    code_block = []
                    in_code = False
                formatted.append(line)
        
        if in_code:
            formatted.extend(code_block)
            formatted.append('```')
        
        return '\n'.join(formatted)
    
    def format_with_template(self, text: str, template_type: str) -> str:
        """
        Format response using a predefined template.
        
        Args:
            text: Response text
            template_type: One of 'greeting', 'answer', 'error', 'info'
            
        Returns:
            Formatted response
        """
        templates = {
            'greeting': self._template_greeting,
            'answer': self._template_answer,
            'error': self._template_error,
            'info': self._template_info,
        }
        
        formatter = templates.get(template_type, self._template_answer)
        return formatter(text)
    
    def _template_greeting(self, text: str) -> str:
        """Format a greeting response."""
        return f"👋 {text}"
    
    def _template_answer(self, text: str) -> str:
        """Format a standard answer response."""
        return self._format_general(text)
    
    def _template_error(self, text: str) -> str:
        """Format an error response."""
        return f"⚠️ **Error**: {text}"
    
    def _template_info(self, text: str) -> str:
        """Format an informational response."""
        return f"ℹ️ {text}"


# Singleton instance
_formatter_instance = None


def get_response_formatter() -> ResponseFormatter:
    """Get the singleton ResponseFormatter instance."""
    global _formatter_instance
    if _formatter_instance is None:
        _formatter_instance = ResponseFormatter()
    return _formatter_instance
