"""
Inference script for the All-Rounder AI Model - Thor 1.1 (Enhanced Version).
"""
import torch
import argparse
import yaml
import os
import math
from typing import Dict, Optional, List
import torch.nn.functional as F

from models import AllRounderModel
from utils import SimpleTokenizer
from services.reasoning_engine import get_reasoning_engine
from services.query_intent_analyzer import get_query_intent_analyzer
from services.context_manager import get_context_manager
from services.problem_solver import get_problem_solver
from services.logical_reasoner import get_logical_reasoner
from services.math_solver import get_math_solver

# Thor 1.1 Enhanced version identifier
THOR_VERSION = "1.1-enhanced"


def load_config(config_path: str):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_device():
    """Setup device (CUDA or CPU)."""
    if torch.cuda.is_available():
        return torch.device('cuda')
    return torch.device('cpu')


class AllRounderInference:
    """Inference interface for the All-Rounder model."""
    
    def __init__(self, model_path: str, tokenizer_path: str, config_path: str = 'config/config/config.yaml'):
        self.config = load_config(config_path)
        self.device = setup_device()
        
        # Load tokenizer
        self.tokenizer = SimpleTokenizer.load(tokenizer_path)
        
        # Prepare task configs
        tasks_config = self.config.get('tasks', [])
        task_configs = {task['name']: task for task in tasks_config if task.get('enabled', True)}
        
        # Load model
        self.model = AllRounderModel.load_model(model_path, task_configs, self.config)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        print(f"Thor {THOR_VERSION} model loaded from {model_path}")
        print(f"Device: {self.device}")
        print(f"Available tasks: {list(task_configs.keys())}")
        print(f"Enhanced features: Multi-step generation, advanced decoding, improved reasoning, better context understanding")
    
    def predict(
        self,
        text: str,
        task: str,
        max_length: Optional[int] = None,
        max_new_tokens: Optional[int] = None,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Make a prediction for the given text and task.
        
        Args:
            text: Input text
            task: Task name (e.g., 'text_classification', 'sentiment_analysis')
            max_length: Maximum sequence length (for input)
            max_new_tokens: Maximum new tokens to generate (for text_generation task)
        
        Returns:
            Dictionary with predictions
        """
        if max_length is None:
            max_length = self.config['model']['max_position_embeddings']
        
        # Store max_new_tokens for text generation
        if max_new_tokens is None:
            max_new_tokens = self.config.get('tasks', [{}])[0].get('max_length', 256) if task == 'text_generation' else None
        self._max_new_tokens = max_new_tokens

        # TODO: Implement conversation context management
        # Manage conversation context if provided
        context_text = ""
        context_metadata = {}
        if conversation_context and task == 'text_generation':
            # context_manager = get_context_manager()
            # context_result = context_manager.manage_context(
            #     conversation_context,
            #     text,
            #     max_tokens=max_length or self.max_position_embeddings
            # )
            # context_text = context_result.get('context', '')
            # context_metadata = {
            #     'context_summarized': context_result.get('summarized', False),
            #     'compression_ratio': context_result.get('compression_ratio', 1.0),
            #     'selected_turns': context_result.get('selected_turns', 0),
            #     'total_turns': context_result.get('total_turns', 0)
            # }
            pass
        
        # Get actual model max position embeddings (might be smaller than config)
        # Check from loaded model if available
        model_max_pos = 256  # Default safe value
        if hasattr(self, 'model') and hasattr(self.model, 'max_position_embeddings'):
            model_max_pos = self.model.max_position_embeddings
        elif 'model' in self.config:
            model_max_pos = self.config['model'].get('max_position_embeddings', 256)
        
        # Use the smaller of the two
        effective_max = min(max_length, model_max_pos)
        
        # Tokenize input
        input_ids = self.tokenizer.encode(text, max_length=effective_max)
        attention_mask = [1 if tid != 0 else 0 for tid in input_ids]

        # Convert to tensors
        input_ids_tensor = torch.tensor([input_ids], dtype=torch.long).to(self.device)
        attention_mask_tensor = torch.tensor([attention_mask], dtype=torch.long).to(self.device)

        # Handle long contexts with compression/sliding window if needed
        if len(input_ids) > model_max_pos:
            input_ids_tensor, attention_mask_tensor, processed_text = self._prepare_long_context(
                text, input_ids_tensor, attention_mask_tensor, model_max_pos
            )
            # Update result metadata
            result['context_processed'] = True
            result['original_length'] = len(text)
            result['processed_length'] = len(processed_text) if 'processed_text' in locals() else len(text)

        input_ids = input_ids_tensor
        attention_mask = attention_mask_tensor
        
        # Forward pass
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                task=task
            )
        
        # Process outputs based on task
        result = {'task': task, 'input': text}
        
        if task == 'text_classification' or task == 'sentiment_analysis':
            logits = outputs['logits']
            probs = torch.softmax(logits, dim=-1)
            predicted_class = torch.argmax(logits, dim=-1).item()
            confidence = probs[0][predicted_class].item()
            
            result['prediction'] = predicted_class
            result['confidence'] = confidence
            result['probabilities'] = probs[0].cpu().tolist()
        
        elif task == 'named_entity_recognition':
            logits = outputs['logits']
            predictions = torch.argmax(logits, dim=-1)[0].cpu().tolist()
            tokens = self.tokenizer.decode(input_ids[0].cpu().tolist(), skip_special_tokens=False).split()
            
            result['predictions'] = predictions[:len(tokens)]
            result['tokens'] = tokens
        
        elif task == 'question_answering':
            start_logits = outputs['start_logits']
            end_logits = outputs['end_logits']
            start_pos = torch.argmax(start_logits, dim=-1).item()
            end_pos = torch.argmax(end_logits, dim=-1).item()
            
            # Extract answer span
            answer_tokens = input_ids[0][start_pos:end_pos+1].cpu().tolist()
            answer = self.tokenizer.decode(answer_tokens, skip_special_tokens=True)
            
            result['answer'] = answer
            result['start_position'] = start_pos
            result['end_position'] = end_pos
        
        elif task == 'text_generation':
            # Enhanced Thor 1.1: Multi-step autoregressive generation with advanced decoding
            max_gen_tokens = getattr(self, '_max_new_tokens', None) or 256

            # Query-type aware generation parameters
            query_type = self._detect_query_type(text)
            generation_params = self._get_generation_params_for_query_type(query_type, max_gen_tokens)

            # Add decoding strategy from kwargs or config
            decoding_strategy = kwargs.get('decoding_strategy', 'nucleus')  # Default to nucleus sampling
            generation_params['decoding_strategy'] = decoding_strategy

            # Add beam width if specified
            if 'beam_width' in kwargs:
                generation_params['beam_width'] = kwargs['beam_width']

            # Check if query requires advanced problem solving
            reasoning_engine = get_reasoning_engine()
            query_analyzer = get_query_intent_analyzer()
            query_analysis = query_analyzer.analyze(text)

            # Extract context and knowledge from kwargs if provided
            context = kwargs.get('context', '')
            knowledge = kwargs.get('knowledge', [])

            # Determine the best solving approach
            solving_approach = self._determine_solving_approach(text, query_analysis, context_text, knowledge)

            if solving_approach == 'logical_reasoning':
                result = self._solve_with_logical_reasoner(text)
            elif solving_approach == 'mathematical_reasoning':
                result = self._solve_with_math_solver(text)
            elif solving_approach == 'multi_step_problem_solving':
                # Check if multi-topic and get multi-topic knowledge
                is_multi_topic = self._is_multi_topic_query(text, query_analysis)
                multi_topic_knowledge = None
                
                if is_multi_topic:
                    try:
                        from .multi_topic_retriever import get_multi_topic_retriever
                        retriever = get_multi_topic_retriever()
                        multi_topic_data = retriever.get_enhanced_multi_topic_knowledge(
                            text,
                            max_topics=5,
                            max_knowledge_per_topic=5
                        )
                        multi_topic_knowledge = multi_topic_data.get('knowledge_by_topic', {})
                    except Exception as e:
                        print(f"[Inference] Multi-topic retrieval error: {e}")
                
                result = self._solve_with_problem_solver(
                    text, input_ids, attention_mask,
                    generation_params, context_text, knowledge,
                    multi_topic_knowledge=multi_topic_knowledge
                )
            elif solving_approach == 'reasoning':
                result = self._generate_with_reasoning(text, input_ids, attention_mask,
                                                     generation_params, context_text, knowledge)
            else:
                # Choose decoding method based on strategy
                if decoding_strategy == 'beam_search':
                    result = self._beam_search_decode(text, input_ids, attention_mask, generation_params)
                elif decoding_strategy == 'contrastive':
                    result = self._contrastive_decode(text, input_ids, attention_mask, generation_params)
                else:
                    result = self._generate_enhanced_text(text, input_ids, attention_mask, generation_params)

        # Add context metadata if context management was used
        if context_metadata:
            result['context_management'] = context_metadata

        return result

    def _determine_solving_approach(self, text: str, query_analysis: Dict, context: str, knowledge: List[Dict]) -> str:
        """
        Determine the best approach for solving the query.

        Returns:
            'logical_reasoning': For logical proofs and arguments
            'mathematical_reasoning': For mathematical calculations and proofs
            'multi_step_problem_solving': For complex problems requiring step-by-step decomposition
            'reasoning': For problems benefiting from chain-of-thought reasoning
            'standard': For straightforward generation
        """
        reasoning_engine = get_reasoning_engine()
        logical_reasoner = get_logical_reasoner()
        math_solver = get_math_solver()

        # Check for multi-topic queries (requires multiple domains/topics)
        is_multi_topic = self._is_multi_topic_query(text, query_analysis)
        
        # Check for logical reasoning
        logical_analysis = logical_reasoner.analyze_logical_query(text)
        if logical_analysis['is_logical'] and logical_analysis['requires_proof']:
            return 'logical_reasoning'

        # Check for mathematical reasoning
        math_analysis = math_solver.analyze_math_query(text)
        if math_analysis['is_mathematical'] and math_analysis['requires_calculation']:
            return 'mathematical_reasoning'

        # Check for multi-step problem indicators
        complexity = query_analysis.get('query_complexity', 0.0)
        decomposed_queries = query_analysis.get('decomposed_queries', [])
        reasoning_type = query_analysis.get('reasoning_type')

        # Multi-step problem solving for highly complex queries or multi-topic queries
        if (is_multi_topic or
            complexity > 0.8 or
            len(decomposed_queries) > 2 or
            reasoning_type in ['mathematical', 'causal', 'comparative'] or
            self._requires_multi_step_solving(text, query_analysis)):

            # Additional check: query length and structure
            if (len(text.split()) > 20 or
                any(word in text.lower() for word in ['how to', 'explain why', 'analyze', 'solve', 'determine']) or
                text.count('?') > 1 or
                is_multi_topic):

                return 'multi_step_problem_solving'

        # Chain-of-thought reasoning for moderately complex queries or multi-topic causal queries
        if is_multi_topic and reasoning_type == 'causal':
            return 'reasoning'  # Use reasoning with multi-topic support
        
        if reasoning_engine.should_use_reasoning(text, query_analysis):
            return 'reasoning'

        return 'standard'
    
    def _is_multi_topic_query(self, text: str, query_analysis: Dict) -> bool:
        """Detect if query requires knowledge from multiple topics/domains."""
        try:
            from .multi_topic_retriever import get_multi_topic_retriever
            
            retriever = get_multi_topic_retriever()
            topics = retriever.identify_topics(text, max_topics=3)
            
            # Check if multiple topics from different domains were identified
            if len(topics) >= 2:
                domains = set(t['domain'] for t in topics if t['domain'] != 'general')
                # Multi-topic if we have 2+ topics or 2+ different domains
                return len(domains) >= 2 or len(topics) >= 2
            
            # Also check query patterns that indicate multi-topic
            text_lower = text.lower()
            multi_topic_patterns = [
                'how does', 'how do', 'why does', 'what causes',
                'affect', 'impact', 'influence', 'relate to',
                'compare', 'versus', 'vs', 'difference between',
                'relationship between', 'connection between'
            ]
            
            if any(pattern in text_lower for pattern in multi_topic_patterns):
                return True
            
            return False
        except ImportError:
            # Fallback: simple heuristic
            text_lower = text.lower()
            # Count distinct domain keywords
            domain_keywords = {
                'science': ['science', 'physics', 'chemistry', 'biology'],
                'economics': ['economic', 'economy', 'market', 'finance'],
                'technology': ['technology', 'tech', 'computer', 'software'],
                'environment': ['climate', 'environment', 'pollution'],
                'politics': ['politics', 'government', 'policy', 'law']
            }
            
            domains_found = set()
            for domain, keywords in domain_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    domains_found.add(domain)
            
            return len(domains_found) >= 2

    def _requires_multi_step_solving(self, text: str, query_analysis: Dict) -> bool:
        """Check if query specifically requires multi-step problem solving"""
        text_lower = text.lower()

        # Multi-step indicators
        multi_step_indicators = [
            'step by step', 'break down', 'analyze the following', 'solve for',
            'determine how', 'figure out why', 'explain the process',
            'what are the steps', 'how does it work', 'walk me through'
        ]

        if any(indicator in text_lower for indicator in multi_step_indicators):
            return True

        # Complex mathematical or logical queries
        if query_analysis.get('reasoning_type') == 'mathematical' and len(text.split()) > 15:
            return True

        # Multi-part questions
        if text.count('?') >= 3 or len(query_analysis.get('decomposed_queries', [])) >= 3:
            return True

        return False

    def _solve_with_problem_solver(
        self,
        text: str,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        generation_params: Optional[Dict] = None,
        context: str = "",
        knowledge: List[Dict] = None,
        multi_topic_knowledge: Optional[Dict[str, List[Dict]]] = None
    ) -> Dict:
        """
        Solve complex problems using the multi-step problem solver.
        """
        try:
            problem_solver = get_problem_solver()

            # Convert multi_topic_knowledge to list format if provided
            if multi_topic_knowledge:
                # Flatten multi-topic knowledge into a list
                all_knowledge = []
                for items in multi_topic_knowledge.values():
                    all_knowledge.extend(items)
                # Combine with provided knowledge
                if knowledge:
                    knowledge = knowledge + all_knowledge
                else:
                    knowledge = all_knowledge

            # Solve the problem
            solution = problem_solver.solve_problem(text, context, knowledge)

            # Format the solution for response
            formatted_solution = self._format_problem_solution(solution)

            # Create result similar to generation results
            result = {
                'generated_text': formatted_solution,
                'version': THOR_VERSION,
                'task': 'text_generation',
                'input': text,
                'problem_solving': {
                    'approach': 'multi_step_problem_solving',
                    'total_steps': solution.execution_summary['total_steps'],
                    'completed_steps': solution.execution_summary['completed_steps'],
                    'solution_confidence': solution.confidence,
                    'solution_quality': solution.solution_quality,
                    'strategy_used': solution.plan.solution_strategy,
                    'execution_time': solution.execution_summary['execution_time']
                }
            }

            return result

        except Exception as e:
            print(f"Error in multi-step problem solving: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to reasoning-based generation
            return self._generate_with_reasoning(text, input_ids, attention_mask,
                                                generation_params, context, knowledge)

    def _format_problem_solution(self, solution) -> str:
        """Format a problem solution for user consumption"""
        lines = [
            f"Solution to: {solution.problem}\n",
            f"Approach: {solution.plan.solution_strategy.replace('_', ' ').title()}\n",
            f"Problem Complexity: {solution.plan.estimated_total_complexity:.2f}/1.0\n",
            "=" * 50,
            ""
        ]

        # Add step-by-step breakdown
        for step in solution.plan.steps:
            status_icon = "✓" if step.status == "completed" else "✗" if step.status == "failed" else "○"
            lines.append(f"{status_icon} Step {step.step_number}: {step.description}")
            if step.result:
                lines.append(f"   Result: {step.result}")
            lines.append("")

        # Add summary
        lines.extend([
            "=" * 50,
            "Solution Summary:",
            f"- Total Steps: {solution.execution_summary['total_steps']}",
            f"- Completed: {solution.execution_summary['completed_steps']}",
            f"- Failed: {solution.execution_summary['failed_steps']}",
            f"- Confidence: {solution.confidence:.2f}",
            f"- Quality Score: {solution.solution_quality:.2f}",
            ""
        ])

        return "\n".join(lines)

    def _adapt_generation_params_for_reasoning(self, base_params: Dict, reasoning_chain) -> Dict:
        """
        Adapt generation parameters based on reasoning complexity and type.
        """
        adapted_params = base_params.copy()

        # Adjust parameters based on reasoning type
        reasoning_type = reasoning_chain.reasoning_type.value

        if reasoning_type == 'complex_reasoning':
            # For complex reasoning, be more focused and deterministic
            adapted_params['temperature'] = min(base_params.get('temperature', 0.8), 0.7)
            adapted_params['top_p'] = min(base_params.get('top_p', 0.95), 0.9)
            adapted_params['top_k'] = min(base_params.get('top_k', 50), 40)

        elif reasoning_type == 'technical':
            # For technical content, be very precise
            adapted_params['temperature'] = min(base_params.get('temperature', 0.8), 0.6)
            adapted_params['top_p'] = min(base_params.get('top_p', 0.95), 0.85)
            adapted_params['top_k'] = min(base_params.get('top_k', 50), 30)

        elif reasoning_type == 'creative':
            # For creative reasoning, allow more diversity
            adapted_params['temperature'] = max(base_params.get('temperature', 0.8), 0.9)
            adapted_params['top_p'] = max(base_params.get('top_p', 0.95), 0.95)
            adapted_params['top_k'] = max(base_params.get('top_k', 50), 60)

        # Adjust based on reasoning confidence
        confidence = reasoning_chain.confidence
        if confidence < 0.7:
            # Lower confidence = be more conservative
            adapted_params['temperature'] = adapted_params.get('temperature', 0.8) * 0.8
            adapted_params['repetition_penalty'] = max(adapted_params.get('repetition_penalty', 1.1), 1.2)

        # Adjust based on reasoning steps (more steps = more structured response needed)
        num_steps = len(reasoning_chain.steps)
        if num_steps > 3:
            adapted_params['max_new_tokens'] = max(adapted_params.get('max_new_tokens', 256),
                                                 min(num_steps * 50, 512))

        return adapted_params

    def _validate_and_enhance_response_quality(self, result: Dict, reasoning_chain, prompt: str) -> Dict:
        """
        Validate response quality and enhance if needed.
        """
        generated_text = result.get('generated_text', '')

        # Quality metrics
        quality_score = self._calculate_response_quality(generated_text, reasoning_chain, prompt)

        # Check for common issues
        issues = self._identify_response_issues(generated_text, reasoning_chain)

        # Enhance response if quality is low or issues are found
        if quality_score < 0.7 or issues:
            enhanced_text = self._enhance_response_quality(generated_text, reasoning_chain, issues)
            result['generated_text'] = enhanced_text
            result['quality_enhanced'] = True
        else:
            result['quality_enhanced'] = False

        # Add quality metadata
        result['response_quality'] = {
            'score': quality_score,
            'issues_found': len(issues),
            'issues': issues,
            'reasoning_aligned': self._check_reasoning_alignment(generated_text, reasoning_chain)
        }

        return result

    def _calculate_response_quality(self, text: str, reasoning_chain, prompt: str) -> float:
        """
        Calculate overall quality score for the generated response.
        """
        score = 0.0
        max_score = 0.0

        # Length appropriateness (1 point)
        max_score += 1
        word_count = len(text.split())
        expected_length = max(50, len(reasoning_chain.conclusion.split()) * 2)
        if expected_length * 0.5 <= word_count <= expected_length * 2:
            score += 1

        # Coherence with reasoning (2 points)
        max_score += 2
        conclusion_words = set(reasoning_chain.conclusion.lower().split())
        response_words = set(text.lower().split())
        overlap = len(conclusion_words.intersection(response_words))
        coherence_ratio = overlap / len(conclusion_words) if conclusion_words else 0
        score += min(coherence_ratio * 2, 2)

        # Completeness (1 point)
        max_score += 1
        if len(text.strip()) > 20 and not text.endswith(('...', 'incomplete', 'tbd')):
            score += 1

        # No repetition (1 point)
        max_score += 1
        # Check for excessive repetition
        words = text.lower().split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio > 0.6:  # Less than 40% repetition
                score += 1

        return score / max_score if max_score > 0 else 0.5

    def _identify_response_issues(self, text: str, reasoning_chain) -> List[str]:
        """
        Identify potential issues in the generated response.
        """
        issues = []

        # Check for incomplete responses
        if text.endswith(('...', 'and', 'or', 'but', 'so', 'then')):
            issues.append('incomplete_sentence')

        # Check for contradiction with reasoning
        conclusion = reasoning_chain.conclusion.lower()
        text_lower = text.lower()

        contradiction_indicators = ['however', 'but', 'although', 'despite', 'contrary']
        if any(indicator in text_lower for indicator in contradiction_indicators):
            if not any(word in conclusion for word in text_lower.split()[:10]):
                issues.append('potential_contradiction')

        # Check for off-topic content
        reasoning_words = set()
        for step in reasoning_chain.steps:
            reasoning_words.update(step.reasoning.lower().split())

        response_words = set(text_lower.split())
        overlap = len(reasoning_words.intersection(response_words))

        if len(reasoning_words) > 5 and overlap / len(reasoning_words) < 0.3:
            issues.append('off_topic')

        # Check for overly verbose responses
        if len(text.split()) > 300 and reasoning_chain.confidence < 0.8:
            issues.append('overly_verbose')

        return issues

    def _enhance_response_quality(self, text: str, reasoning_chain, issues: List[str]) -> str:
        """
        Enhance response quality by addressing identified issues.
        """
        enhanced_text = text

        # Fix incomplete sentences
        if 'incomplete_sentence' in issues and not enhanced_text.endswith('.'):
            # Try to complete based on reasoning conclusion
            conclusion = reasoning_chain.conclusion
            if conclusion and len(conclusion.split()) > 3:
                enhanced_text += f" {conclusion.split('.')[0]}."

        # Address contradictions
        if 'potential_contradiction' in issues:
            enhanced_text = f"Based on the reasoning analysis: {enhanced_text}"

        # Fix off-topic content
        if 'off_topic' in issues:
            # Prepend with conclusion to refocus
            conclusion = reasoning_chain.conclusion
            enhanced_text = f"{conclusion} {enhanced_text}"

        # Trim overly verbose responses
        if 'overly_verbose' in issues:
            words = enhanced_text.split()
            if len(words) > 250:
                # Find a good breaking point
                truncated = ' '.join(words[:200])
                last_period = truncated.rfind('.')
                if last_period > 150:
                    enhanced_text = truncated[:last_period + 1]
                else:
                    enhanced_text = truncated + '.'

        return enhanced_text

    def _check_reasoning_alignment(self, text: str, reasoning_chain) -> bool:
        """
        Check if the generated response aligns with the reasoning chain.
        """
        conclusion = reasoning_chain.conclusion.lower()
        text_lower = text.lower()

        # Check for key conclusion elements in response
        conclusion_words = set(conclusion.split())
        text_words = set(text_lower.split())

        overlap_ratio = len(conclusion_words.intersection(text_words)) / len(conclusion_words) if conclusion_words else 0

        return overlap_ratio > 0.4  # At least 40% overlap with conclusion

    def _solve_with_logical_reasoner(self, text: str) -> Dict:
        """
        Solve logical reasoning queries using the logical reasoner.
        """
        try:
            logical_reasoner = get_logical_reasoner()
            result = logical_reasoner.solve_logical_query(text)

            if result['success']:
                return {
                    'generated_text': result['response'],
                    'version': THOR_VERSION,
                    'task': 'text_generation',
                    'input': text,
                    'logical_reasoning': {
                        'logic_type': result['argument']['logic_type'],
                        'validity': result['argument']['validity'],
                        'soundness': result['argument']['soundness'],
                        'confidence': result['argument']['confidence']
                    }
                }
            else:
                # Fallback to standard generation
                return self._generate_enhanced_text(text, torch.tensor([[0]]), torch.tensor([[1]]))

        except Exception as e:
            print(f"Error in logical reasoning: {e}")
            # Fallback to standard generation
            return self._generate_enhanced_text(text, torch.tensor([[0]]), torch.tensor([[1]]))

    def _solve_with_math_solver(self, text: str) -> Dict:
        """
        Solve mathematical queries using the math solver.
        """
        try:
            math_solver = get_math_solver()
            result = math_solver.solve_mathematical_problem(text)

            if result['success']:
                return {
                    'generated_text': result['response'],
                    'version': THOR_VERSION,
                    'task': 'text_generation',
                    'input': text,
                    'mathematical_reasoning': {
                        'math_type': result['solution']['math_type'],
                        'steps': result['solution']['steps'],
                        'confidence': result['solution']['confidence'],
                        'method': result['solution']['method'],
                        'final_answer': result['solution']['final_answer']
                    }
                }
            else:
                # Fallback to standard generation
                return self._generate_enhanced_text(text, torch.tensor([[0]]), torch.tensor([[1]]))

        except Exception as e:
            print(f"Error in mathematical reasoning: {e}")
            # Fallback to standard generation
            return self._generate_enhanced_text(text, torch.tensor([[0]]), torch.tensor([[1]]))

    def _generate_enhanced_text(
        self,
        text: str,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        generation_params: Optional[Dict] = None
    ) -> Dict:
        """
        Enhanced text generation with multi-step autoregressive generation.
        Uses advanced decoding strategies: nucleus sampling, temperature control, repetition penalty.
        """
        try:
            # Enhanced generation parameters based on query type
            if generation_params is None:
                generation_params = {
                    'max_new_tokens': min(256, self.config['model'].get('max_position_embeddings', 256)),
                    'temperature': 0.8,
                    'top_k': 50,
                    'top_p': 0.95,
                    'repetition_penalty': 1.1,
                    'min_length': 20
                }

            max_new_tokens = generation_params.get('max_new_tokens', 256)
            temperature = generation_params.get('temperature', 0.8)
            top_k = generation_params.get('top_k', 50)
            top_p = generation_params.get('top_p', 0.95)
            repetition_penalty = generation_params.get('repetition_penalty', 1.1)
            min_length = generation_params.get('min_length', 20)
            reasoning_steps = generation_params.get('reasoning_steps', False)
            
            # Start with input tokens
            generated_ids = input_ids[0].clone().cpu().tolist()
            input_length = len(generated_ids)
            seen_tokens = set(generated_ids[-10:])  # Track recent tokens for repetition penalty
            
            # Enhanced prompt engineering: Add context markers and reasoning steps for complex queries
            if reasoning_steps:
                enhanced_prompt = self._enhance_prompt_with_reasoning(text)
            else:
                enhanced_prompt = self._enhance_prompt(text)
            
            # Multi-step generation loop
            for step in range(max_new_tokens):
                # Prepare current sequence
                current_ids = torch.tensor([generated_ids], dtype=torch.long).to(self.device)
                current_mask = torch.ones_like(current_ids).to(self.device)
                
                # Safety: don't exceed model's max position embeddings
                if len(generated_ids) >= self.model.max_position_embeddings:
                    break
                
                # Forward pass
                with torch.no_grad():
                    outputs = self.model(
                        input_ids=current_ids,
                        attention_mask=current_mask,
                        task='text_generation'
                    )
                
                logits = outputs.get('logits')
                if logits is None or len(logits.shape) < 3:
                    break
                
                # Get next token logits (last position)
                next_token_logits = logits[0, -1, :]  # [vocab_size]
                
                # Apply repetition penalty
                for token_id in seen_tokens:
                    if next_token_logits[token_id] > 0:
                        next_token_logits[token_id] /= repetition_penalty
                    else:
                        next_token_logits[token_id] *= repetition_penalty
                
                # Apply temperature
                next_token_logits = next_token_logits / temperature
                
                # Top-k filtering
                if top_k > 0:
                    indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k)[0][..., -1, None]
                    next_token_logits[indices_to_remove] = float('-inf')
                
                # Nucleus (top-p) sampling
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # Remove tokens with cumulative probability above threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    indices_to_remove = sorted_indices[sorted_indices_to_remove]
                    next_token_logits[indices_to_remove] = float('-inf')
                
                # Sample next token
                probs = F.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1).item()
                
                # Add to generated sequence
                generated_ids.append(next_token)
                
                # Update seen tokens (keep last 20 for repetition tracking)
                seen_tokens.add(next_token)
                if len(seen_tokens) > 20:
                    seen_tokens = set(generated_ids[-20:])
                
                # Early stopping conditions
                # Check for end-of-sequence tokens or natural stopping points
                decoded_so_far = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
                
                # Stop if we've generated enough and hit a natural stopping point
                if len(generated_ids) - input_length >= min_length:
                    # Check for natural sentence endings
                    if decoded_so_far.strip().endswith(('.', '!', '?', '\n\n')):
                        # Additional check: if we have a complete thought
                        if len(decoded_so_far.split('.')) >= 2 or len(decoded_so_far.split('!')) >= 2:
                            break
                
                # Safety: prevent infinite loops
                if step > 200:
                    break
            
            # Decode final sequence
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            # Extract only the generated part (remove input)
            if generated_text.startswith(text):
                generated_text = generated_text[len(text):].strip()
            
            # Post-processing: clean up the response
            generated_text = self._post_process_response(generated_text, text)
            
            # Fallback if generation failed
            if not generated_text or len(generated_text.strip()) < 10:
                generated_text = self._generate_fallback_response(text)
            
            return {
                'generated_text': generated_text,
                'version': THOR_VERSION,
                'generation_length': len(generated_ids) - input_length,
                'enhanced': True
            }
            
        except Exception as e:
            print(f"Error in enhanced text generation: {e}")
            import traceback
            traceback.print_exc()
            return {
                'generated_text': self._generate_fallback_response(text),
                'version': THOR_VERSION,
                'error': str(e)
            }

    def _beam_search_decode(
        self,
        text: str,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        generation_params: Dict
    ) -> Dict:
        """
        Beam search decoding for improved generation quality.

        Args:
            text: Original input text
            input_ids: Tokenized input IDs
            attention_mask: Attention mask
            generation_params: Generation parameters including beam_width

        Returns:
            Dictionary with generated text and metadata
        """
        try:
            # Extract parameters
            max_new_tokens = generation_params.get('max_new_tokens', 256)
            beam_width = generation_params.get('beam_width', 4)
            temperature = generation_params.get('temperature', 0.8)
            top_k = generation_params.get('top_k', 50)
            top_p = generation_params.get('top_p', 0.95)
            repetition_penalty = generation_params.get('repetition_penalty', 1.1)
            min_length = generation_params.get('min_length', 20)

            # Initialize beams: each beam is (sequence, score, seen_tokens)
            beams = [(
                input_ids[0].clone().cpu().tolist(),
                0.0,  # log probability score
                set(input_ids[0].clone().cpu().tolist()[-10:])  # seen tokens for repetition
            )]

            input_length = len(beams[0][0])

            for step in range(max_new_tokens):
                if not beams:
                    break

                # Generate candidates from all beams
                candidates = []

                for beam_seq, beam_score, seen_tokens in beams:
                    # Prepare current sequence
                    current_ids = torch.tensor([beam_seq], dtype=torch.long).to(self.device)
                    current_mask = torch.ones_like(current_ids).to(self.device)

                    # Safety: don't exceed model's max position embeddings
                    if len(beam_seq) >= self.model.max_position_embeddings:
                        candidates.append((beam_seq, beam_score, seen_tokens))
                        continue

                    # Forward pass
                    with torch.no_grad():
                        outputs = self.model(
                            input_ids=current_ids,
                            attention_mask=current_mask,
                            task='text_generation'
                        )

                    logits = outputs.get('logits')
                    if logits is None or len(logits.shape) < 3:
                        candidates.append((beam_seq, beam_score, seen_tokens))
                        continue

                    # Get next token logits (last position)
                    next_token_logits = logits[0, -1, :]  # [vocab_size]

                    # Apply repetition penalty
                    for token_id in seen_tokens:
                        if next_token_logits[token_id] > 0:
                            next_token_logits[token_id] /= repetition_penalty
                        else:
                            next_token_logits[token_id] *= repetition_penalty

                    # Apply temperature
                    next_token_logits = next_token_logits / temperature

                    # Top-k filtering
                    if top_k > 0:
                        indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k)[0][..., -1, None]
                        next_token_logits[indices_to_remove] = float('-inf')

                    # Nucleus (top-p) sampling
                    if top_p < 1.0:
                        sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

                        # Remove tokens with cumulative probability above threshold
                        sorted_indices_to_remove = cumulative_probs > top_p
                        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                        sorted_indices_to_remove[..., 0] = 0

                        indices_to_remove = sorted_indices[sorted_indices_to_remove]
                        next_token_logits[indices_to_remove] = float('-inf')

                    # Get probabilities
                    probs = F.softmax(next_token_logits, dim=-1)

                    # Get top beam_width candidates
                    top_probs, top_indices = torch.topk(probs, min(beam_width, len(probs[probs > 0])))

                    for prob, token_id in zip(top_probs.cpu().tolist(), top_indices.cpu().tolist()):
                        if prob > 0:
                            new_seq = beam_seq + [token_id]
                            new_score = beam_score + math.log(prob + 1e-10)  # Add log probability
                            new_seen_tokens = seen_tokens.copy()
                            new_seen_tokens.add(token_id)
                            if len(new_seen_tokens) > 20:
                                # Keep only recent tokens
                                new_seen_tokens = set(new_seq[-20:])

                            candidates.append((new_seq, new_score, new_seen_tokens))

                # Select top beam_width candidates
                candidates.sort(key=lambda x: x[1], reverse=True)  # Sort by score (highest first)
                beams = candidates[:beam_width]

                # Early stopping check
                best_beam = beams[0]
                decoded_so_far = self.tokenizer.decode(best_beam[0], skip_special_tokens=True)

                # Stop if we've generated enough and hit a natural stopping point
                if len(best_beam[0]) - input_length >= min_length:
                    if decoded_so_far.strip().endswith(('.', '!', '?', '\n\n')):
                        if len(decoded_so_far.split('.')) >= 2 or len(decoded_so_far.split('!')) >= 2:
                            break

                # Safety: prevent infinite loops
                if step > 200:
                    break

            # Select best beam
            best_beam = max(beams, key=lambda x: x[1])  # Highest score
            generated_ids = best_beam[0]

            # Decode final sequence
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            # Extract only the generated part (remove input)
            if generated_text.startswith(text):
                generated_text = generated_text[len(text):].strip()

            # Post-processing: clean up the response
            generated_text = self._post_process_response(generated_text, text)

            # Fallback if generation failed
            if not generated_text or len(generated_text.strip()) < 10:
                generated_text = self._generate_fallback_response(text)

            return {
                'generated_text': generated_text,
                'version': THOR_VERSION,
                'generation_length': len(generated_ids) - input_length,
                'enhanced': True,
                'decoding_strategy': 'beam_search',
                'beam_width': beam_width
            }

        except Exception as e:
            print(f"Error in beam search decoding: {e}")
            import traceback
            traceback.print_exc()
            return {
                'generated_text': self._generate_fallback_response(text),
                'version': THOR_VERSION,
                'error': str(e),
                'decoding_strategy': 'beam_search_failed'
            }

    def _contrastive_decode(
        self,
        text: str,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        generation_params: Dict
    ) -> Dict:
        """
        Contrastive decoding for improved factuality and reduced hallucinations.
        Compares outputs with and without context to guide generation.

        Args:
            text: Original input text
            input_ids: Tokenized input IDs
            attention_mask: Attention mask
            generation_params: Generation parameters

        Returns:
            Dictionary with generated text and metadata
        """
        try:
            # Extract parameters
            max_new_tokens = generation_params.get('max_new_tokens', 256)
            temperature = generation_params.get('temperature', 0.8)
            top_k = generation_params.get('top_k', 50)
            top_p = generation_params.get('top_p', 0.95)
            repetition_penalty = generation_params.get('repetition_penalty', 1.1)
            min_length = generation_params.get('min_length', 20)
            contrastive_weight = generation_params.get('contrastive_weight', 0.1)

            # Generate with context (expert model)
            expert_logits = self._get_logits_sequence(input_ids, attention_mask, max_new_tokens)

            # Generate without context (amateur model) - use only BOS token
            bos_token = self.tokenizer.word_to_id.get('<bos>', 2)
            amateur_input_ids = torch.tensor([[bos_token]], dtype=torch.long).to(self.device)
            amateur_attention_mask = torch.ones_like(amateur_input_ids).to(self.device)
            amateur_logits = self._get_logits_sequence(amateur_input_ids, amateur_attention_mask, max_new_tokens)

            # Generate sequence using contrastive decoding
            generated_ids = input_ids[0].clone().cpu().tolist()
            input_length = len(generated_ids)
            seen_tokens = set(generated_ids[-10:])

            for step in range(max_new_tokens):
                current_ids = torch.tensor([generated_ids], dtype=torch.long).to(self.device)
                current_mask = torch.ones_like(current_ids).to(self.device)

                # Safety: don't exceed model's max position embeddings
                if len(generated_ids) >= self.model.max_position_embeddings:
                    break

                # Get current logits
                with torch.no_grad():
                    outputs = self.model(
                        input_ids=current_ids,
                        attention_mask=current_mask,
                        task='text_generation'
                    )

                logits = outputs.get('logits')
                if logits is None or len(logits.shape) < 3:
                    break

                next_token_logits = logits[0, -1, :]  # [vocab_size]

                # Get corresponding amateur logits (same position)
                if step < len(amateur_logits):
                    amateur_next_logits = amateur_logits[step]
                else:
                    # Fallback: use generic amateur logits
                    amateur_next_logits = amateur_logits[-1] if amateur_logits else next_token_logits

                # Apply contrastive decoding: expert - weight * amateur
                contrastive_logits = next_token_logits - contrastive_weight * amateur_next_logits

                # Apply repetition penalty
                for token_id in seen_tokens:
                    if contrastive_logits[token_id] > 0:
                        contrastive_logits[token_id] /= repetition_penalty
                    else:
                        contrastive_logits[token_id] *= repetition_penalty

                # Apply temperature
                contrastive_logits = contrastive_logits / temperature

                # Top-k filtering
                if top_k > 0:
                    indices_to_remove = contrastive_logits < torch.topk(contrastive_logits, top_k)[0][..., -1, None]
                    contrastive_logits[indices_to_remove] = float('-inf')

                # Nucleus (top-p) sampling
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(contrastive_logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

                    # Remove tokens with cumulative probability above threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0

                    indices_to_remove = sorted_indices[sorted_indices_to_remove]
                    contrastive_logits[indices_to_remove] = float('-inf')

                # Sample next token
                probs = F.softmax(contrastive_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1).item()

                # Add to generated sequence
                generated_ids.append(next_token)

                # Update seen tokens
                seen_tokens.add(next_token)
                if len(seen_tokens) > 20:
                    seen_tokens = set(generated_ids[-20:])

                # Early stopping conditions
                decoded_so_far = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

                if len(generated_ids) - input_length >= min_length:
                    if decoded_so_far.strip().endswith(('.', '!', '?', '\n\n')):
                        if len(decoded_so_far.split('.')) >= 2 or len(decoded_so_far.split('!')) >= 2:
                            break

                if step > 200:
                    break

            # Decode final sequence
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            # Extract only the generated part (remove input)
            if generated_text.startswith(text):
                generated_text = generated_text[len(text):].strip()

            # Post-processing: clean up the response
            generated_text = self._post_process_response(generated_text, text)

            # Fallback if generation failed
            if not generated_text or len(generated_text.strip()) < 10:
                generated_text = self._generate_fallback_response(text)

            return {
                'generated_text': generated_text,
                'version': THOR_VERSION,
                'generation_length': len(generated_ids) - input_length,
                'enhanced': True,
                'decoding_strategy': 'contrastive',
                'contrastive_weight': contrastive_weight
            }

        except Exception as e:
            print(f"Error in contrastive decoding: {e}")
            import traceback
            traceback.print_exc()
            return {
                'generated_text': self._generate_fallback_response(text),
                'version': THOR_VERSION,
                'error': str(e),
                'decoding_strategy': 'contrastive_failed'
            }

    def _compress_context(self, text: str, max_length: int = 1024, preserve_recent: bool = True) -> str:
        """
        Compress long context by summarizing or truncating intelligently.

        Args:
            text: Input text to compress
            max_length: Maximum length to preserve
            preserve_recent: Whether to preserve more recent content

        Returns:
            Compressed text
        """
        if len(text) <= max_length:
            return text

        words = text.split()
        if len(words) <= max_length // 6:  # Rough word count check
            return text

        # Simple compression: keep beginning, middle summary, and end
        if preserve_recent:
            # Keep more from the end (recent context)
            keep_start = max_length // 4
            keep_end = max_length * 3 // 4
            middle_remove = len(text) - keep_start - keep_end

            if middle_remove > 0:
                compressed = text[:keep_start] + f"\n[... {middle_remove} characters summarized ...]\n" + text[-keep_end:]
                return compressed

        # Alternative: truncate with summary markers
        truncated = text[:max_length-50] + "\n[Content truncated for length]"
        return truncated

    def _apply_sliding_window(self, input_ids: List[int], window_size: int = 512, stride: int = 256) -> List[int]:
        """
        Apply sliding window to handle long sequences.
        Keeps the most recent context within the window size.

        Args:
            input_ids: Token IDs
            window_size: Size of the sliding window
            stride: How much to slide the window

        Returns:
            Windowed token IDs
        """
        if len(input_ids) <= window_size:
            return input_ids

        # Keep the most recent window
        return input_ids[-window_size:]

    def _prepare_long_context(
        self,
        text: str,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        max_position_embeddings: int
    ) -> Tuple[torch.Tensor, torch.Tensor, str]:
        """
        Prepare long context for model input using compression and sliding window.

        Args:
            text: Original text
            input_ids: Token IDs tensor
            attention_mask: Attention mask tensor
            max_position_embeddings: Model's max position embeddings

        Returns:
            Tuple of (processed_input_ids, processed_attention_mask, processed_text)
        """
        seq_len = input_ids.size(1)

        # If within limits, return as-is
        if seq_len <= max_position_embeddings:
            return input_ids, attention_mask, text

        # Try compression first
        compressed_text = self._compress_context(text, max_length=max_position_embeddings*4)  # Allow some buffer
        compressed_input_ids = self.tokenizer.encode(compressed_text, max_length=max_position_embeddings)

        if len(compressed_input_ids) <= max_position_embeddings:
            # Compression worked
            compressed_attention_mask = [1 if tid != 0 else 0 for tid in compressed_input_ids]
            while len(compressed_input_ids) < max_position_embeddings:
                compressed_input_ids.append(0)  # Pad
                compressed_attention_mask.append(0)

            return (
                torch.tensor([compressed_input_ids], dtype=torch.long).to(self.device),
                torch.tensor([compressed_attention_mask], dtype=torch.long).to(self.device),
                compressed_text
            )

        # Fallback to sliding window
        windowed_ids = self._apply_sliding_window(input_ids[0].tolist(), window_size=max_position_embeddings-50)
        windowed_attention_mask = [1] * len(windowed_ids)

        # Pad to max length
        while len(windowed_ids) < max_position_embeddings:
            windowed_ids.append(0)
            windowed_attention_mask.append(0)

        # Decode windowed text for reference
        windowed_text = self.tokenizer.decode(windowed_ids, skip_special_tokens=True)

        return (
            torch.tensor([windowed_ids], dtype=torch.long).to(self.device),
            torch.tensor([windowed_attention_mask], dtype=torch.long).to(self.device),
            windowed_text
        )

    def _get_logits_sequence(self, input_ids: torch.Tensor, attention_mask: torch.Tensor, max_steps: int) -> List[torch.Tensor]:
        """
        Get sequence of logits for contrastive decoding.
        Used to generate both expert and amateur logits.

        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask
            max_steps: Maximum number of steps to generate

        Returns:
            List of logit tensors for each step
        """
        logits_sequence = []
        current_ids = input_ids.clone()
        current_mask = attention_mask.clone()

        for step in range(max_steps):
            # Safety check
            if len(current_ids[0]) >= self.model.max_position_embeddings:
                break

            with torch.no_grad():
                outputs = self.model(
                    input_ids=current_ids,
                    attention_mask=current_mask,
                    task='text_generation'
                )

            logits = outputs.get('logits')
            if logits is None or len(logits.shape) < 3:
                break

            # Store logits for current position
            next_token_logits = logits[0, -1, :]  # [vocab_size]
            logits_sequence.append(next_token_logits.clone())

            # Sample next token (greedy for consistency)
            next_token = torch.argmax(next_token_logits, dim=-1).item()

            # Add to sequence
            next_token_tensor = torch.tensor([[next_token]], dtype=torch.long).to(self.device)
            current_ids = torch.cat([current_ids, next_token_tensor], dim=1)
            current_mask = torch.cat([current_mask, torch.ones_like(next_token_tensor)], dim=1)

        return logits_sequence
    
    def _enhance_prompt(self, text: str) -> str:
        """
        Enhance the prompt with better context understanding.
        Adds implicit instructions for better response quality.
        """
        # Detect query type and add appropriate context
        text_lower = text.lower().strip()
        
        # Question detection
        if any(text_lower.startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which']):
            enhanced = f"Answer this question clearly and comprehensively: {text}"
        # Explanation request
        elif any(word in text_lower for word in ['explain', 'describe', 'tell me about', 'what is']):
            enhanced = f"Provide a clear and detailed explanation: {text}"
        # Code request
        elif any(word in text_lower for word in ['code', 'program', 'function', 'script', 'algorithm']):
            enhanced = f"Provide code or programming help: {text}"
        # Creative request
        elif any(word in text_lower for word in ['write', 'create', 'generate', 'make', 'design']):
            enhanced = f"Create or generate content: {text}"
        else:
            # Default: conversational response
            enhanced = f"Respond naturally and helpfully: {text}"
        
        return enhanced
    
    def _post_process_response(self, generated_text: str, original_query: str) -> str:
        """
        Post-process generated text to improve quality.
        - Remove incomplete sentences
        - Fix common issues
        - Ensure coherence
        """
        if not generated_text:
            return generated_text
        
        # Remove leading/trailing whitespace
        generated_text = generated_text.strip()
        
        # Remove incomplete sentences at the end (if they're too short)
        sentences = generated_text.split('.')
        if len(sentences) > 1:
            # Check if last sentence is too short (likely incomplete)
            last_sentence = sentences[-1].strip()
            if len(last_sentence) < 10 and not last_sentence.endswith(('!', '?')):
                # Remove incomplete last sentence
                generated_text = '.'.join(sentences[:-1])
                if generated_text and not generated_text.endswith('.'):
                    generated_text += '.'
        
        # Remove excessive whitespace
        import re
        generated_text = re.sub(r'\s+', ' ', generated_text)
        generated_text = re.sub(r'\n\s*\n', '\n\n', generated_text)
        
        # Ensure it starts with a capital letter
        if generated_text and generated_text[0].islower():
            generated_text = generated_text[0].upper() + generated_text[1:]
        
        # Remove common artifacts
        artifacts = [
            'Response pattern for',
            'Use appropriate',
            'This is a',
            'I understand your message',
        ]
        for artifact in artifacts:
            if generated_text.startswith(artifact) and len(generated_text) < 50:
                # Likely an artifact, try to extract meaningful content
                pass
        
        return generated_text.strip()
    
    def _generate_fallback_response(self, text: str) -> str:
        """
        Generate a helpful fallback response when generation fails.
        """
        text_lower = text.lower().strip()
        
        # Context-aware fallbacks
        if any(text_lower.startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who']):
            return f"I understand you're asking about '{text}'. Let me provide you with a helpful answer based on my knowledge."
        elif 'explain' in text_lower:
            return f"I'd be happy to explain '{text}'. Here's what I know about this topic."
        elif any(word in text_lower for word in ['code', 'program', 'function']):
            return f"I can help you with '{text}'. Let me provide you with code examples and explanations."
        else:
            return f"I understand your message: '{text}'. How can I assist you with this?"

    def _detect_query_type(self, text: str) -> str:
        """Detect the type of query to optimize generation parameters."""
        text_lower = text.lower().strip()

        # Complex reasoning queries
        complex_indicators = [
            'why', 'how does', 'what causes', 'explain why', 'analyze',
            'compare', 'versus', 'vs', 'difference between', 'relationship',
            'process', 'mechanism', 'theory', 'concept'
        ]
        if any(indicator in text_lower for indicator in complex_indicators):
            return 'complex_reasoning'

        # Technical/programming queries
        tech_indicators = [
            'code', 'program', 'function', 'algorithm', 'implement',
            'debug', 'error', 'fix', 'api', 'database', 'server'
        ]
        if any(indicator in text_lower for indicator in tech_indicators):
            return 'technical'

        # Creative/writing queries
        creative_indicators = [
            'write', 'create', 'design', 'story', 'poem', 'essay',
            'describe', 'imagine', 'generate'
        ]
        if any(indicator in text_lower for indicator in creative_indicators):
            return 'creative'

        # Factual queries
        factual_indicators = [
            'what is', 'who is', 'when did', 'where is', 'how many',
            'list', 'facts about', 'information on'
        ]
        if any(indicator in text_lower for indicator in factual_indicators):
            return 'factual'

        # Conversational queries
        if len(text.split()) < 10 and not any(text_lower.startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who']):
            return 'conversational'

        return 'general'

    def _get_generation_params_for_query_type(self, query_type: str, max_tokens: int) -> Dict:
        """Get optimized generation parameters based on query type."""
        base_params = {
            'max_new_tokens': max_tokens,
            'repetition_penalty': 1.1,
            'min_length': 20
        }

        if query_type == 'complex_reasoning':
            # More focused, longer responses with reasoning steps - use beam search for better quality
            return {
                **base_params,
                'temperature': 0.7,  # Lower temperature for more focused reasoning
                'top_k': 40,
                'top_p': 0.9,
                'max_new_tokens': min(max_tokens * 1.5, 512),  # Allow longer responses
                'reasoning_steps': True,
                'decoding_strategy': 'beam_search',  # Use beam search for complex reasoning
                'beam_width': 4  # Moderate beam width for quality vs speed balance
            }

        elif query_type == 'technical':
            # Precise, code-friendly responses
            return {
                **base_params,
                'temperature': 0.6,  # Very focused for technical accuracy
                'top_k': 30,
                'top_p': 0.85,
                'max_new_tokens': max_tokens
            }

        elif query_type == 'creative':
            # More creative and varied responses
            return {
                **base_params,
                'temperature': 0.9,  # Higher temperature for creativity
                'top_k': 60,
                'top_p': 0.95,
                'max_new_tokens': min(max_tokens * 1.2, 400)
            }

        elif query_type == 'factual':
            # Balanced, informative responses
            return {
                **base_params,
                'temperature': 0.7,
                'top_k': 45,
                'top_p': 0.92,
                'max_new_tokens': max_tokens
            }

        elif query_type == 'conversational':
            # Shorter, more natural responses
            return {
                **base_params,
                'temperature': 0.8,
                'top_k': 50,
                'top_p': 0.95,
                'max_new_tokens': min(max_tokens * 0.8, 150),
                'min_length': 10
            }

        else:  # general
            return {
                **base_params,
                'temperature': 0.8,
                'top_k': 50,
                'top_p': 0.95,
                'max_new_tokens': max_tokens
            }

    def _enhance_prompt_with_reasoning(self, text: str) -> str:
        """
        Enhance prompt with systematic chain-of-thought reasoning instructions.
        Uses domain-specific CoT templates for better reasoning quality.
        """
        text_lower = text.lower()

        # Causal/Analytical reasoning (why questions)
        if any(phrase in text_lower for phrase in ['why', 'explain why', 'analyze why', 'what causes', 'reason for']):
            enhanced = f"""Analyze this question systematically using chain-of-thought reasoning:

Question: {text}

Chain-of-Thought Analysis:
1. Identify the core phenomenon or event being asked about
2. Examine the underlying mechanisms or factors at play
3. Consider historical or contextual background
4. Evaluate evidence and logical connections
5. Draw well-supported conclusions

Let me break this down step by step:"""

        # Process/Mechanism reasoning (how questions)
        elif any(phrase in text_lower for phrase in ['how does', 'how do', 'process', 'mechanism', 'steps to', 'procedure']):
            enhanced = f"""Explain this process using systematic step-by-step reasoning:

Question: {text}

Process Analysis Framework:
1. Identify the initial conditions or starting point
2. Break down the process into sequential stages
3. Explain the mechanisms or transformations at each step
4. Describe the intermediate states and transitions
5. Identify the final outcome or result

Step-by-step breakdown:"""

        # Comparative reasoning (comparisons, differences)
        elif any(phrase in text_lower for phrase in ['compare', 'versus', 'vs', 'difference', 'similarities', 'better than', 'advantages']):
            enhanced = f"""Conduct a systematic comparison using structured analytical reasoning:

Question: {text}

Comparative Analysis Framework:
1. Identify the entities or concepts being compared
2. Establish clear criteria for comparison
3. Examine similarities and commonalities
4. Analyze differences and distinctions
5. Consider context-dependent advantages and trade-offs
6. Provide balanced assessment with evidence

Structured comparison:"""

        # Conceptual/Theoretical reasoning
        elif any(phrase in text_lower for phrase in ['theory', 'concept', 'principle', 'understanding', 'foundation', 'basis']):
            enhanced = f"""Develop a deep conceptual understanding using theoretical reasoning:

Question: {text}

Conceptual Analysis Framework:
1. Define key terms and establish foundational concepts
2. Explore the theoretical underpinnings and principles
3. Examine relationships between concepts
4. Consider implications and applications
5. Address potential limitations or boundaries

Theoretical explanation:"""

        # Mathematical/Logical reasoning
        elif any(phrase in text_lower for phrase in ['calculate', 'compute', 'solve', 'prove', 'logic', 'mathematical', 'equation']):
            enhanced = f"""Apply systematic mathematical and logical reasoning:

Question: {text}

Mathematical Reasoning Framework:
1. Identify the problem type and required approach
2. Break down into solvable components
3. Apply appropriate mathematical principles or formulas
4. Show step-by-step calculations with clear explanations
5. Verify results and consider edge cases

Step-by-step solution:"""

        # Ethical/Moral reasoning
        elif any(phrase in text_lower for phrase in ['ethical', 'moral', 'right', 'wrong', 'should', 'ought', 'justice', 'fair']):
            enhanced = f"""Apply ethical reasoning using structured moral analysis:

Question: {text}

Ethical Reasoning Framework:
1. Identify stakeholders and their interests
2. Consider relevant ethical principles and values
3. Examine potential consequences and impacts
4. Evaluate alternative perspectives and viewpoints
5. Balance competing ethical considerations
6. Provide well-reasoned ethical judgment

Ethical analysis:"""

        # Scientific reasoning
        elif any(phrase in text_lower for phrase in ['scientific', 'experiment', 'hypothesis', 'evidence', 'research', 'study']):
            enhanced = f"""Apply scientific reasoning using empirical and evidence-based analysis:

Question: {text}

Scientific Reasoning Framework:
1. Formulate clear research questions or hypotheses
2. Review existing evidence and prior research
3. Design appropriate methods for investigation
4. Analyze data and interpret results
5. Draw evidence-based conclusions
6. Consider limitations and future research directions

Scientific analysis:"""

        # Default comprehensive reasoning
        else:
            enhanced = f"""Provide a comprehensive, well-reasoned response using systematic analysis:

Question: {text}

Comprehensive Analysis Framework:
1. Understand the core question and context
2. Break down complex elements into manageable parts
3. Apply relevant knowledge and principles
4. Consider multiple perspectives and implications
5. Provide evidence-based reasoning
6. Draw clear, well-supported conclusions

Detailed analysis:"""

        return enhanced

    def _generate_with_reasoning(
        self,
        text: str,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        generation_params: Optional[Dict] = None,
        context: str = "",
        knowledge: List[Dict] = None
    ) -> Dict:
        """
        Generate text using chain-of-thought reasoning for complex queries.
        Integrates reasoning engine with enhanced knowledge retrieval and text generation.
        Enhanced with multi-topic knowledge retrieval for cross-domain reasoning.
        """
        try:
            from brain import BrainConnector
            from .multi_topic_retriever import get_multi_topic_retriever
            from .knowledge_synthesizer import get_knowledge_synthesizer
            from .causal_reasoner import get_causal_reasoner

            reasoning_engine = get_reasoning_engine()
            brain_connector = BrainConnector()
            
            # Check if this is a multi-topic query
            query_analyzer = get_query_intent_analyzer()
            query_analysis = query_analyzer.analyze(text)
            is_multi_topic = self._is_multi_topic_query(text, query_analysis)
            
            # Initialize variables
            enhanced_knowledge = {}
            multi_topic_data = {}
            
            # Use causal reasoner for causal multi-topic queries
            if is_multi_topic and query_analysis.get('reasoning_type') == 'causal':
                try:
                    causal_reasoner = get_causal_reasoner()
                    reasoning_chain = causal_reasoner.solve_causal_query(text, context)
                except Exception as e:
                    print(f"[Inference] Causal reasoner error, falling back: {e}")
                    is_multi_topic = False  # Fall back to standard reasoning
            
            if is_multi_topic:
                # Multi-topic retrieval and reasoning
                multi_topic_retriever = get_multi_topic_retriever()
                knowledge_synthesizer = get_knowledge_synthesizer()
                
                # Get multi-topic knowledge
                multi_topic_data = multi_topic_retriever.get_enhanced_multi_topic_knowledge(
                    text,
                    max_topics=5,
                    max_knowledge_per_topic=5
                )
                
                knowledge_by_topic = multi_topic_data.get('knowledge_by_topic', {})
                
                # Synthesize knowledge
                synthesis_result = knowledge_synthesizer.synthesize_knowledge(
                    knowledge_by_topic,
                    text,
                    context
                )
                
                # Generate reasoning chain with multi-topic knowledge
                reasoning_chain = reasoning_engine.generate_reasoning_chain(
                    text,
                    context,
                    knowledge=None,
                    multi_topic_knowledge=knowledge_by_topic,
                    use_iterative_retrieval=True
                )
                
                injection_context = synthesis_result.get('synthesized_context', '')
                knowledge_items = []
                for items in knowledge_by_topic.values():
                    knowledge_items.extend(items)
            else:
                # Standard single-topic retrieval
                enhanced_knowledge = brain_connector.get_enhanced_knowledge(
                    text, context, max_results=5, include_citations=True
                )

                # Use the enhanced knowledge for reasoning
                knowledge_items = enhanced_knowledge.get('knowledge_items', [])
                injection_context = enhanced_knowledge.get('injection_context', '')

                # Generate reasoning chain with enhanced knowledge
                reasoning_chain = reasoning_engine.generate_reasoning_chain(
                    text, context, knowledge_items,
                    multi_topic_knowledge=None,
                    use_iterative_retrieval=False
                )

            # Format reasoning output
            reasoning_output = reasoning_engine.format_reasoning_output(reasoning_chain)

            # If reasoning chain is valid and confidence is high, use it as the basis for generation
            if reasoning_chain.verification_result and reasoning_chain.confidence > 0.7:
                # Combine reasoning context with knowledge injection
                full_context = reasoning_output
                if injection_context:
                    full_context += "\n\n" + injection_context

                # Enhance the prompt with combined reasoning and knowledge context
                enhanced_prompt = self._enhance_prompt_with_reasoning_context(text, full_context)

                # Apply adaptive generation parameters based on reasoning complexity
                adapted_params = self._adapt_generation_params_for_reasoning(generation_params, reasoning_chain)

                # Update input_ids and attention_mask with enhanced prompt
                enhanced_input_ids = self.tokenizer.encode(enhanced_prompt, max_length=input_ids.shape[1])
                enhanced_attention_mask = [1 if tid != 0 else 0 for tid in enhanced_input_ids]

                # Pad/truncate to match original length
                max_len = input_ids.shape[1]
                if len(enhanced_input_ids) > max_len:
                    enhanced_input_ids = enhanced_input_ids[:max_len]
                    enhanced_attention_mask = enhanced_attention_mask[:max_len]
                else:
                    # Pad with zeros
                    padding_length = max_len - len(enhanced_input_ids)
                    enhanced_input_ids.extend([0] * padding_length)
                    enhanced_attention_mask.extend([0] * padding_length)

                # Convert to tensors
                enhanced_input_ids = torch.tensor([enhanced_input_ids], dtype=torch.long).to(self.device)
                enhanced_attention_mask = torch.tensor([enhanced_attention_mask], dtype=torch.long).to(self.device)

                # Generate final response using enhanced prompt and adapted parameters
                result = self._generate_enhanced_text(enhanced_prompt, enhanced_input_ids,
                                                    enhanced_attention_mask, adapted_params)

                # Apply quality validation and enhancement
                result = self._validate_and_enhance_response_quality(result, reasoning_chain, enhanced_prompt)

                # Add reasoning and knowledge metadata to result
                result['reasoning_chain'] = {
                    'steps': len(reasoning_chain.steps),
                    'confidence': reasoning_chain.confidence,
                    'quality_score': reasoning_chain.reasoning_quality_score,
                    'reasoning_type': reasoning_chain.reasoning_type.value,
                    'verification_passed': reasoning_chain.verification_result
                }

                # Prepare knowledge integration metadata
                knowledge_metadata = {
                    'knowledge_items_used': len(knowledge_items),
                    'semantic_ranking_applied': True,
                    'multi_topic': is_multi_topic
                }
                
                if is_multi_topic:
                    knowledge_metadata['total_candidates'] = len(knowledge_items)
                    knowledge_metadata['citations'] = []
                    knowledge_metadata['topics_covered'] = [t['topic'] for t in multi_topic_data.get('topics', [])]
                    knowledge_metadata['domains'] = multi_topic_data.get('domains', [])
                else:
                    knowledge_metadata['total_candidates'] = enhanced_knowledge.get('total_candidates', 0)
                    knowledge_metadata['citations'] = enhanced_knowledge.get('citations', [])
                
                result['knowledge_integration'] = knowledge_metadata

                return result
            else:
                # Fallback: Use enhanced knowledge injection without reasoning
                print(f"Reasoning confidence too low ({reasoning_chain.confidence:.2f}), using knowledge-enhanced generation")

                if injection_context:
                    # Inject knowledge directly into generation
                    enhanced_prompt = brain_connector.inject_knowledge_into_prompt(text, injection_context)

                    # Tokenize and generate
                    enhanced_input_ids = self.tokenizer.encode(enhanced_prompt, max_length=input_ids.shape[1])
                    enhanced_attention_mask = [1 if tid != 0 else 0 for tid in enhanced_input_ids]

                    # Pad/truncate
                    max_len = input_ids.shape[1]
                    if len(enhanced_input_ids) > max_len:
                        enhanced_input_ids = enhanced_input_ids[:max_len]
                        enhanced_attention_mask = enhanced_attention_mask[:max_len]
                    else:
                        padding_length = max_len - len(enhanced_input_ids)
                        enhanced_input_ids.extend([0] * padding_length)
                        enhanced_attention_mask.extend([0] * padding_length)

                    enhanced_input_ids = torch.tensor([enhanced_input_ids], dtype=torch.long).to(self.device)
                    enhanced_attention_mask = torch.tensor([enhanced_attention_mask], dtype=torch.long).to(self.device)

                    result = self._generate_enhanced_text(enhanced_prompt, enhanced_input_ids,
                                                        enhanced_attention_mask, generation_params)

                    result['knowledge_integration'] = {
                        'knowledge_items_used': len(knowledge_items),
                        'reasoning_fallback': True,
                        'citations': enhanced_knowledge.get('citations', [])
                    }

                    return result
                else:
                    # Final fallback to regular generation
                    return self._generate_enhanced_text(text, input_ids, attention_mask, generation_params)

        except Exception as e:
            print(f"Error in reasoning-based generation: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to regular generation
            return self._generate_enhanced_text(text, input_ids, attention_mask, generation_params)

    def _enhance_prompt_with_reasoning_context(self, original_query: str, reasoning_output: str) -> str:
        """
        Enhance the prompt by incorporating reasoning context.
        """
        return f"""Based on the following chain-of-thought reasoning analysis, provide a comprehensive and accurate response to: {original_query}

Reasoning Analysis:
{reasoning_output}

Now, provide your final response incorporating these insights:"""


def main():
    parser = argparse.ArgumentParser(description='Run inference with All-Rounder AI Model')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to model checkpoint')
    parser.add_argument('--tokenizer', type=str, required=True,
                       help='Path to tokenizer file')
    parser.add_argument('--text', type=str, required=True,
                       help='Input text')
    parser.add_argument('--task', type=str, required=True,
                       choices=['text_classification', 'text_generation', 'question_answering',
                               'sentiment_analysis', 'named_entity_recognition'],
                       help='Task to perform')
    parser.add_argument('--config', type=str, default='config/config/config.yaml',
                       help='Path to config file')
    
    args = parser.parse_args()
    
    # Initialize inference
    inference = AllRounderInference(args.model, args.tokenizer, args.config)
    
    # Make prediction
    result = inference.predict(args.text, args.task)
    
    # Print results
    print("\n" + "="*50)
    print(f"Task: {result['task']}")
    print(f"Input: {result['input']}")
    print("-"*50)
    
    if 'prediction' in result:
        print(f"Prediction: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.4f}")
    elif 'answer' in result:
        print(f"Answer: {result['answer']}")
    elif 'generated_text' in result:
        print(f"Generated: {result['generated_text']}")
    elif 'predictions' in result:
        print(f"NER Predictions: {result['predictions']}")
    
    print("="*50)


if __name__ == '__main__':
    main()

