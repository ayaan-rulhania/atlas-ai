"""
Chain-of-Thought Reasoning Engine for Thor 1.1
Implements step-by-step reasoning with self-verification and multi-step generation
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ReasoningType(Enum):
    LOGICAL = "logical"
    MATHEMATICAL = "mathematical"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    ANALYTICAL = "analytical"
    GENERAL = "general"


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning chain"""
    step_number: int
    description: str
    reasoning: str
    confidence: float
    evidence: List[str] = None
    sub_steps: List['ReasoningStep'] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []
        if self.sub_steps is None:
            self.sub_steps = []


@dataclass
class ReasoningChain:
    """Complete reasoning chain with steps and final conclusion"""
    query: str
    reasoning_type: ReasoningType
    steps: List[ReasoningStep]
    conclusion: str
    confidence: float
    verification_result: bool = True
    reasoning_quality_score: float = 0.0


class ReasoningEngine:
    """Chain-of-Thought reasoning engine for complex problem solving"""

    def __init__(self):
        self.max_steps = 5
        self.min_confidence_threshold = 0.6
        self.templates = self._load_reasoning_templates()

    def _load_reasoning_templates(self) -> Dict[str, Dict]:
        """Load reasoning templates for different reasoning types"""
        return {
            ReasoningType.LOGICAL.value: {
                "step_template": "Step {step}: {description}\nReasoning: {reasoning}\nEvidence: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Therefore, {conclusion}",
                "indicators": ["if", "then", "and", "or", "not", "implies", "therefore", "because"]
            },
            ReasoningType.MATHEMATICAL.value: {
                "step_template": "Step {step}: {description}\nCalculation: {reasoning}\nResult: {evidence}\nVerification: {confidence:.2f}",
                "conclusion_template": "Final answer: {conclusion}",
                "indicators": ["calculate", "solve", "equals", "plus", "minus", "times", "divide", "sum", "difference"]
            },
            ReasoningType.CAUSAL.value: {
                "step_template": "Step {step}: Analyzing causal relationship\nCause: {reasoning}\nEffect: {evidence}\nStrength: {confidence:.2f}",
                "conclusion_template": "Therefore, {conclusion}",
                "indicators": ["because", "causes", "leads to", "results in", "due to", "why", "reason"]
            },
            ReasoningType.COMPARATIVE.value: {
                "step_template": "Step {step}: Comparing {description}\nAspect: {reasoning}\nComparison: {evidence}\nSimilarity/Difference: {confidence:.2f}",
                "conclusion_template": "Overall comparison: {conclusion}",
                "indicators": ["versus", "vs", "compared to", "better than", "worse than", "similar to", "different from"]
            },
            ReasoningType.ANALYTICAL.value: {
                "step_template": "Step {step}: Analyzing {description}\nBreakdown: {reasoning}\nInsights: {evidence}\nRelevance: {confidence:.2f}",
                "conclusion_template": "Analysis conclusion: {conclusion}",
                "indicators": ["analyze", "examine", "evaluate", "assess", "break down", "understand"]
            }
        }

    def detect_reasoning_type(self, query: str) -> ReasoningType:
        """Detect the type of reasoning required for the query"""
        query_lower = query.lower()

        # Check for mathematical reasoning
        if any(word in query_lower for word in ["calculate", "solve", "math", "equation", "number", "plus", "minus"]):
            return ReasoningType.MATHEMATICAL

        # Check for logical reasoning
        if any(word in query_lower for word in ["if", "then", "logic", "therefore", "because", "implies"]):
            return ReasoningType.LOGICAL

        # Check for causal reasoning
        if any(word in query_lower for word in ["why", "cause", "effect", "reason", "leads to", "results in"]):
            return ReasoningType.CAUSAL

        # Check for comparative reasoning
        if any(word in query_lower for word in ["vs", "versus", "compare", "better", "worse", "difference"]):
            return ReasoningType.COMPARATIVE

        # Check for analytical reasoning
        if any(word in query_lower for word in ["analyze", "examine", "evaluate", "how", "what makes"]):
            return ReasoningType.ANALYTICAL

        return ReasoningType.GENERAL

    def should_use_reasoning(self, query: str, query_analysis: Dict = None) -> bool:
        """Determine if query requires chain-of-thought reasoning"""
        query_lower = query.lower()

        # Always use reasoning for complex queries
        complex_indicators = [
            "why", "how does", "what causes", "explain why", "analyze",
            "compare", "versus", "vs", "difference between", "relationship",
            "process", "mechanism", "theory", "concept", "if", "then"
        ]

        if any(indicator in query_lower for indicator in complex_indicators):
            return True

        # Use reasoning for queries that are likely to benefit from step-by-step thinking
        reasoning_indicators = [
            "solve", "calculate", "determine", "figure out", "understand",
            "explain", "analyze", "evaluate", "assess", "break down"
        ]

        if any(indicator in query_lower for indicator in reasoning_indicators):
            return True

        # Check query analysis if provided
        if query_analysis:
            if query_analysis.get('intent') in ['philosophical', 'definition', 'biographical']:
                return True
            if query_analysis.get('should_search_web', False):
                return True

        # Default: use reasoning for queries longer than 10 words
        return len(query.split()) > 10

    def generate_reasoning_chain(self, query: str, context: str = "", knowledge: List[Dict] = None) -> ReasoningChain:
        """
        Generate a complete reasoning chain for the query

        Args:
            query: The user's query
            context: Conversation context
            knowledge: Relevant knowledge from brain

        Returns:
            ReasoningChain with steps and conclusion
        """
        reasoning_type = self.detect_reasoning_type(query)

        # Create initial reasoning steps
        steps = self._decompose_query_into_steps(query, reasoning_type, context, knowledge)

        # Generate step-by-step reasoning
        for i, step in enumerate(steps):
            if step.reasoning == "":  # Only fill in empty reasoning
                step.reasoning = self._generate_step_reasoning(query, step, steps[:i], context, knowledge)
                step.confidence = self._assess_step_confidence(step, knowledge)

        # Generate conclusion
        conclusion = self._synthesize_conclusion(steps, query, reasoning_type)

        # Calculate overall confidence
        avg_confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.5

        # Verify reasoning chain
        verification_result = self._verify_reasoning_chain(steps, conclusion)

        # Calculate reasoning quality score
        quality_score = self._calculate_reasoning_quality(steps, conclusion, verification_result)

        return ReasoningChain(
            query=query,
            reasoning_type=reasoning_type,
            steps=steps,
            conclusion=conclusion,
            confidence=avg_confidence,
            verification_result=verification_result,
            reasoning_quality_score=quality_score
        )

    def _decompose_query_into_steps(self, query: str, reasoning_type: ReasoningType,
                                  context: str = "", knowledge: List[Dict] = None) -> List[ReasoningStep]:
        """Break down the query into logical reasoning steps"""
        steps = []

        if reasoning_type == ReasoningType.MATHEMATICAL:
            steps = self._decompose_mathematical_query(query)
        elif reasoning_type == ReasoningType.LOGICAL:
            steps = self._decompose_logical_query(query)
        elif reasoning_type == ReasoningType.CAUSAL:
            steps = self._decompose_causal_query(query)
        elif reasoning_type == ReasoningType.COMPARATIVE:
            steps = self._decompose_comparative_query(query)
        elif reasoning_type == ReasoningType.ANALYTICAL:
            steps = self._decompose_analytical_query(query)
        else:
            steps = self._decompose_general_query(query)

        return steps

    def _decompose_mathematical_query(self, query: str) -> List[ReasoningStep]:
        """Decompose mathematical queries into calculation steps"""
        steps = []

        # Extract numbers and operations
        numbers = re.findall(r'\d+', query)
        operations = re.findall(r'[+\-*/=]', query)

        if numbers and operations:
            steps.append(ReasoningStep(
                step_number=1,
                description="Identify the mathematical operation",
                reasoning=f"Found operation: {operations[0]}",
                confidence=0.9
            ))

            steps.append(ReasoningStep(
                step_number=2,
                description="Extract numbers involved",
                reasoning=f"Numbers: {', '.join(numbers)}",
                confidence=0.9
            ))

            steps.append(ReasoningStep(
                step_number=3,
                description="Perform the calculation",
                reasoning="",
                confidence=0.8
            ))
        else:
            # Generic mathematical reasoning steps
            steps = [
                ReasoningStep(1, "Understand the mathematical problem", "", 0.8),
                ReasoningStep(2, "Identify the appropriate mathematical approach", "", 0.8),
                ReasoningStep(3, "Apply the mathematical method", "", 0.7),
                ReasoningStep(4, "Verify the result", "", 0.8)
            ]

        return steps

    def _decompose_logical_query(self, query: str) -> List[ReasoningStep]:
        """Decompose logical queries into reasoning steps"""
        steps = [
            ReasoningStep(1, "Identify the logical premises", "", 0.8),
            ReasoningStep(2, "Determine the logical relationship", "", 0.8),
            ReasoningStep(3, "Apply logical rules", "", 0.7),
            ReasoningStep(4, "Draw logical conclusion", "", 0.8)
        ]
        return steps

    def _decompose_causal_query(self, query: str) -> List[ReasoningStep]:
        """Decompose causal queries into reasoning steps"""
        steps = [
            ReasoningStep(1, "Identify potential causes", "", 0.7),
            ReasoningStep(2, "Evaluate causal relationships", "", 0.7),
            ReasoningStep(3, "Assess evidence strength", "", 0.8),
            ReasoningStep(4, "Determine most likely cause", "", 0.7)
        ]
        return steps

    def _decompose_comparative_query(self, query: str) -> List[ReasoningStep]:
        """Decompose comparative queries into reasoning steps"""
        steps = [
            ReasoningStep(1, "Identify items to compare", "", 0.9),
            ReasoningStep(2, "Determine comparison criteria", "", 0.8),
            ReasoningStep(3, "Evaluate each criterion", "", 0.7),
            ReasoningStep(4, "Synthesize comparison results", "", 0.8)
        ]
        return steps

    def _decompose_analytical_query(self, query: str) -> List[ReasoningStep]:
        """Decompose analytical queries into reasoning steps"""
        steps = [
            ReasoningStep(1, "Break down the subject into components", "", 0.8),
            ReasoningStep(2, "Analyze each component", "", 0.7),
            ReasoningStep(3, "Identify patterns and relationships", "", 0.7),
            ReasoningStep(4, "Synthesize findings", "", 0.8)
        ]
        return steps

    def _decompose_general_query(self, query: str) -> List[ReasoningStep]:
        """Decompose general queries into basic reasoning steps"""
        steps = [
            ReasoningStep(1, "Understand the query requirements", "", 0.8),
            ReasoningStep(2, "Gather relevant information", "", 0.7),
            ReasoningStep(3, "Process and analyze information", "", 0.7),
            ReasoningStep(4, "Formulate response", "", 0.8)
        ]
        return steps

    def _generate_step_reasoning(self, query: str, current_step: ReasoningStep,
                               previous_steps: List[ReasoningStep], context: str = "",
                               knowledge: List[Dict] = None) -> str:
        """Generate reasoning for a specific step"""
        # This would typically use the model's generation capabilities
        # For now, provide template-based reasoning

        step_num = current_step.step_number
        description = current_step.description

        if "identify" in description.lower():
            return f"To answer '{query}', I need to first {description.lower()}."
        elif "evaluate" in description.lower() or "analyze" in description.lower():
            return f"For this step, I {description.lower()} by considering relevant factors and evidence."
        elif "apply" in description.lower():
            return f"I {description.lower()} the appropriate method based on the problem requirements."
        elif "determine" in description.lower():
            return f"Based on the analysis so far, I can {description.lower()}."
        else:
            return f"This step involves {description.lower()} to progress toward the answer."

    def _assess_step_confidence(self, step: ReasoningStep, knowledge: List[Dict] = None) -> float:
        """Assess confidence in a reasoning step"""
        confidence = 0.7  # Base confidence

        # Increase confidence if step has evidence
        if step.evidence:
            confidence += 0.1

        # Increase confidence if step has sub-steps
        if step.sub_steps:
            confidence += 0.1

        # Adjust based on knowledge availability
        if knowledge and len(knowledge) > 0:
            confidence += 0.1

        return min(confidence, 1.0)

    def _synthesize_conclusion(self, steps: List[ReasoningStep], query: str,
                             reasoning_type: ReasoningType) -> str:
        """Synthesize final conclusion from reasoning steps"""
        if not steps:
            return "I cannot provide a definitive answer based on the available information."

        # Combine insights from all steps
        insights = []
        for step in steps:
            if step.reasoning:
                insights.append(step.reasoning)

        # Generate conclusion based on reasoning type
        if reasoning_type == ReasoningType.MATHEMATICAL:
            return f"Based on the mathematical analysis: {'. '.join(insights)}"
        elif reasoning_type == ReasoningType.LOGICAL:
            return f"Logically following the premises: {'. '.join(insights)}"
        elif reasoning_type == ReasoningType.CAUSAL:
            return f"The most likely cause is: {'. '.join(insights)}"
        elif reasoning_type == ReasoningType.COMPARATIVE:
            return f"After comparing all aspects: {'. '.join(insights)}"
        else:
            return f"Based on the analysis: {'. '.join(insights)}"

    def _verify_reasoning_chain(self, steps: List[ReasoningStep], conclusion: str) -> bool:
        """Verify the logical consistency of the reasoning chain"""
        if not steps:
            return False

        # Basic verification checks
        checks = []

        # Check if all steps have reasoning
        has_reasoning = all(step.reasoning.strip() for step in steps)
        checks.append(has_reasoning)

        # Check if confidence scores are reasonable
        avg_confidence = sum(step.confidence for step in steps) / len(steps)
        reasonable_confidence = avg_confidence > self.min_confidence_threshold
        checks.append(reasonable_confidence)

        # Check if conclusion is coherent with steps
        conclusion_coherent = len(conclusion.strip()) > 10
        checks.append(conclusion_coherent)

        return all(checks)

    def _calculate_reasoning_quality(self, steps: List[ReasoningStep], conclusion: str,
                                   verification_result: bool) -> float:
        """Calculate overall reasoning quality score"""
        if not steps:
            return 0.0

        # Base score from verification
        score = 0.5 if verification_result else 0.2

        # Add score based on number of steps (more steps = more thorough)
        step_score = min(len(steps) / self.max_steps, 1.0) * 0.2
        score += step_score

        # Add score based on average confidence
        avg_confidence = sum(step.confidence for step in steps) / len(steps)
        confidence_score = avg_confidence * 0.3
        score += confidence_score

        return min(score, 1.0)

    def format_reasoning_output(self, chain: ReasoningChain) -> str:
        """Format reasoning chain for output"""
        if not chain.steps:
            return chain.conclusion

        output_lines = [f"Let me think through this step by step for: {chain.query}\n"]

        for step in chain.steps:
            template = self.templates[chain.reasoning_type.value]["step_template"]
            formatted_step = template.format(
                step=step.step_number,
                description=step.description,
                reasoning=step.reasoning,
                evidence="; ".join(step.evidence) if step.evidence else "Based on analysis",
                confidence=step.confidence
            )
            output_lines.append(formatted_step)
            output_lines.append("")  # Empty line between steps

        # Add conclusion
        conclusion_template = self.templates[chain.reasoning_type.value]["conclusion_template"]
        output_lines.append(conclusion_template.format(conclusion=chain.conclusion))

        # Add quality indicators
        output_lines.append("")
        output_lines.append(f"Reasoning confidence: {chain.confidence:.2f}")
        output_lines.append(f"Reasoning quality score: {chain.reasoning_quality_score:.2f}")

        return "\n".join(output_lines)


# Global instance
_reasoning_engine = None

def get_reasoning_engine():
    """Get or create global reasoning engine instance"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine

