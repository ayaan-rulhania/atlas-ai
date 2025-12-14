"""
Markdown Handler - Provides markdown processing utilities for Atlas AI.
Handles conversion, validation, and enhancement of markdown content.
"""

import re
from typing import Optional, List, Dict, Any


class MarkdownHandler:
    """
    Handles markdown processing for model responses.
    Provides utilities for parsing, validating, and enhancing markdown.
    """
    
    def __init__(self):
        self.supported_elements = {
            'headers': True,
            'bold': True,
            'italic': True,
            'code_inline': True,
            'code_block': True,
            'lists': True,
            'links': True,
            'images': True,
            'blockquotes': True,
            'tables': True,
        }
    
    def validate_markdown(self, text: str) -> Dict[str, Any]:
        """
        Validate markdown structure and return a report.
        
        Args:
            text: Markdown text to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            'valid': True,
            'warnings': [],
            'elements_found': [],
        }
        
        # Check for unclosed code blocks
        code_blocks = text.count('```')
        if code_blocks % 2 != 0:
            result['valid'] = False
            result['warnings'].append('Unclosed code block detected')
        
        # Check for unclosed bold/italic
        bold_count = len(re.findall(r'\*\*', text))
        if bold_count % 2 != 0:
            result['warnings'].append('Unclosed bold markers detected')
        
        # Identify elements
        if re.search(r'^#+\s', text, re.MULTILINE):
            result['elements_found'].append('headers')
        if re.search(r'\*\*[^*]+\*\*', text):
            result['elements_found'].append('bold')
        if re.search(r'!\[.*\]\(.*\)', text):
            result['elements_found'].append('images')
        if re.search(r'^\s*[-*]\s', text, re.MULTILINE):
            result['elements_found'].append('unordered_lists')
        if re.search(r'^\s*\d+\.\s', text, re.MULTILINE):
            result['elements_found'].append('ordered_lists')
        
        return result
    
    def enhance_markdown(self, text: str) -> str:
        """
        Enhance plain text with markdown formatting.
        
        Args:
            text: Plain text or partially formatted markdown
            
        Returns:
            Enhanced markdown text
        """
        if not text:
            return text
        
        # Fix common markdown issues
        text = self._fix_common_issues(text)
        
        # Enhance formatting
        text = self._enhance_headers(text)
        text = self._enhance_emphasis(text)
        text = self._enhance_lists(text)
        text = self._enhance_code(text)
        
        return text
    
    def _fix_common_issues(self, text: str) -> str:
        """Fix common markdown formatting issues."""
        # Fix headers without space after #
        text = re.sub(r'^(#{1,6})([^#\s])', r'\1 \2', text, flags=re.MULTILINE)
        
        # Fix lists without space after bullet
        text = re.sub(r'^(\s*)[-*]([^\s])', r'\1- \2', text, flags=re.MULTILINE)
        
        # Fix numbered lists without space after period
        text = re.sub(r'^(\s*)(\d+)\.([^\s])', r'\1\2. \3', text, flags=re.MULTILINE)
        
        # Ensure code blocks have language hint if missing
        text = re.sub(r'```\n([^`])', r'```text\n\1', text)
        
        return text
    
    def _enhance_headers(self, text: str) -> str:
        """Add headers where appropriate."""
        lines = text.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip if already a header
            if stripped.startswith('#'):
                result.append(line)
                continue
            
            # Convert lines that look like section titles
            # (Short, ends with colon, followed by content)
            if (stripped.endswith(':') and 
                len(stripped) < 60 and 
                i + 1 < len(lines) and 
                lines[i + 1].strip()):
                
                title = stripped[:-1].strip()
                if title and not any(c.isdigit() for c in title[:3]):
                    result.append(f"### {title}")
                    continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _enhance_emphasis(self, text: str) -> str:
        """Add emphasis to important terms."""
        # Bold key terms that appear before colons
        text = re.sub(
            r'^([A-Z][^:\n]{2,30}):\s',
            r'**\1**: ',
            text,
            flags=re.MULTILINE
        )
        
        # Bold emphasis words
        emphasis_words = [
            'important', 'note', 'warning', 'caution', 'tip',
            'remember', 'key', 'essential', 'critical'
        ]
        
        for word in emphasis_words:
            # Match word not already in bold
            pattern = rf'(?<!\*\*)\b({word})\b(?!\*\*)'
            text = re.sub(pattern, r'**\1**', text, flags=re.IGNORECASE)
        
        return text
    
    def _enhance_lists(self, text: str) -> str:
        """Enhance list formatting."""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            
            # Convert text patterns to proper lists
            # Pattern: starts with letter/number followed by )
            if re.match(r'^[a-zA-Z]\)\s', stripped):
                result.append('- ' + stripped[3:])
            elif re.match(r'^\d\)\s', stripped):
                num = stripped[0]
                result.append(f'{num}. ' + stripped[3:])
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _enhance_code(self, text: str) -> str:
        """Enhance code formatting."""
        # Wrap inline code-like content
        # Match function calls, variables, etc.
        text = re.sub(
            r'`?([a-z_][a-z0-9_]*\([^)]*\))`?',
            r'`\1`',
            text
        )
        
        return text
    
    def strip_markdown(self, text: str) -> str:
        """
        Remove all markdown formatting from text.
        
        Args:
            text: Markdown text
            
        Returns:
            Plain text without markdown
        """
        # Remove code blocks first
        text = re.sub(r'```[\s\S]*?```', '', text)
        
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        
        # Remove blockquotes
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def to_html(self, text: str) -> str:
        """
        Convert markdown to HTML.
        Simple conversion for basic markdown elements.
        
        Args:
            text: Markdown text
            
        Returns:
            HTML string
        """
        html = text
        
        # Escape HTML entities first
        html = html.replace('&', '&amp;')
        html = html.replace('<', '&lt;')
        html = html.replace('>', '&gt;')
        
        # Code blocks
        html = re.sub(
            r'```(\w+)?\n([\s\S]*?)```',
            r'<pre class="code-block"><code class="language-\1">\2</code></pre>',
            html
        )
        
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', html)
        
        # Headers
        html = re.sub(r'^### (.*?)$', r'<h3 class="md-h3">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2 class="md-h2">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1 class="md-h1">\1</h1>', html, flags=re.MULTILINE)
        
        # Bold
        html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
        
        # Images
        html = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<div class="md-image"><img src="\2" alt="\1" loading="lazy"></div>',
            html
        )
        
        # Links
        html = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2" target="_blank" rel="noopener">\1</a>',
            html
        )
        
        # Line breaks
        html = html.replace('\n\n', '</p><p class="md-p">')
        html = f'<p class="md-p">{html}</p>'
        
        return html


# Singleton instance
_handler_instance = None


def get_markdown_handler() -> MarkdownHandler:
    """Get the singleton MarkdownHandler instance."""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = MarkdownHandler()
    return _handler_instance
