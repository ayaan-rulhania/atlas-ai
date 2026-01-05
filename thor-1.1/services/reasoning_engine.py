"""
Comprehensive Chain-of-Thought Reasoning Engine for Thor 1.1
Extensive implementation with multi-topic support, knowledge synthesis,
advanced reasoning capabilities, and extensive utility functions.

Features:
- Multiple reasoning types (11 types)
- Domain classification
- Entity extraction
- Evidence collection and scoring
- Advanced confidence calibration
- Step dependency resolution
- Alternative reasoning paths
- Query expansion
- Performance metrics
- Multiple output formats (text, JSON, Markdown, HTML)
- Caching support
- Batch processing
- Comprehensive validation
"""
import re
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime


class ReasoningType(Enum):
    LOGICAL = "logical"
    MATHEMATICAL = "mathematical"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    ANALYTICAL = "analytical"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    INDUCTIVE = "inductive"
    DEDUCTIVE = "deductive"
    ABDUCTIVE = "abductive"
    GENERAL = "general"


class Domain(Enum):
    SCIENCE = "science"
    ECONOMICS = "economics"
    TECHNOLOGY = "technology"
    ENVIRONMENT = "environment"
    POLITICS = "politics"
    HEALTH = "health"
    EDUCATION = "education"
    HISTORY = "history"
    PHILOSOPHY = "philosophy"
    GENERAL = "general"


class RelationshipType(Enum):
    CAUSAL = "causal"
    HIERARCHICAL = "hierarchical"
    ASSOCIATIVE = "associative"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning chain"""
    step_number: int
    description: str
    reasoning: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    sub_steps: List['ReasoningStep'] = field(default_factory=list)
    dependencies: List[int] = field(default_factory=list)
    knowledge_used: List[Dict] = field(default_factory=list)
    execution_time: Optional[float] = None
    quality_score: float = 0.0


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
    topics_involved: List[str] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)
    domains: List[Domain] = field(default_factory=list)
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryAnalysis:
    """Comprehensive query analysis"""
    original_query: str
    intent: str
    complexity: float
    reasoning_type: ReasoningType
    domains: List[Domain]
    topics: List[str]
    requires_multi_topic: bool
    entities: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    complexity_level: int = 1


@dataclass
class Relationship:
    """Represents a relationship between topics"""
    topic1: str
    topic2: str
    rel_type: RelationshipType
    strength: float
    confidence: float
    evidence: str = ""


class ReasoningEngine:
    """
    Comprehensive Chain-of-Thought reasoning engine for complex problem solving.
    Supports multiple reasoning types, domain classification, evidence collection,
    and advanced reasoning strategies.
    """

    def __init__(self):
        self.max_steps = 10
        self.min_confidence_threshold = 0.6
        self.templates = self._load_reasoning_templates()
        self.cache = {}  # Simple in-memory cache
        self.stats = {
            'total_queries': 0,
            'total_steps': 0,
            'avg_confidence': 0.0,
            'avg_quality': 0.0,
        }
        
        # Domain keywords for classification
        self.domain_keywords = {
            Domain.SCIENCE: ['science', 'physics', 'chemistry', 'biology', 'research', 
                            'experiment', 'theory', 'hypothesis', 'discovery', 'scientific'],
            Domain.ECONOMICS: ['economics', 'economic', 'economy', 'market', 'trade',
                              'finance', 'financial', 'policy', 'inflation', 'gdp', 'recession'],
            Domain.TECHNOLOGY: ['technology', 'tech', 'computer', 'software', 'hardware',
                              'digital', 'internet', 'network', 'system', 'platform', 'application'],
            Domain.ENVIRONMENT: ['climate', 'environment', 'environmental', 'pollution',
                               'carbon', 'emission', 'green', 'sustainable', 'renewable', 'ecosystem'],
            Domain.POLITICS: ['politics', 'political', 'government', 'policy', 'law',
                             'legislation', 'democracy', 'election', 'vote', 'senate', 'congress'],
            Domain.HEALTH: ['health', 'medical', 'medicine', 'disease', 'treatment',
                          'patient', 'doctor', 'hospital', 'symptom', 'diagnosis', 'therapy'],
            Domain.EDUCATION: ['education', 'learning', 'teaching', 'school', 'university',
                             'student', 'teacher', 'curriculum', 'academic', 'study'],
            Domain.HISTORY: ['history', 'historical', 'war', 'battle', 'empire', 'ancient',
                           'medieval', 'revolution', 'civilization', 'culture'],
            Domain.PHILOSOPHY: ['philosophy', 'philosophical', 'ethics', 'moral', 'existence',
                               'reality', 'consciousness', 'truth', 'meaning', 'wisdom'],
        }
        
        # Stop words for topic extraction
        self.stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'who', 'what', 'where', 'when', 'why', 'how', 'which', 'whose',
            'and', 'or', 'but', 'if', 'then', 'else', 'for', 'with', 'from',
            'to', 'of', 'in', 'on', 'at', 'by', 'about', 'into', 'through',
            'tell', 'me', 'explain', 'about'
        }

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
            },
            ReasoningType.TEMPORAL.value: {
                "step_template": "Step {step}: Temporal analysis - {description}\nTimeline: {reasoning}\nSequence: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Temporal conclusion: {conclusion}",
                "indicators": ["before", "after", "during", "when", "then", "subsequently", "previously"]
            },
            ReasoningType.SPATIAL.value: {
                "step_template": "Step {step}: Spatial analysis - {description}\nLocation: {reasoning}\nSpatial relationships: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Spatial conclusion: {conclusion}",
                "indicators": ["where", "location", "place", "position", "spatial", "geographic"]
            },
            ReasoningType.INDUCTIVE.value: {
                "step_template": "Step {step}: Inductive reasoning - {description}\nObservation: {reasoning}\nPattern: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Inductive conclusion: {conclusion}",
                "indicators": ["pattern", "trend", "generalize", "observe", "example"]
            },
            ReasoningType.DEDUCTIVE.value: {
                "step_template": "Step {step}: Deductive reasoning - {description}\nPremise: {reasoning}\nInference: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Deductive conclusion: {conclusion}",
                "indicators": ["if", "then", "must", "necessarily", "therefore", "follows"]
            },
            ReasoningType.ABDUCTIVE.value: {
                "step_template": "Step {step}: Abductive reasoning - {description}\nObservation: {reasoning}\nExplanation: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Best explanation: {conclusion}",
                "indicators": ["explain", "hypothesis", "best", "likely", "probably"]
            },
            ReasoningType.GENERAL.value: {
                "step_template": "Step {step}: {description}\nReasoning: {reasoning}\nEvidence: {evidence}\nConfidence: {confidence:.2f}",
                "conclusion_template": "Conclusion: {conclusion}",
                "indicators": []
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

        # Check for temporal reasoning
        if any(word in query_lower for word in ["before", "after", "during", "when", "then", "subsequently", "previously"]):
            return ReasoningType.TEMPORAL

        # Check for spatial reasoning
        if any(word in query_lower for word in ["where", "location", "place", "position", "spatial", "geographic"]):
            return ReasoningType.SPATIAL

        # Check for inductive reasoning
        if any(word in query_lower for word in ["pattern", "trend", "generalize", "observe", "example", "usually"]):
            return ReasoningType.INDUCTIVE

        # Check for deductive reasoning
        if any(word in query_lower for word in ["must", "necessarily", "follows", "if all", "then all"]):
            return ReasoningType.DEDUCTIVE

        # Check for abductive reasoning
        if any(word in query_lower for word in ["explain", "hypothesis", "best explanation", "probably", "likely cause"]):
            return ReasoningType.ABDUCTIVE

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

    def generate_reasoning_chain(
        self, 
        query: str, 
        context: str = "", 
        knowledge: List[Dict] = None,
        multi_topic_knowledge: Optional[Dict[str, List[Dict]]] = None,
        use_iterative_retrieval: bool = False
    ) -> ReasoningChain:
        """
        Generate a complete reasoning chain for the query

        Args:
            query: The user's query
            context: Conversation context
            knowledge: Relevant knowledge from brain (legacy parameter)
            multi_topic_knowledge: Dictionary mapping topic -> knowledge items
            use_iterative_retrieval: Whether to retrieve knowledge iteratively per step

        Returns:
            ReasoningChain with steps and conclusion
        """
        reasoning_type = self.detect_reasoning_type(query)

        # Create initial reasoning steps
        steps = self._decompose_query_into_steps(query, reasoning_type, context, knowledge)

        # Accumulate knowledge across steps for iterative reasoning
        accumulated_knowledge = {}
        previous_step_contexts = []

        # Generate step-by-step reasoning with iterative knowledge retrieval
        for i, step in enumerate(steps):
            if step.reasoning == "":  # Only fill in empty reasoning
                # Get knowledge for this step (iterative if enabled)
                step_knowledge = self._get_step_knowledge(
                    step,
                    query,
                    multi_topic_knowledge,
                    accumulated_knowledge,
                    previous_step_contexts,
                    use_iterative_retrieval
                )
                
                # Generate reasoning using step-specific knowledge
                step.reasoning = self._generate_step_reasoning(
                    query, 
                    step, 
                    steps[:i], 
                    context, 
                    step_knowledge,
                    previous_step_contexts
                )
                step.confidence = self._assess_step_confidence(step, step_knowledge)
                
                # Accumulate knowledge and context for next steps
                if step_knowledge:
                    accumulated_knowledge.update(step_knowledge)
                    previous_step_contexts.append(step.reasoning)

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
        """Decompose causal queries into reasoning steps with multi-topic support"""
        # Enhanced causal decomposition for multi-topic problems
        query_lower = query.lower()
        
        # Detect if this is a multi-topic causal query
        # Look for patterns like "how does X affect Y" or "why does X cause Y"
        multi_topic_patterns = [
            r'how does (.+?) affect (.+)',
            r'how do (.+?) affect (.+)',
            r'why does (.+?) cause (.+)',
            r'what causes (.+?) to (.+)',
            r'how does (.+?) impact (.+)',
            r'how does (.+?) influence (.+)'
        ]
        
        is_multi_topic = False
        for pattern in multi_topic_patterns:
            if re.search(pattern, query_lower):
                is_multi_topic = True
                break
        
        if is_multi_topic:
            # Multi-topic causal chain steps
            steps = [
                ReasoningStep(1, "Identify the initial cause or factor", "", 0.7),
                ReasoningStep(2, "Identify the affected domain or outcome", "", 0.7),
                ReasoningStep(3, "Retrieve knowledge about the causal mechanism", "", 0.8),
                ReasoningStep(4, "Evaluate the causal relationship between domains", "", 0.7),
                ReasoningStep(5, "Assess evidence and strength of causal link", "", 0.8),
                ReasoningStep(6, "Determine the complete causal chain", "", 0.7)
            ]
        else:
            # Single-topic causal steps
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

    def _generate_step_reasoning(
        self, 
        query: str, 
        current_step: ReasoningStep,
        previous_steps: List[ReasoningStep], 
        context: str = "",
        knowledge: List[Dict] = None,
        previous_step_contexts: List[str] = None
    ) -> str:
        """Generate reasoning for a specific step with multi-topic knowledge support"""
        step_num = current_step.step_number
        description = current_step.description
        
        # Build context from previous steps
        previous_context = ""
        if previous_step_contexts:
            previous_context = " ".join(previous_step_contexts[-2:])  # Last 2 steps
        
        # Use knowledge to enhance reasoning
        knowledge_context = ""
        if knowledge:
            # Extract key information from knowledge items
            key_facts = []
            for item in knowledge[:3]:  # Use top 3 knowledge items
                content = item.get('content', '')
                if content:
                    # Extract first sentence or first 100 chars
                    first_sentence = content.split('.')[0]
                    if len(first_sentence) > 100:
                        first_sentence = content[:100] + "..."
                    key_facts.append(first_sentence)
            if key_facts:
                knowledge_context = " ".join(key_facts)

        # Generate reasoning with context
        if "identify" in description.lower():
            base_reasoning = f"To answer '{query}', I need to first {description.lower()}."
            if knowledge_context:
                base_reasoning += f" Based on available knowledge: {knowledge_context[:200]}"
            if previous_context:
                base_reasoning += f" Building on previous analysis: {previous_context[:150]}"
            return base_reasoning
        elif "evaluate" in description.lower() or "analyze" in description.lower():
            base_reasoning = f"For this step, I {description.lower()} by considering relevant factors and evidence."
            if knowledge_context:
                base_reasoning += f" Relevant information: {knowledge_context[:200]}"
            if previous_context:
                base_reasoning += f" Previous findings: {previous_context[:150]}"
            return base_reasoning
        elif "apply" in description.lower():
            base_reasoning = f"I {description.lower()} the appropriate method based on the problem requirements."
            if knowledge_context:
                base_reasoning += f" Using knowledge: {knowledge_context[:200]}"
            return base_reasoning
        elif "determine" in description.lower():
            base_reasoning = f"Based on the analysis so far, I can {description.lower()}."
            if previous_context:
                base_reasoning += f" From previous steps: {previous_context[:150]}"
            if knowledge_context:
                base_reasoning += f" With supporting knowledge: {knowledge_context[:200]}"
            return base_reasoning
        else:
            base_reasoning = f"This step involves {description.lower()} to progress toward the answer."
            if knowledge_context:
                base_reasoning += f" Knowledge available: {knowledge_context[:200]}"
            return base_reasoning
    
    def _get_step_knowledge(
        self,
        step: ReasoningStep,
        query: str,
        multi_topic_knowledge: Optional[Dict[str, List[Dict]]],
        accumulated_knowledge: Dict[str, List[Dict]],
        previous_step_contexts: List[str],
        use_iterative_retrieval: bool
    ) -> Optional[Dict[str, List[Dict]]]:
        """
        Get knowledge relevant to a specific reasoning step.
        
        Returns:
            Dictionary mapping topic -> knowledge items, or None if not using multi-topic
        """
        if not use_iterative_retrieval:
            # Use provided multi_topic_knowledge if available
            return multi_topic_knowledge
        
        # Iterative retrieval: get knowledge for this specific step
        try:
            from .multi_topic_retriever import get_multi_topic_retriever
            from .knowledge_synthesizer import get_knowledge_synthesizer
            
            retriever = get_multi_topic_retriever()
            synthesizer = get_knowledge_synthesizer()
            
            # Create step-specific query
            step_query = f"{query} {step.description}"
            
            # Retrieve knowledge for this step
            step_knowledge_data = retriever.get_enhanced_multi_topic_knowledge(
                step_query,
                max_topics=3,
                max_knowledge_per_topic=3
            )
            
            # Merge with accumulated knowledge
            step_knowledge = step_knowledge_data.get('knowledge_by_topic', {})
            merged_knowledge = {**accumulated_knowledge, **step_knowledge}
            
            return merged_knowledge if merged_knowledge else None
            
        except ImportError:
            # Fallback to provided knowledge
            return multi_topic_knowledge

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
        
        # Add topics and domains if available
        if chain.topics_involved:
            output_lines.append(f"Topics involved: {', '.join(chain.topics_involved)}")
        if chain.domains:
            domain_names = [d.value for d in chain.domains]
            output_lines.append(f"Domains: {', '.join(domain_names)}")

        return "\n".join(output_lines)

    # ========================================================================
    # Utility Functions
    # ========================================================================

    def _normalize_confidence(self, score: float) -> float:
        """Normalize confidence score to [0.0, 1.0]"""
        return max(0.0, min(1.0, score))

    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple Jaccard similarity between two strings"""
        words1 = set(w.lower() for w in s1.split() if len(w) > 2)
        words2 = set(w.lower() for w in s2.split() if len(w) > 2)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def _extract_meaningful_words(self, text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful words from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) >= min_length and w not in self.stop_words]

    def _count_word_occurrences(self, text: str, word: str) -> int:
        """Count occurrences of a word in text"""
        return len(re.findall(r'\b' + re.escape(word.lower()) + r'\b', text.lower()))

    # ========================================================================
    # Domain Classification
    # ========================================================================

    def classify_domain(self, text: str) -> Domain:
        """Classify text into a domain"""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                domain_scores[domain] = matches / len(keywords)
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return Domain.GENERAL

    def classify_multiple_domains(self, text: str, top_n: int = 3) -> List[Tuple[Domain, float]]:
        """Classify text into multiple domains with scores"""
        text_lower = text.lower()
        domain_scores = []
        
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                score = matches / len(keywords)
                domain_scores.append((domain, score))
        
        domain_scores.sort(key=lambda x: x[1], reverse=True)
        return domain_scores[:top_n]

    # ========================================================================
    # Query Analysis
    # ========================================================================

    def analyze_query_comprehensive(self, query: str) -> QueryAnalysis:
        """Comprehensive query analysis"""
        query_lower = query.lower()
        word_count = len(query.split())
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Calculate complexity
        complexity = self._calculate_complexity(query, word_count)
        
        # Detect reasoning type
        reasoning_type = self.detect_reasoning_type(query)
        
        # Classify domains
        domains = [d for d, _ in self.classify_multiple_domains(query)]
        
        # Extract topics
        topics = self._extract_topics_from_query(query)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(query)
        
        # Check if multi-topic
        requires_multi_topic = (
            len(topics) >= 2 or
            'affect' in query_lower or
            'impact' in query_lower or
            'influence' in query_lower or
            'relationship between' in query_lower or
            'connection between' in query_lower
        )
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(query, complexity, word_count)
        
        return QueryAnalysis(
            original_query=query,
            intent=intent,
            complexity=complexity,
            reasoning_type=reasoning_type,
            domains=domains,
            topics=topics,
            requires_multi_topic=requires_multi_topic,
            entities=entities,
            key_phrases=key_phrases,
            complexity_level=complexity_level
        )

    def _detect_intent(self, query_lower: str) -> str:
        """Detect query intent"""
        if 'what is' in query_lower or 'what are' in query_lower:
            return 'definition'
        elif 'how' in query_lower:
            return 'how_to'
        elif 'why' in query_lower:
            return 'causal_explanation'
        elif 'compare' in query_lower or 'versus' in query_lower:
            return 'comparison'
        elif 'explain' in query_lower:
            return 'explanation'
        elif 'who' in query_lower:
            return 'biographical'
        elif 'when' in query_lower:
            return 'temporal'
        elif 'where' in query_lower:
            return 'spatial'
        else:
            return 'general'

    def _calculate_complexity(self, query: str, word_count: int) -> float:
        """Calculate query complexity score"""
        base = 0.3
        word_factor = min(word_count / 20.0, 0.4)
        question_factor = 0.2 if '?' in query else 0.0
        conjunction_factor = (
            0.1 if ('and' in query.lower() or 'between' in query.lower()) else 0.0
        )
        
        return self._normalize_confidence(base + word_factor + question_factor + conjunction_factor)

    def _determine_complexity_level(self, query: str, complexity: float, word_count: int) -> int:
        """Determine complexity level (1-5)"""
        base_level = 1
        if complexity > 0.8:
            base_level = 3
        elif complexity > 0.6:
            base_level = 2
        
        if word_count > 20:
            base_level += 1
        if '?' in query and query.count('?') > 1:
            base_level += 1
        
        return min(base_level, 5)

    def _extract_topics_from_query(self, query: str) -> List[str]:
        """Extract topics from query"""
        words = self._extract_meaningful_words(query, min_length=4)
        return words[:5]  # Top 5 topics

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query"""
        # Simple entity extraction - look for capitalized words/phrases
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        return entities[:10]

    def _extract_key_phrases(self, query: str) -> List[str]:
        """Extract key phrases from query"""
        query_lower = query.lower()
        phrases = []
        
        patterns = [
            r'how does (.+?)',
            r'how do (.+?)',
            r'why does (.+?)',
            r'what causes (.+?)',
            r'what is (.+?)',
            r'compare (.+?)',
            r'difference between (.+?)',
            r'relationship between (.+?)',
            r'effect of (.+?)',
            r'impact of (.+?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query_lower)
            phrases.extend(matches)
        
        return phrases[:5]

    # ========================================================================
    # Evidence Collection
    # ========================================================================

    def collect_evidence(self, knowledge_items: List[Dict], query: str) -> List[str]:
        """Collect evidence from knowledge items"""
        query_lower = query.lower()
        query_words = set(self._extract_meaningful_words(query_lower, 3))
        evidence = []
        
        for item in knowledge_items:
            content = item.get('content', '').lower()
            title = item.get('title', '').lower()
            
            # Extract sentences that contain query words
            sentences = re.split(r'[.!?]+', content)
            
            for sentence in sentences:
                sentence_words = set(self._extract_meaningful_words(sentence, 3))
                overlap = len(query_words.intersection(sentence_words))
                
                if overlap >= 2 and len(sentence.strip()) > 20:
                    evidence.append(sentence.strip())
        
        # Remove duplicates and limit
        seen = set()
        unique_evidence = []
        for e in evidence:
            if e not in seen:
                seen.add(e)
                unique_evidence.append(e)
                if len(unique_evidence) >= 10:
                    break
        
        return unique_evidence

    def score_evidence_relevance(self, evidence: str, query: str) -> float:
        """Score evidence relevance to query"""
        return self._calculate_string_similarity(evidence, query)

    def rank_evidence_by_relevance(self, evidence_list: List[str], query: str) -> List[Tuple[str, float]]:
        """Rank evidence by relevance to query"""
        scored = [(e, self.score_evidence_relevance(e, query)) for e in evidence_list]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ========================================================================
    # Advanced Confidence Calibration
    # ========================================================================

    def calibrate_confidence(
        self,
        base_confidence: float,
        evidence_count: int,
        knowledge_count: int,
        verification_passed: bool
    ) -> float:
        """Calibrate confidence scores based on evidence"""
        evidence_bonus = min(evidence_count * 0.05, 0.2)
        knowledge_bonus = 0.15 if knowledge_count >= 3 else (0.1 if knowledge_count >= 1 else 0.0)
        verification_bonus = 0.1 if verification_passed else 0.0
        
        return self._normalize_confidence(
            base_confidence + evidence_bonus + knowledge_bonus + verification_bonus
        )

    def adjust_confidence_by_dependencies(
        self,
        step: ReasoningStep,
        dependency_steps: List[ReasoningStep]
    ) -> float:
        """Adjust confidence based on step dependencies"""
        base_confidence = step.confidence
        
        if not dependency_steps:
            return base_confidence
        
        dependency_confidence = sum(s.confidence for s in dependency_steps) / len(dependency_steps)
        dependency_penalty = 0.1 if dependency_confidence < 0.6 else 0.0
        
        return self._normalize_confidence(base_confidence * dependency_confidence - dependency_penalty)

    # ========================================================================
    # Step Dependency Resolution
    # ========================================================================

    def resolve_dependencies(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """Resolve and validate step dependencies"""
        step_map = {step.step_number: step for step in steps}
        
        def verify_dependencies(step: ReasoningStep) -> bool:
            return all(
                dep_num in step_map and step_map[dep_num].step_number < step.step_number
                for dep_num in step.dependencies
            )
        
        return [step for step in steps if verify_dependencies(step)]

    def topological_sort_steps(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """Topologically sort steps by dependencies"""
        step_map = {step.step_number: step for step in steps}
        visited = set()
        result = []
        
        def visit(step_num: int):
            if step_num in visited:
                return
            visited.add(step_num)
            
            if step_num in step_map:
                step = step_map[step_num]
                for dep_num in step.dependencies:
                    visit(dep_num)
                result.append(step)
        
        for step in steps:
            visit(step.step_number)
        
        return result

    # ========================================================================
    # Query Expansion
    # ========================================================================

    def expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expansions = [query]
        query_lower = query.lower()
        
        synonyms = {
            'affect': ['impact', 'influence', 'change'],
            'cause': ['lead to', 'result in', 'bring about'],
            'compare': ['contrast', 'examine differences', 'evaluate'],
            'analyze': ['examine', 'study', 'investigate'],
            'explain': ['describe', 'clarify', 'elucidate'],
        }
        
        for word, syns in synonyms.items():
            if word in query_lower:
                for syn in syns:
                    expanded = query_lower.replace(word, syn)
                    if expanded not in expansions:
                        expansions.append(expanded)
        
        return expansions

    def generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations"""
        variations = [query]
        
        if '?' not in query:
            variations.append(query + '?')
        
        query_lower = query.lower()
        if 'what is' not in query_lower:
            variations.append(f"What is {query}?")
        
        if 'how' not in query_lower:
            variations.append(f"How does {query} work?")
        
        return variations

    # ========================================================================
    # Knowledge Filtering and Ranking
    # ========================================================================

    def filter_knowledge_by_relevance(
        self,
        knowledge_items: List[Dict],
        query: str,
        min_relevance: float = 0.3
    ) -> List[Dict]:
        """Filter knowledge items by relevance to query"""
        query_words = set(self._extract_meaningful_words(query.lower(), 3))
        
        def calculate_relevance(item: Dict) -> float:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            
            title_score = 0.3 if any(w in title for w in query_words) else 0.0
            
            content_words = set(self._extract_meaningful_words(content, 3))
            overlap = len(query_words.intersection(content_words))
            content_score = (overlap / len(query_words) * 0.5) if query_words else 0.0
            
            confidence_factor = item.get('confidence', 0.5) * 0.2
            
            return self._normalize_confidence(title_score + content_score + confidence_factor)
        
        scored_items = [(item, calculate_relevance(item)) for item in knowledge_items]
        filtered = [(item, score) for item, score in scored_items if score >= min_relevance]
        filtered.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, _ in filtered]

    def rank_knowledge_by_quality(self, knowledge_items: List[Dict]) -> List[Dict]:
        """Rank knowledge items by quality"""
        def calculate_quality_score(item: Dict) -> float:
            content = item.get('content', '')
            length = len(content)
            
            length_score = 0.3 if 100 <= length <= 1000 else (0.2 if length > 100 else 0.1)
            confidence_score = item.get('confidence', 0.5) * 0.4
            
            source = item.get('source', '')
            source_score = 0.2 if source == 'wikipedia' else (0.15 if source == 'structured' else 0.1)
            
            return self._normalize_confidence(length_score + confidence_score + source_score)
        
        scored_items = [(item, calculate_quality_score(item)) for item in knowledge_items]
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, _ in scored_items]

    # ========================================================================
    # Advanced Reasoning Strategies
    # ========================================================================

    def generate_alternative_paths(
        self,
        query: str,
        main_chain: ReasoningChain
    ) -> List[ReasoningChain]:
        """Generate alternative reasoning paths"""
        alternative_types = {
            ReasoningType.CAUSAL: [ReasoningType.ANALYTICAL, ReasoningType.COMPARATIVE],
            ReasoningType.COMPARATIVE: [ReasoningType.ANALYTICAL, ReasoningType.CAUSAL],
            ReasoningType.ANALYTICAL: [ReasoningType.CAUSAL, ReasoningType.COMPARATIVE],
        }
        
        alt_types = alternative_types.get(main_chain.reasoning_type, 
                                         [ReasoningType.CAUSAL, ReasoningType.ANALYTICAL])
        
        alternative_chains = []
        for alt_type in alt_types:
            try:
                alt_steps = self._decompose_query_into_steps(query, alt_type, "", None)
                
                # Process steps
                for i, step in enumerate(alt_steps):
                    if step.reasoning == "":
                        step.reasoning = self._generate_step_reasoning(
                            query, step, alt_steps[:i], "", None
                        )
                        step.confidence = self._assess_step_confidence(step, None)
                
                conclusion = self._synthesize_conclusion(alt_steps, query, alt_type)
                avg_confidence = sum(s.confidence for s in alt_steps) / len(alt_steps) if alt_steps else 0.5
                
                alt_chain = ReasoningChain(
                    query=query,
                    reasoning_type=alt_type,
                    steps=alt_steps,
                    conclusion=conclusion,
                    confidence=avg_confidence,
                    verification_result=self._verify_reasoning_chain(alt_steps, conclusion),
                    reasoning_quality_score=self._calculate_reasoning_quality(alt_steps, conclusion, True),
                    topics_involved=main_chain.topics_involved,
                    relationships=[]
                )
                
                alternative_chains.append(alt_chain)
            except Exception:
                continue
        
        return alternative_chains

    def merge_reasoning_chains(self, chains: List[ReasoningChain]) -> Optional[ReasoningChain]:
        """Merge multiple reasoning chains"""
        if not chains:
            return None
        
        first_chain = chains[0]
        
        # Combine all steps
        all_steps = []
        for chain in chains:
            all_steps.extend(chain.steps)
        
        # Remove duplicate steps
        seen_descriptions = set()
        unique_steps = []
        for step in all_steps:
            if step.description not in seen_descriptions:
                seen_descriptions.add(step.description)
                unique_steps.append(step)
        
        # Renumber steps
        for i, step in enumerate(unique_steps, 1):
            step.step_number = i
        
        # Combine conclusions
        combined_conclusion = " ".join(c.conclusion for c in chains)
        
        # Calculate average metrics
        avg_confidence = sum(c.confidence for c in chains) / len(chains)
        avg_quality = sum(c.reasoning_quality_score for c in chains) / len(chains)
        
        # Combine topics
        all_topics = []
        for chain in chains:
            all_topics.extend(chain.topics_involved)
        unique_topics = list(dict.fromkeys(all_topics))  # Preserve order, remove duplicates
        
        # Combine relationships
        all_relationships = []
        for chain in chains:
            all_relationships.extend(chain.relationships)
        
        return ReasoningChain(
            query=first_chain.query,
            reasoning_type=first_chain.reasoning_type,
            steps=unique_steps,
            conclusion=combined_conclusion,
            confidence=avg_confidence,
            verification_result=all(c.verification_result for c in chains),
            reasoning_quality_score=avg_quality,
            topics_involved=unique_topics,
            relationships=all_relationships
        )

    # ========================================================================
    # Advanced Formatting
    # ========================================================================

    def format_reasoning_json(self, chain: ReasoningChain) -> str:
        """Format reasoning chain as JSON"""
        def step_to_dict(step: ReasoningStep) -> Dict:
            return {
                'step_number': step.step_number,
                'description': step.description,
                'reasoning': step.reasoning,
                'confidence': step.confidence,
                'evidence': step.evidence,
                'dependencies': step.dependencies
            }
        
        data = {
            'query': chain.query,
            'reasoning_type': chain.reasoning_type.value,
            'steps': [step_to_dict(s) for s in chain.steps],
            'conclusion': chain.conclusion,
            'confidence': chain.confidence,
            'verification_result': chain.verification_result,
            'quality_score': chain.reasoning_quality_score,
            'topics_involved': chain.topics_involved,
            'domains': [d.value for d in chain.domains] if chain.domains else []
        }
        
        return json.dumps(data, indent=2)

    def format_reasoning_markdown(self, chain: ReasoningChain) -> str:
        """Format reasoning chain as Markdown"""
        lines = [
            f"# Reasoning Analysis\n",
            f"**Query:** {chain.query}\n",
            f"**Reasoning Type:** {chain.reasoning_type.value}\n",
            "\n## Reasoning Steps\n"
        ]
        
        for step in chain.steps:
            evidence_str = f"\n*Evidence: {', '.join(step.evidence)}*" if step.evidence else ""
            lines.append(
                f"### Step {step.step_number}: {step.description}\n\n"
                f"{step.reasoning}\n\n"
                f"*Confidence: {step.confidence:.2f}*{evidence_str}\n"
            )
        
        lines.extend([
            "\n## Conclusion\n",
            f"{chain.conclusion}\n",
            "\n## Metrics\n",
            f"- **Confidence:** {chain.confidence:.2f}\n",
            f"- **Quality Score:** {chain.reasoning_quality_score:.2f}\n",
            f"- **Verification:** {'✓ Passed' if chain.verification_result else '✗ Failed'}\n"
        ])
        
        if chain.topics_involved:
            lines.append(f"- **Topics:** {', '.join(chain.topics_involved)}\n")
        
        return "\n".join(lines)

    def format_reasoning_html(self, chain: ReasoningChain) -> str:
        """Format reasoning chain as HTML"""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head><title>Reasoning Analysis</title></head>",
            "<body>",
            f"<h1>Reasoning Analysis</h1>",
            f"<p><strong>Query:</strong> {chain.query}</p>",
            f"<p><strong>Reasoning Type:</strong> {chain.reasoning_type.value}</p>",
            "<h2>Reasoning Steps</h2>"
        ]
        
        for step in chain.steps:
            html.append(
                f"<div class='step'>"
                f"<h3>Step {step.step_number}: {step.description}</h3>"
                f"<p>{step.reasoning}</p>"
                f"<p><em>Confidence: {step.confidence:.2f}</em></p>"
                f"</div>"
            )
        
        html.extend([
            "<h2>Conclusion</h2>",
            f"<p>{chain.conclusion}</p>",
            "<h2>Metrics</h2>",
            f"<ul>",
            f"<li>Confidence: {chain.confidence:.2f}</li>",
            f"<li>Quality Score: {chain.reasoning_quality_score:.2f}</li>",
            f"<li>Verification: {'Passed' if chain.verification_result else 'Failed'}</li>",
            f"</ul>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html)

    # ========================================================================
    # Caching Support
    # ========================================================================

    def _hash_query(self, query: str) -> str:
        """Hash query for caching"""
        return hashlib.md5(query.encode()).hexdigest()

    def check_cache(self, query: str) -> Optional[ReasoningChain]:
        """Check cache for existing reasoning"""
        query_hash = self._hash_query(query)
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            # Check if cache entry is still valid (1 hour)
            if time.time() - entry.get('timestamp', 0) < 3600:
                return entry.get('chain')
            else:
                del self.cache[query_hash]
        return None

    def store_in_cache(self, query: str, chain: ReasoningChain) -> None:
        """Store reasoning in cache"""
        query_hash = self._hash_query(query)
        self.cache[query_hash] = {
            'query': query,
            'chain': chain,
            'timestamp': time.time()
        }

    def clear_cache(self) -> None:
        """Clear the cache"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'entries': len(self.cache)
        }

    # ========================================================================
    # Batch Processing
    # ========================================================================

    def process_batch_queries(self, queries: List[str]) -> List[ReasoningChain]:
        """Process multiple queries in batch"""
        return [self.generate_reasoning_chain(q) for q in queries]

    def process_batch_with_knowledge(
        self,
        queries: List[str],
        shared_knowledge: List[Dict]
    ) -> List[ReasoningChain]:
        """Process queries with shared knowledge"""
        return [
            self.generate_reasoning_chain(q, knowledge=shared_knowledge)
            for q in queries
        ]

    # ========================================================================
    # Statistics and Metrics
    # ========================================================================

    def calculate_stats(self, chains: List[ReasoningChain]) -> Dict[str, Any]:
        """Calculate statistics from reasoning chains"""
        if not chains:
            return {
                'total_queries': 0,
                'avg_confidence': 0.0,
                'avg_quality_score': 0.0,
                'verification_rate': 0.0,
                'reasoning_type_distribution': {},
                'avg_steps_per_chain': 0.0
            }
        
        total = len(chains)
        confidences = [c.confidence for c in chains]
        quality_scores = [c.reasoning_quality_score for c in chains]
        verified_count = sum(1 for c in chains if c.verification_result)
        step_counts = [len(c.steps) for c in chains]
        
        # Count reasoning types
        type_distribution = defaultdict(int)
        for chain in chains:
            type_distribution[chain.reasoning_type.value] += 1
        
        return {
            'total_queries': total,
            'avg_confidence': sum(confidences) / total,
            'avg_quality_score': sum(quality_scores) / total,
            'verification_rate': verified_count / total,
            'reasoning_type_distribution': dict(type_distribution),
            'avg_steps_per_chain': sum(step_counts) / total
        }

    def update_stats(self, chain: ReasoningChain) -> None:
        """Update internal statistics"""
        self.stats['total_queries'] += 1
        self.stats['total_steps'] += len(chain.steps)
        
        # Update running averages
        n = self.stats['total_queries']
        self.stats['avg_confidence'] = (
            (self.stats['avg_confidence'] * (n - 1) + chain.confidence) / n
        )
        self.stats['avg_quality'] = (
            (self.stats['avg_quality'] * (n - 1) + chain.reasoning_quality_score) / n
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self.stats.copy()

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_step(self, step: ReasoningStep) -> Tuple[bool, List[str]]:
        """Validate a reasoning step"""
        errors = []
        
        if step.step_number <= 0:
            errors.append("Invalid step number")
        
        if not step.description:
            errors.append("Empty step description")
        
        if step.confidence < 0.0 or step.confidence > 1.0:
            errors.append("Confidence out of range")
        
        # Check dependencies
        for dep in step.dependencies:
            if dep >= step.step_number:
                errors.append(f"Invalid dependency: step {step.step_number} depends on step {dep}")
        
        return (len(errors) == 0, errors)

    def validate_reasoning_chain(self, chain: ReasoningChain) -> Tuple[bool, List[str]]:
        """Validate a reasoning chain"""
        errors = []
        
        if not chain.query:
            errors.append("Empty query")
        
        if not chain.steps:
            errors.append("No reasoning steps")
        
        # Validate each step
        for step in chain.steps:
            valid, step_errors = self.validate_step(step)
            if not valid:
                errors.extend(step_errors)
        
        if not chain.conclusion:
            errors.append("Empty conclusion")
        
        if chain.confidence < 0.0 or chain.confidence > 1.0:
            errors.append("Confidence out of range")
        
        # Check step numbering
        step_numbers = [s.step_number for s in chain.steps]
        expected = list(range(1, len(chain.steps) + 1))
        if sorted(step_numbers) != expected:
            errors.append("Step numbers not sequential")
        
        return (len(errors) == 0, errors)

    # ========================================================================
    # Performance Metrics
    # ========================================================================

    def benchmark_reasoning(self, query: str, iterations: int = 10) -> Dict[str, float]:
        """Benchmark reasoning generation"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            _ = self.generate_reasoning_chain(query)
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_time': sum(times)
        }

    # ========================================================================
    # Enhanced Decomposition Methods
    # ========================================================================

    def _decompose_temporal_query(self, query: str) -> List[ReasoningStep]:
        """Decompose temporal queries into reasoning steps"""
        return [
            ReasoningStep(1, "Identify temporal sequence", "", 0.8),
            ReasoningStep(2, "Determine temporal relationships", "", 0.7),
            ReasoningStep(3, "Analyze cause-effect over time", "", 0.7),
            ReasoningStep(4, "Synthesize temporal conclusion", "", 0.8)
        ]

    def _decompose_spatial_query(self, query: str) -> List[ReasoningStep]:
        """Decompose spatial queries into reasoning steps"""
        return [
            ReasoningStep(1, "Identify spatial locations", "", 0.8),
            ReasoningStep(2, "Determine spatial relationships", "", 0.7),
            ReasoningStep(3, "Analyze spatial patterns", "", 0.7),
            ReasoningStep(4, "Synthesize spatial conclusion", "", 0.8)
        ]

    def _decompose_inductive_query(self, query: str) -> List[ReasoningStep]:
        """Decompose inductive queries into reasoning steps"""
        return [
            ReasoningStep(1, "Identify observations", "", 0.8),
            ReasoningStep(2, "Detect patterns", "", 0.7),
            ReasoningStep(3, "Formulate generalization", "", 0.7),
            ReasoningStep(4, "Validate generalization", "", 0.8)
        ]

    def _decompose_deductive_query(self, query: str) -> List[ReasoningStep]:
        """Decompose deductive queries into reasoning steps"""
        return [
            ReasoningStep(1, "Identify premises", "", 0.8),
            ReasoningStep(2, "Apply logical rules", "", 0.8),
            ReasoningStep(3, "Derive conclusion", "", 0.7),
            ReasoningStep(4, "Verify logical validity", "", 0.8)
        ]

    def _decompose_abductive_query(self, query: str) -> List[ReasoningStep]:
        """Decompose abductive queries into reasoning steps"""
        return [
            ReasoningStep(1, "Identify observations", "", 0.8),
            ReasoningStep(2, "Generate possible explanations", "", 0.7),
            ReasoningStep(3, "Evaluate explanations", "", 0.7),
            ReasoningStep(4, "Select best explanation", "", 0.8)
        ]

    # ========================================================================
    # Enhanced Step Reasoning Generation
    # ========================================================================

    def _generate_enhanced_step_reasoning(
        self,
        query: str,
        step: ReasoningStep,
        previous_steps: List[ReasoningStep],
        knowledge_items: List[Dict],
        evidence: List[str]
    ) -> str:
        """Generate enhanced reasoning with evidence"""
        base_reasoning = self._generate_step_reasoning(
            query, step, previous_steps, "", knowledge_items
        )
        
        # Add evidence if available
        if evidence:
            evidence_snippet = "; ".join(evidence[:2])
            base_reasoning += f" Evidence: {evidence_snippet}"
        
        return base_reasoning

    # ========================================================================
    # Relationship Detection
    # ========================================================================

    def detect_relationships(
        self,
        topic1: str,
        topic2: str,
        content: str
    ) -> List[Relationship]:
        """Detect relationships between topics in content"""
        relationships = []
        content_lower = content.lower()
        topic1_lower = topic1.lower()
        topic2_lower = topic2.lower()
        
        if topic1_lower not in content_lower or topic2_lower not in content_lower:
            return relationships
        
        # Causal relationships
        causal_patterns = ['causes', 'leads to', 'results in', 'affects', 'impacts']
        if any(pattern in content_lower for pattern in causal_patterns):
            relationships.append(Relationship(
                topic1=topic1,
                topic2=topic2,
                rel_type=RelationshipType.CAUSAL,
                strength=0.7,
                confidence=0.6,
                evidence="Causal relationship detected"
            ))
        
        # Hierarchical relationships
        hierarchical_patterns = ['is a type of', 'is part of', 'belongs to', 'contains', 'includes']
        if any(pattern in content_lower for pattern in hierarchical_patterns):
            relationships.append(Relationship(
                topic1=topic1,
                topic2=topic2,
                rel_type=RelationshipType.HIERARCHICAL,
                strength=0.6,
                confidence=0.5,
                evidence="Hierarchical relationship detected"
            ))
        
        # Associative relationships
        associative_patterns = ['related to', 'associated with', 'connected to', 'linked to']
        if any(pattern in content_lower for pattern in associative_patterns):
            relationships.append(Relationship(
                topic1=topic1,
                topic2=topic2,
                rel_type=RelationshipType.ASSOCIATIVE,
                strength=0.5,
                confidence=0.5,
                evidence="Associative relationship detected"
            ))
        
        return relationships

    # ========================================================================
    # Enhanced Conclusion Synthesis
    # ========================================================================

    def _synthesize_enhanced_conclusion(
        self,
        steps: List[ReasoningStep],
        query: str,
        reasoning_type: ReasoningType,
        relationships: List[Relationship] = None
    ) -> str:
        """Enhanced conclusion synthesis with relationships"""
        base_conclusion = self._synthesize_conclusion(steps, query, reasoning_type)
        
        # Add relationship information if available
        if relationships:
            rel_info = []
            for rel in relationships[:3]:  # Top 3 relationships
                rel_info.append(f"{rel.topic1} {rel.rel_type.value} {rel.topic2}")
            
            if rel_info:
                base_conclusion += f" Relationships: {', '.join(rel_info)}."
        
        return base_conclusion

    # ========================================================================
    # Main Entry Point Enhancement
    # ========================================================================

    def generate_reasoning_chain(
        self, 
        query: str, 
        context: str = "", 
        knowledge: List[Dict] = None,
        multi_topic_knowledge: Optional[Dict[str, List[Dict]]] = None,
        use_iterative_retrieval: bool = False
    ) -> ReasoningChain:
        """
        Generate a complete reasoning chain for the query
        
        Enhanced with caching, comprehensive analysis, and advanced features.

        Args:
            query: The user's query
            context: Conversation context
            knowledge: Relevant knowledge from brain (legacy parameter)
            multi_topic_knowledge: Dictionary mapping topic -> knowledge items
            use_iterative_retrieval: Whether to retrieve knowledge iteratively per step

        Returns:
            ReasoningChain with steps and conclusion
        """
        # Check cache first
        cached = self.check_cache(query)
        if cached:
            return cached
        
        start_time = time.time()
        
        # Comprehensive query analysis
        analysis = self.analyze_query_comprehensive(query)
        
        reasoning_type = analysis.reasoning_type

        # Create initial reasoning steps
        steps = self._decompose_query_into_steps(query, reasoning_type, context, knowledge)
        
        # Add temporal/spatial/inductive/deductive/abductive decomposition if needed
        if reasoning_type == ReasoningType.TEMPORAL:
            steps = self._decompose_temporal_query(query)
        elif reasoning_type == ReasoningType.SPATIAL:
            steps = self._decompose_spatial_query(query)
        elif reasoning_type == ReasoningType.INDUCTIVE:
            steps = self._decompose_inductive_query(query)
        elif reasoning_type == ReasoningType.DEDUCTIVE:
            steps = self._decompose_deductive_query(query)
        elif reasoning_type == ReasoningType.ABDUCTIVE:
            steps = self._decompose_abductive_query(query)

        # Accumulate knowledge across steps for iterative reasoning
        accumulated_knowledge = {}
        previous_step_contexts = []
        all_relationships = []

        # Generate step-by-step reasoning with iterative knowledge retrieval
        for i, step in enumerate(steps):
            if step.reasoning == "":  # Only fill in empty reasoning
                # Get knowledge for this step (iterative if enabled)
                step_knowledge = self._get_step_knowledge(
                    step,
                    query,
                    multi_topic_knowledge,
                    accumulated_knowledge,
                    previous_step_contexts,
                    use_iterative_retrieval
                )
                
                # Collect evidence
                knowledge_list = []
                if step_knowledge:
                    for items in step_knowledge.values():
                        knowledge_list.extend(items)
                elif knowledge:
                    knowledge_list = knowledge
                
                evidence = self.collect_evidence(knowledge_list, query)
                step.evidence = evidence[:5]  # Top 5 evidence items
                
                # Generate reasoning using step-specific knowledge
                step.reasoning = self._generate_step_reasoning(
                    query, 
                    step, 
                    steps[:i], 
                    context, 
                    knowledge_list,
                    previous_step_contexts
                )
                
                # Enhanced confidence assessment
                step.confidence = self._assess_step_confidence(step, knowledge_list)
                step.confidence = self.calibrate_confidence(
                    step.confidence,
                    len(evidence),
                    len(knowledge_list),
                    True  # Will be verified later
                )
                
                # Detect relationships
                if step_knowledge:
                    for topic1, items1 in step_knowledge.items():
                        for topic2, items2 in step_knowledge.items():
                            if topic1 != topic2:
                                for item1 in items1[:2]:
                                    rels = self.detect_relationships(
                                        topic1, topic2, item1.get('content', '')
                                    )
                                    all_relationships.extend(rels)
                
                # Accumulate knowledge and context for next steps
                if step_knowledge:
                    accumulated_knowledge.update(step_knowledge)
                    previous_step_contexts.append(step.reasoning)
                
                step.knowledge_used = knowledge_list

        # Generate conclusion with relationships
        conclusion = self._synthesize_enhanced_conclusion(
            steps, query, reasoning_type, all_relationships
        )

        # Calculate overall confidence
        avg_confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.5

        # Verify reasoning chain
        verification_result = self._verify_reasoning_chain(steps, conclusion)

        # Calculate reasoning quality score
        quality_score = self._calculate_reasoning_quality(steps, conclusion, verification_result)
        
        processing_time = time.time() - start_time

        chain = ReasoningChain(
            query=query,
            reasoning_type=reasoning_type,
            steps=steps,
            conclusion=conclusion,
            confidence=avg_confidence,
            verification_result=verification_result,
            reasoning_quality_score=quality_score,
            topics_involved=analysis.topics,
            relationships=[self._relationship_to_dict(r) for r in all_relationships],
            domains=analysis.domains,
            processing_time=processing_time,
            metadata={
                'intent': analysis.intent,
                'complexity': analysis.complexity,
                'complexity_level': analysis.complexity_level
            }
        )
        
        # Store in cache
        self.store_in_cache(query, chain)
        
        # Update statistics
        self.update_stats(chain)
        
        return chain

    def _relationship_to_dict(self, rel: Relationship) -> Dict:
        """Convert Relationship to dictionary"""
        return {
            'topic1': rel.topic1,
            'topic2': rel.topic2,
            'type': rel.rel_type.value,
            'strength': rel.strength,
            'confidence': rel.confidence,
            'evidence': rel.evidence
        }

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
        elif reasoning_type == ReasoningType.TEMPORAL:
            steps = self._decompose_temporal_query(query)
        elif reasoning_type == ReasoningType.SPATIAL:
            steps = self._decompose_spatial_query(query)
        elif reasoning_type == ReasoningType.INDUCTIVE:
            steps = self._decompose_inductive_query(query)
        elif reasoning_type == ReasoningType.DEDUCTIVE:
            steps = self._decompose_deductive_query(query)
        elif reasoning_type == ReasoningType.ABDUCTIVE:
            steps = self._decompose_abductive_query(query)
        else:
            steps = self._decompose_general_query(query)

        return steps


    # ========================================================================
    # Additional Utility Methods
    # ========================================================================

    def extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        words = self._extract_meaningful_words(text, min_length=4)
        # Filter by frequency
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        # Return most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]

    def find_similar_queries(self, query: str, query_history: List[str], threshold: float = 0.5) -> List[str]:
        """Find similar queries from history"""
        similar = []
        for hist_query in query_history:
            similarity = self._calculate_string_similarity(query, hist_query)
            if similarity >= threshold:
                similar.append(hist_query)
        return similar

    def generate_query_suggestions(self, query: str) -> List[str]:
        """Generate query suggestions based on current query"""
        suggestions = []
        
        # Add variations
        variations = self.generate_query_variations(query)
        suggestions.extend(variations)
        
        # Add expansions
        expansions = self.expand_query(query)
        suggestions.extend(expansions[:3])
        
        return suggestions[:5]

    def analyze_step_dependencies(self, steps: List[ReasoningStep]) -> Dict[int, List[int]]:
        """Analyze dependencies between steps"""
        dependency_graph = {}
        for step in steps:
            dependency_graph[step.step_number] = step.dependencies
        return dependency_graph

    def calculate_step_importance(self, step: ReasoningStep, all_steps: List[ReasoningStep]) -> float:
        """Calculate importance of a step based on dependencies"""
        # Count how many steps depend on this one
        dependents = sum(1 for s in all_steps if step.step_number in s.dependencies)
        importance = 0.5 + (dependents * 0.1)
        return self._normalize_confidence(importance)

    def identify_critical_steps(self, chain: ReasoningChain) -> List[ReasoningStep]:
        """Identify critical steps in reasoning chain"""
        critical = []
        for step in chain.steps:
            importance = self.calculate_step_importance(step, chain.steps)
            if importance > 0.7:
                critical.append(step)
        return critical

    def summarize_reasoning_chain(self, chain: ReasoningChain, max_length: int = 200) -> str:
        """Create a concise summary of reasoning chain"""
        summary_parts = [
            f"Query: {chain.query[:50]}...",
            f"Type: {chain.reasoning_type.value}",
            f"Steps: {len(chain.steps)}",
            f"Confidence: {chain.confidence:.2f}"
        ]
        
        if chain.topics_involved:
            summary_parts.append(f"Topics: {', '.join(chain.topics_involved[:3])}")
        
        summary = " | ".join(summary_parts)
        return summary[:max_length]

    def compare_reasoning_chains(self, chain1: ReasoningChain, chain2: ReasoningChain) -> Dict[str, Any]:
        """Compare two reasoning chains"""
        return {
            'confidence_diff': chain1.confidence - chain2.confidence,
            'quality_diff': chain1.reasoning_quality_score - chain2.reasoning_quality_score,
            'step_count_diff': len(chain1.steps) - len(chain2.steps),
            'verification_match': chain1.verification_result == chain2.verification_result,
            'type_match': chain1.reasoning_type == chain2.reasoning_type
        }

    def extract_reasoning_patterns(self, chains: List[ReasoningChain]) -> Dict[str, Any]:
        """Extract common patterns from multiple reasoning chains"""
        patterns = {
            'common_step_types': defaultdict(int),
            'common_topics': defaultdict(int),
            'common_domains': defaultdict(int),
            'avg_step_count': 0.0,
            'common_reasoning_types': defaultdict(int)
        }
        
        step_counts = []
        for chain in chains:
            patterns['common_reasoning_types'][chain.reasoning_type.value] += 1
            
            for step in chain.steps:
                patterns['common_step_types'][step.description] += 1
            
            for topic in chain.topics_involved:
                patterns['common_topics'][topic] += 1
            
            for domain in chain.domains:
                patterns['common_domains'][domain.value] += 1
            
            step_counts.append(len(chain.steps))
        
        patterns['avg_step_count'] = sum(step_counts) / len(step_counts) if step_counts else 0.0
        
        return patterns

    def optimize_reasoning_chain(self, chain: ReasoningChain) -> ReasoningChain:
        """Optimize reasoning chain by removing redundant steps"""
        optimized_steps = []
        seen_reasoning = set()
        
        for step in chain.steps:
            # Skip if reasoning is too similar to previous steps
            reasoning_hash = hash(step.reasoning[:50])
            if reasoning_hash not in seen_reasoning:
                seen_reasoning.add(reasoning_hash)
                optimized_steps.append(step)
        
        # Renumber steps
        for i, step in enumerate(optimized_steps, 1):
            step.step_number = i
        
        # Recalculate metrics
        avg_confidence = sum(s.confidence for s in optimized_steps) / len(optimized_steps) if optimized_steps else 0.5
        quality_score = self._calculate_reasoning_quality(optimized_steps, chain.conclusion, chain.verification_result)
        
        return ReasoningChain(
            query=chain.query,
            reasoning_type=chain.reasoning_type,
            steps=optimized_steps,
            conclusion=chain.conclusion,
            confidence=avg_confidence,
            verification_result=chain.verification_result,
            reasoning_quality_score=quality_score,
            topics_involved=chain.topics_involved,
            relationships=chain.relationships,
            domains=chain.domains,
            processing_time=chain.processing_time,
            metadata=chain.metadata
        )

    def export_reasoning_data(self, chain: ReasoningChain, format: str = 'json') -> str:
        """Export reasoning chain in various formats"""
        if format == 'json':
            return self.format_reasoning_json(chain)
        elif format == 'markdown':
            return self.format_reasoning_markdown(chain)
        elif format == 'html':
            return self.format_reasoning_html(chain)
        else:
            return self.format_reasoning_output(chain)

    def import_reasoning_data(self, data: str, format: str = 'json') -> Optional[ReasoningChain]:
        """Import reasoning chain from various formats"""
        try:
            if format == 'json':
                obj = json.loads(data)
                # Reconstruct chain from JSON
                steps = []
                for step_data in obj.get('steps', []):
                    step = ReasoningStep(
                        step_number=step_data['step_number'],
                        description=step_data['description'],
                        reasoning=step_data['reasoning'],
                        confidence=step_data['confidence'],
                        evidence=step_data.get('evidence', []),
                        dependencies=step_data.get('dependencies', [])
                    )
                    steps.append(step)
                
                reasoning_type = ReasoningType(obj.get('reasoning_type', 'general'))
                
                return ReasoningChain(
                    query=obj.get('query', ''),
                    reasoning_type=reasoning_type,
                    steps=steps,
                    conclusion=obj.get('conclusion', ''),
                    confidence=obj.get('confidence', 0.5),
                    verification_result=obj.get('verification_result', True),
                    reasoning_quality_score=obj.get('quality_score', 0.0),
                    topics_involved=obj.get('topics_involved', []),
                    domains=[Domain(d) for d in obj.get('domains', [])]
                )
        except Exception:
            return None

    def create_reasoning_report(self, chains: List[ReasoningChain]) -> str:
        """Create comprehensive report from multiple reasoning chains"""
        stats = self.calculate_stats(chains)
        patterns = self.extract_reasoning_patterns(chains)
        
        report_lines = [
            "# Reasoning Analysis Report\n",
            f"## Summary\n",
            f"- Total Queries: {stats['total_queries']}\n",
            f"- Average Confidence: {stats['avg_confidence']:.2f}\n",
            f"- Average Quality Score: {stats['avg_quality_score']:.2f}\n",
            f"- Verification Rate: {stats['verification_rate']:.2%}\n",
            f"- Average Steps per Chain: {stats['avg_steps_per_chain']:.1f}\n",
            "\n## Reasoning Type Distribution\n"
        ]
        
        for rtype, count in stats['reasoning_type_distribution'].items():
            report_lines.append(f"- {rtype}: {count}\n")
        
        report_lines.append("\n## Common Topics\n")
        sorted_topics = sorted(patterns['common_topics'].items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:10]:
            report_lines.append(f"- {topic}: {count}\n")
        
        return "".join(report_lines)

    def validate_and_fix_chain(self, chain: ReasoningChain) -> Tuple[ReasoningChain, List[str]]:
        """Validate chain and fix issues if possible"""
        valid, errors = self.validate_reasoning_chain(chain)
        
        if valid:
            return chain, []
        
        # Try to fix common issues
        fixed_steps = chain.steps.copy()
        fixes = []
        
        # Fix step numbering
        for i, step in enumerate(fixed_steps, 1):
            if step.step_number != i:
                step.step_number = i
                fixes.append(f"Fixed step numbering for step {i}")
        
        # Fix confidence out of range
        for step in fixed_steps:
            if step.confidence < 0.0 or step.confidence > 1.0:
                step.confidence = self._normalize_confidence(step.confidence)
                fixes.append(f"Fixed confidence for step {step.step_number}")
        
        # Recalculate chain metrics
        avg_confidence = sum(s.confidence for s in fixed_steps) / len(fixed_steps) if fixed_steps else 0.5
        quality_score = self._calculate_reasoning_quality(fixed_steps, chain.conclusion, chain.verification_result)
        
        fixed_chain = ReasoningChain(
            query=chain.query,
            reasoning_type=chain.reasoning_type,
            steps=fixed_steps,
            conclusion=chain.conclusion,
            confidence=avg_confidence,
            verification_result=chain.verification_result,
            reasoning_quality_score=quality_score,
            topics_involved=chain.topics_involved,
            relationships=chain.relationships,
            domains=chain.domains,
            processing_time=chain.processing_time,
            metadata=chain.metadata
        )
        
        return fixed_chain, fixes + errors

    def get_reasoning_insights(self, chain: ReasoningChain) -> Dict[str, Any]:
        """Get insights about reasoning chain"""
        return {
            'total_steps': len(chain.steps),
            'avg_step_confidence': sum(s.confidence for s in chain.steps) / len(chain.steps) if chain.steps else 0.0,
            'total_evidence_items': sum(len(s.evidence) for s in chain.steps),
            'critical_steps': len(self.identify_critical_steps(chain)),
            'topics_count': len(chain.topics_involved),
            'domains_count': len(chain.domains),
            'relationships_count': len(chain.relationships),
            'processing_time': chain.processing_time,
            'quality_tier': (
                'high' if chain.reasoning_quality_score > 0.8 else
                'medium' if chain.reasoning_quality_score > 0.6 else
                'low'
            )
        }

    def enhance_reasoning_with_context(
        self,
        chain: ReasoningChain,
        additional_context: str
    ) -> ReasoningChain:
        """Enhance reasoning chain with additional context"""
        # Add context to conclusion
        enhanced_conclusion = f"{chain.conclusion} [Context: {additional_context[:100]}]"
        
        return ReasoningChain(
            query=chain.query,
            reasoning_type=chain.reasoning_type,
            steps=chain.steps,
            conclusion=enhanced_conclusion,
            confidence=chain.confidence,
            verification_result=chain.verification_result,
            reasoning_quality_score=chain.reasoning_quality_score,
            topics_involved=chain.topics_involved,
            relationships=chain.relationships,
            domains=chain.domains,
            processing_time=chain.processing_time,
            metadata={**chain.metadata, 'additional_context': additional_context}
        )


# Global instance
_reasoning_engine = None

def get_reasoning_engine():
    """Get or create global reasoning engine instance"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine

