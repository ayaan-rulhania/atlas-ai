"""
Causal Reasoner - Specialized reasoning engine for causal chain problems
requiring multi-topic knowledge and step-by-step causal reasoning.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .reasoning_engine import ReasoningStep, ReasoningChain, ReasoningType
from .multi_topic_retriever import get_multi_topic_retriever
from .knowledge_synthesizer import get_knowledge_synthesizer
from .topic_relationship_mapper import get_topic_relationship_mapper


@dataclass
class CausalStep:
    """Represents a step in a causal chain"""
    step_number: int
    cause_topic: str
    effect_topic: str
    mechanism: str
    knowledge_items: List[Dict]
    confidence: float
    reasoning: str = ""


class CausalReasoner:
    """
    Specialized reasoning engine for causal chain problems.
    Breaks down causal questions into step-by-step reasoning using multi-topic knowledge.
    """
    
    def __init__(self):
        self.multi_topic_retriever = get_multi_topic_retriever()
        self.knowledge_synthesizer = get_knowledge_synthesizer()
        self.relationship_mapper = get_topic_relationship_mapper()
    
    def solve_causal_query(
        self,
        query: str,
        context: str = ""
    ) -> ReasoningChain:
        """
        Solve a causal query by breaking it into causal chain steps.
        
        Args:
            query: Causal query (e.g., "How does climate change affect economic policy?")
            context: Additional context
            
        Returns:
            ReasoningChain with causal reasoning steps
        """
        # Identify topics involved in the causal query
        topics_data = self.multi_topic_retriever.identify_topics(query, max_topics=5)
        topics = [t['topic'] for t in topics_data]
        
        if len(topics) < 2:
            # Not a multi-topic causal query, use standard reasoning
            from .reasoning_engine import get_reasoning_engine
            reasoning_engine = get_reasoning_engine()
            return reasoning_engine.generate_reasoning_chain(query, context)
        
        # Retrieve knowledge for all topics
        knowledge_by_topic = self.multi_topic_retriever.retrieve_multi_topic_knowledge(
            query,
            topics=topics_data,
            max_knowledge_per_topic=5
        )
        
        # Build relationship graph
        relationship_graph = self.relationship_mapper.build_relationship_graph(
            topics,
            knowledge_by_topic
        )
        
        # Decompose into causal steps
        causal_steps = self._decompose_causal_chain(
            query,
            topics,
            relationship_graph,
            knowledge_by_topic
        )
        
        # Generate reasoning for each step
        reasoning_steps = []
        accumulated_context = []
        
        for i, causal_step in enumerate(causal_steps):
            # Get knowledge for this causal step
            step_knowledge = self._get_step_knowledge(
                causal_step,
                knowledge_by_topic,
                accumulated_context
            )
            
            # Synthesize knowledge for this step
            synthesis_result = self.knowledge_synthesizer.synthesize_knowledge(
                step_knowledge,
                query,
                "\n".join(accumulated_context) if accumulated_context else None
            )
            
            # Generate reasoning
            reasoning = self._generate_causal_reasoning(
                causal_step,
                synthesis_result,
                accumulated_context
            )
            
            # Create reasoning step
            reasoning_step = ReasoningStep(
                step_number=causal_step.step_number,
                description=f"Analyze causal relationship: {causal_step.cause_topic} → {causal_step.effect_topic}",
                reasoning=reasoning,
                confidence=causal_step.confidence,
                evidence=synthesis_result.get('relationships', [])
            )
            
            reasoning_steps.append(reasoning_step)
            accumulated_context.append(reasoning)
        
        # Generate conclusion
        conclusion = self._synthesize_causal_conclusion(reasoning_steps, query)
        
        # Calculate overall confidence
        avg_confidence = sum(step.confidence for step in reasoning_steps) / len(reasoning_steps) if reasoning_steps else 0.5
        
        return ReasoningChain(
            query=query,
            reasoning_type=ReasoningType.CAUSAL,
            steps=reasoning_steps,
            conclusion=conclusion,
            confidence=avg_confidence,
            verification_result=True,
            reasoning_quality_score=avg_confidence
        )
    
    def _decompose_causal_chain(
        self,
        query: str,
        topics: List[str],
        relationship_graph: Dict[str, List[Dict]],
        knowledge_by_topic: Dict[str, List[Dict]]
    ) -> List[CausalStep]:
        """Decompose query into causal chain steps."""
        causal_steps = []
        
        # Try to find causal path between topics
        if len(topics) >= 2:
            # Look for causal relationships in graph
            for i, topic1 in enumerate(topics):
                for topic2 in topics[i+1:]:
                    # Check for causal relationship
                    relationships = relationship_graph.get(topic1, [])
                    causal_rels = [r for r in relationships 
                                 if r.get('topic2') == topic2 and r.get('relationship_type') == 'causal']
                    
                    if causal_rels:
                        # Found causal relationship
                        rel = causal_rels[0]
                        causal_steps.append(CausalStep(
                            step_number=len(causal_steps) + 1,
                            cause_topic=topic1,
                            effect_topic=topic2,
                            mechanism=rel.get('evidence', ''),
                            knowledge_items=knowledge_by_topic.get(topic1, []) + knowledge_by_topic.get(topic2, []),
                            confidence=rel.get('strength', 0.5)
                        ))
            
            # If no explicit causal relationships found, create steps based on query structure
            if not causal_steps and len(topics) >= 2:
                # Assume first topic causes/affects second topic
                causal_steps.append(CausalStep(
                    step_number=1,
                    cause_topic=topics[0],
                    effect_topic=topics[1] if len(topics) > 1 else topics[0],
                    mechanism='',
                    knowledge_items=knowledge_by_topic.get(topics[0], []) + knowledge_by_topic.get(topics[1] if len(topics) > 1 else topics[0], []),
                    confidence=0.6
                ))
        
        # If still no steps, create generic causal steps
        if not causal_steps:
            for i, topic in enumerate(topics[:3]):  # Max 3 steps
                next_topic = topics[i+1] if i+1 < len(topics) else topics[0]
                causal_steps.append(CausalStep(
                    step_number=i+1,
                    cause_topic=topic,
                    effect_topic=next_topic,
                    mechanism='',
                    knowledge_items=knowledge_by_topic.get(topic, []),
                    confidence=0.5
                ))
        
        return causal_steps
    
    def _get_step_knowledge(
        self,
        causal_step: CausalStep,
        knowledge_by_topic: Dict[str, List[Dict]],
        accumulated_context: List[str]
    ) -> Dict[str, List[Dict]]:
        """Get knowledge relevant to a causal step."""
        step_knowledge = {}
        
        # Get knowledge for cause topic
        if causal_step.cause_topic in knowledge_by_topic:
            step_knowledge[causal_step.cause_topic] = knowledge_by_topic[causal_step.cause_topic]
        
        # Get knowledge for effect topic
        if causal_step.effect_topic in knowledge_by_topic:
            step_knowledge[causal_step.effect_topic] = knowledge_by_topic[causal_step.effect_topic]
        
        return step_knowledge
    
    def _generate_causal_reasoning(
        self,
        causal_step: CausalStep,
        synthesis_result: Dict,
        accumulated_context: List[str]
    ) -> str:
        """Generate reasoning for a causal step."""
        cause = causal_step.cause_topic
        effect = causal_step.effect_topic
        mechanism = causal_step.mechanism
        
        reasoning_parts = [
            f"Step {causal_step.step_number}: Analyzing how '{cause}' affects '{effect}'"
        ]
        
        # Add synthesized knowledge
        synthesized_context = synthesis_result.get('synthesized_context', '')
        if synthesized_context:
            # Extract key points (first 200 chars)
            key_points = synthesized_context[:200].replace('\n', ' ')
            reasoning_parts.append(f"Knowledge: {key_points}")
        
        # Add mechanism if available
        if mechanism:
            reasoning_parts.append(f"Mechanism: {mechanism}")
        
        # Add relationships
        relationships = synthesis_result.get('relationships', [])
        if relationships:
            rel_info = []
            for rel in relationships[:2]:  # Max 2 relationships
                rel_info.append(f"{rel['topic1']} {rel['relationship_type']} {rel['topic2']}")
            if rel_info:
                reasoning_parts.append(f"Relationships: {', '.join(rel_info)}")
        
        # Reference previous steps if available
        if accumulated_context:
            reasoning_parts.append(f"Building on previous analysis: {accumulated_context[-1][:150]}")
        
        return ". ".join(reasoning_parts)
    
    def _synthesize_causal_conclusion(
        self,
        reasoning_steps: List[ReasoningStep],
        query: str
    ) -> str:
        """Synthesize final conclusion from causal reasoning steps."""
        if not reasoning_steps:
            return "Unable to determine the causal relationship."
        
        # Extract key insights from each step
        insights = []
        for step in reasoning_steps:
            if step.reasoning:
                # Extract the main point (first sentence or first 100 chars)
                main_point = step.reasoning.split('.')[0]
                if len(main_point) > 100:
                    main_point = step.reasoning[:100] + "..."
                insights.append(main_point)
        
        conclusion = f"Based on the causal analysis: {' '.join(insights)}"
        
        return conclusion


# Global instance
_causal_reasoner = None


def get_causal_reasoner() -> CausalReasoner:
    """Get or create the global causal reasoner instance."""
    global _causal_reasoner
    if _causal_reasoner is None:
        _causal_reasoner = CausalReasoner()
    return _causal_reasoner

