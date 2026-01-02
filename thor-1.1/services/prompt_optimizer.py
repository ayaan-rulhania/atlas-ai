"""
Prompt Optimizer Service.
Provides systematic prompt templates, few-shot learning, and prompt optimization.
"""
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Represents a prompt template with metadata."""

    def __init__(self, name: str, template: str, task_type: str, variables: List[str],
                 description: str = "", examples: Optional[List[Dict]] = None):
        self.name = name
        self.template = template
        self.task_type = task_type
        self.variables = variables
        self.description = description
        self.examples = examples or []
        self.performance_score = 0.0
        self.usage_count = 0

    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable in template {self.name}: {e}")
            return self.template

    def add_example(self, input_text: str, output_text: str, quality_score: float = 1.0):
        """Add a few-shot example."""
        self.examples.append({
            'input': input_text,
            'output': output_text,
            'quality_score': quality_score,
            'added_at': datetime.now().isoformat()
        })


class FewShotExampleSelector:
    """Selects relevant few-shot examples for a query."""

    def __init__(self):
        self.embedding_cache = {}
        self.similarity_threshold = 0.7

    def select_examples(self, query: str, examples: List[Dict],
                       max_examples: int = 3, method: str = "similarity") -> List[Dict]:
        """
        Select the most relevant few-shot examples for a query.

        Args:
            query: The input query
            examples: List of example dictionaries with 'input' and 'output' keys
            max_examples: Maximum number of examples to return
            method: Selection method ("similarity", "random", "recent")

        Returns:
            List of selected examples
        """
        if not examples:
            return []

        if method == "random":
            import random
            return random.sample(examples, min(max_examples, len(examples)))

        elif method == "recent":
            # Sort by recency (if available)
            sorted_examples = sorted(
                examples,
                key=lambda x: x.get('added_at', '2000-01-01'),
                reverse=True
            )
            return sorted_examples[:max_examples]

        elif method == "similarity":
            return self._select_by_similarity(query, examples, max_examples)

        else:
            return examples[:max_examples]

    def _select_by_similarity(self, query: str, examples: List[Dict], max_examples: int) -> List[Dict]:
        """Select examples based on semantic similarity to query."""
        query_lower = query.lower()

        scored_examples = []
        for example in examples:
            example_input = example.get('input', '').lower()
            score = self._calculate_similarity_score(query_lower, example_input)
            scored_examples.append((score, example))

        # Sort by similarity score (highest first)
        scored_examples.sort(key=lambda x: x[0], reverse=True)

        return [example for score, example in scored_examples[:max_examples]]

    def _calculate_similarity_score(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts."""
        if not text1 or not text2:
            return 0.0

        # Simple word overlap similarity (in production, use embeddings)
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


class PromptOptimizer:
    """
    Main prompt optimization service with template management and few-shot learning.
    """

    def __init__(self, templates_dir: str = "templates/prompts"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        self.templates: Dict[str, PromptTemplate] = {}
        self.example_selector = FewShotExampleSelector()

        # Built-in templates
        self._load_builtin_templates()
        self._load_custom_templates()

    def _load_builtin_templates(self):
        """Load built-in prompt templates."""
        builtin_templates = {
            "chain_of_thought": PromptTemplate(
                name="chain_of_thought",
                template="""Solve this problem step by step using chain-of-thought reasoning:

Question: {question}

Let me think through this systematically:
1. First, identify the key elements and requirements
2. Break down the problem into manageable steps
3. Apply relevant principles and logic
4. Consider alternative approaches if needed
5. Provide a clear, well-reasoned answer

Step-by-step reasoning:""",
                task_type="reasoning",
                variables=["question"],
                description="Chain-of-thought reasoning for complex problems"
            ),

            "code_explanation": PromptTemplate(
                name="code_explanation",
                template="""Explain this code in a clear, structured way:

Code:
```python
{code}
```

Explanation Structure:
1. **Purpose**: What does this code do?
2. **Key Components**: Break down the main parts
3. **Logic Flow**: How does the execution proceed?
4. **Important Concepts**: Any key programming concepts used
5. **Potential Improvements**: Suggestions for better code

Detailed explanation:""",
                task_type="code",
                variables=["code"],
                description="Structured code explanation with key insights"
            ),

            "creative_writing": PromptTemplate(
                name="creative_writing",
                template="""Write a creative piece based on this prompt:

Prompt: {prompt}
Style: {style}
Length: {length}

Creative writing guidelines:
- Engage the reader's imagination
- Use vivid, descriptive language
- Develop interesting characters or scenarios
- Include sensory details and emotional elements
- Maintain consistent tone and style

Creative piece:""",
                task_type="creative",
                variables=["prompt", "style", "length"],
                description="Creative writing with style and length specifications"
            ),

            "analysis_comparison": PromptTemplate(
                name="analysis_comparison",
                template="""Provide a detailed comparison and analysis:

Topic: {topic}
Compare: {item1} vs {item2}

Comparative Analysis Framework:
1. **Core Differences**: Key distinguishing features
2. **Similarities**: Common elements and shared characteristics
3. **Strengths and Weaknesses**: Pros and cons of each approach
4. **Use Cases**: When to choose one over the other
5. **Recommendations**: Context-dependent guidance

Structured comparison:""",
                task_type="analysis",
                variables=["topic", "item1", "item2"],
                description="Systematic comparison and analysis framework"
            ),

            "technical_explanation": PromptTemplate(
                name="technical_explanation",
                template="""Explain this technical concept clearly and comprehensively:

Concept: {concept}
Audience Level: {audience_level}

Explanation Structure:
1. **Definition**: Clear, concise definition
2. **Context**: Why this concept matters
3. **Components**: Break down into key parts
4. **Examples**: Practical illustrations
5. **Applications**: Real-world use cases
6. **Common Pitfalls**: Things to watch out for

Technical explanation:""",
                task_type="technical",
                variables=["concept", "audience_level"],
                description="Technical concept explanation for different audiences"
            ),

            "problem_solving": PromptTemplate(
                name="problem_solving",
                template="""Solve this problem systematically:

Problem: {problem}
Constraints: {constraints}

Problem-Solving Approach:
1. **Understand**: Restate the problem in your own words
2. **Plan**: Outline your solution strategy
3. **Execute**: Work through the solution step by step
4. **Verify**: Check your answer and consider edge cases
5. **Explain**: Describe your reasoning clearly

Step-by-step solution:""",
                task_type="problem_solving",
                variables=["problem", "constraints"],
                description="Systematic problem-solving framework"
            )
        }

        self.templates.update(builtin_templates)

    def _load_custom_templates(self):
        """Load custom templates from disk."""
        if not self.templates_dir.exists():
            return

        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)

                template = PromptTemplate(
                    name=template_data['name'],
                    template=template_data['template'],
                    task_type=template_data['task_type'],
                    variables=template_data['variables'],
                    description=template_data.get('description', ''),
                    examples=template_data.get('examples', [])
                )

                self.templates[template.name] = template

            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def select_template(self, query: str, task_type: Optional[str] = None) -> PromptTemplate:
        """
        Select the best template for a given query.

        Args:
            query: The input query
            task_type: Optional task type hint

        Returns:
            Best matching template
        """
        query_lower = query.lower()

        # Task type detection
        if task_type is None:
            task_type = self._detect_task_type(query_lower)

        # Filter templates by task type
        candidates = [t for t in self.templates.values() if t.task_type == task_type]

        if not candidates:
            # Fallback to general templates
            candidates = [t for t in self.templates.values() if t.task_type == "general"]

        if not candidates:
            # Ultimate fallback
            return self.templates.get("chain_of_thought", list(self.templates.values())[0])

        # Select based on performance score and usage
        candidates.sort(key=lambda x: (x.performance_score, x.usage_count), reverse=True)

        return candidates[0]

    def _detect_task_type(self, query: str) -> str:
        """Detect task type from query content."""
        query_lower = query.lower()

        # Reasoning patterns
        if any(word in query_lower for word in ['why', 'how does', 'explain why', 'analyze', 'reason']):
            return "reasoning"

        # Code patterns
        if any(word in query_lower for word in ['code', 'function', 'program', 'script', 'implement']):
            return "code"

        # Creative patterns
        if any(word in query_lower for word in ['write', 'create', 'story', 'poem', 'design']):
            return "creative"

        # Analysis patterns
        if any(word in query_lower for word in ['compare', 'versus', 'vs', 'difference', 'analysis']):
            return "analysis"

        # Technical patterns
        if any(word in query_lower for word in ['technical', 'concept', 'principle', 'architecture']):
            return "technical"

        # Problem solving patterns
        if any(word in query_lower for word in ['solve', 'problem', 'calculate', 'find']):
            return "problem_solving"

        return "reasoning"  # Default

    def create_optimized_prompt(
        self,
        query: str,
        template_name: Optional[str] = None,
        include_examples: bool = True,
        max_examples: int = 3,
        **template_vars
    ) -> str:
        """
        Create an optimized prompt with template and few-shot examples.

        Args:
            query: The input query
            template_name: Specific template to use (auto-select if None)
            include_examples: Whether to include few-shot examples
            max_examples: Maximum number of examples to include
            **template_vars: Variables for template formatting

        Returns:
            Optimized prompt string
        """
        # Select template
        if template_name and template_name in self.templates:
            template = self.templates[template_name]
        else:
            template = self.select_template(query)

        # Update template usage
        template.usage_count += 1

        # Prepare template variables
        if 'query' not in template_vars:
            template_vars['query'] = query

        # Format base prompt
        prompt_parts = []

        # Add few-shot examples if requested
        if include_examples and template.examples:
            selected_examples = self.example_selector.select_examples(
                query, template.examples, max_examples
            )

            for example in selected_examples:
                prompt_parts.append(f"Example Input: {example['input']}")
                prompt_parts.append(f"Example Output: {example['output']}\n")

        # Add main template
        prompt_parts.append(template.format(**template_vars))

        return "\n".join(prompt_parts)

    def add_template(self, template: PromptTemplate):
        """Add a new template."""
        self.templates[template.name] = template

        # Save to disk
        template_file = self.templates_dir / f"{template.name}.json"
        template_data = {
            'name': template.name,
            'template': template.template,
            'task_type': template.task_type,
            'variables': template.variables,
            'description': template.description,
            'examples': template.examples
        }

        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)

    def update_template_performance(self, template_name: str, performance_score: float):
        """Update template performance score."""
        if template_name in self.templates:
            template = self.templates[template_name]
            # Exponential moving average for performance tracking
            alpha = 0.1  # Learning rate
            template.performance_score = (1 - alpha) * template.performance_score + alpha * performance_score

    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about template usage and performance."""
        stats = {
            'total_templates': len(self.templates),
            'templates_by_type': defaultdict(int),
            'top_performing': [],
            'most_used': []
        }

        for template in self.templates.values():
            stats['templates_by_type'][template.task_type] += 1

        # Sort templates by performance and usage
        sorted_by_performance = sorted(
            self.templates.values(),
            key=lambda x: x.performance_score,
            reverse=True
        )[:5]

        sorted_by_usage = sorted(
            self.templates.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )[:5]

        stats['top_performing'] = [
            {'name': t.name, 'score': t.performance_score, 'type': t.task_type}
            for t in sorted_by_performance
        ]

        stats['most_used'] = [
            {'name': t.name, 'usage': t.usage_count, 'type': t.task_type}
            for t in sorted_by_usage
        ]

        return dict(stats)


# Global instance
_prompt_optimizer = None


def get_prompt_optimizer(templates_dir: str = "templates/prompts") -> PromptOptimizer:
    """Get or create the global prompt optimizer instance."""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer(templates_dir)
    return _prompt_optimizer
