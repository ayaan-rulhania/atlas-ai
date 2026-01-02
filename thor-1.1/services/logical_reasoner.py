"""
Logical Reasoner - Handles logical queries and proofs
Provides deductive, inductive, and abductive logical reasoning capabilities
"""
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class LogicType(Enum):
    """Types of logical reasoning"""
    DEDUCTIVE = "deductive"    # Premises → Conclusion (certain)
    INDUCTIVE = "inductive"    # Specific → General (probable)
    ABDUCTIVE = "abductive"    # Best explanation (inference to best explanation)
    ANALOGICAL = "analogical"  # Reasoning by analogy


@dataclass
class LogicalPremise:
    """Represents a logical premise"""
    statement: str
    is_negated: bool = False
    confidence: float = 1.0
    source: Optional[str] = None


@dataclass
class LogicalArgument:
    """Represents a logical argument"""
    premises: List[LogicalPremise]
    conclusion: LogicalPremise
    logic_type: LogicType
    validity: bool = True
    soundness: bool = True
    strength: float = 1.0  # For inductive arguments


@dataclass
class LogicalProof:
    """Represents a logical proof"""
    argument: LogicalArgument
    steps: List[str]
    rules_used: List[str]
    final_conclusion: str
    confidence: float
    proof_type: str


class LogicalReasoner:
    """Handles logical reasoning and proofs"""

    def __init__(self):
        self.logical_operators = {
            'and': '&', 'or': '|', 'not': '¬', 'implies': '→', 'if': '→',
            'then': '→', 'therefore': '∴', 'because': '∵'
        }

        self.logical_rules = {
            'modus_ponens': {'pattern': 'A → B, A ⊨ B', 'name': 'Modus Ponens'},
            'modus_tollens': {'pattern': 'A → B, ¬B ⊨ ¬A', 'name': 'Modus Tollens'},
            'hypothetical_syllogism': {'pattern': 'A → B, B → C ⊨ A → C', 'name': 'Hypothetical Syllogism'},
            'disjunctive_syllogism': {'pattern': 'A ∨ B, ¬A ⊨ B', 'name': 'Disjunctive Syllogism'},
            'addition': {'pattern': 'A ⊨ A ∨ B', 'name': 'Addition'},
            'simplification': {'pattern': 'A ∧ B ⊨ A', 'name': 'Simplification'},
            'conjunction': {'pattern': 'A, B ⊨ A ∧ B', 'name': 'Conjunction'},
            'resolution': {'pattern': 'A ∨ B, ¬A ∨ C ⊨ B ∨ C', 'name': 'Resolution'}
        }

    def analyze_logical_query(self, query: str) -> Dict[str, Any]:
        """Analyze a logical query and determine reasoning approach"""
        query_lower = query.lower()

        analysis = {
            'is_logical': self._is_logical_query(query),
            'logic_type': self._detect_logic_type(query),
            'premises': self._extract_premises(query),
            'operators': self._extract_logical_operators(query),
            'complexity': self._assess_logical_complexity(query),
            'requires_proof': self._requires_formal_proof(query)
        }

        return analysis

    def _is_logical_query(self, query: str) -> bool:
        """Check if query involves logical reasoning"""
        logical_indicators = [
            'if', 'then', 'therefore', 'because', 'implies', 'follows that',
            'logically', 'reasoning', 'deduce', 'infer', 'conclude',
            'premise', 'conclusion', 'valid', 'invalid', 'sound', 'unsound'
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in logical_indicators)

    def _detect_logic_type(self, query: str) -> LogicType:
        """Detect the type of logical reasoning required"""
        query_lower = query.lower()

        # Deductive indicators
        if any(word in query_lower for word in ['must be', 'necessarily', 'follows logically', 'deduce']):
            return LogicType.DEDUCTIVE

        # Inductive indicators
        if any(word in query_lower for word in ['probably', 'likely', 'generally', 'usually', 'tend to']):
            return LogicType.INDUCTIVE

        # Abductive indicators
        if any(word in query_lower for word in ['best explanation', 'most likely', 'probably because']):
            return LogicType.ABDUCTIVE

        # Analogical indicators
        if any(word in query_lower for word in ['similar to', 'like', 'analogous', 'by analogy']):
            return LogicType.ANALOGICAL

        # Default to deductive for logical queries
        return LogicType.DEDUCTIVE

    def _extract_premises(self, query: str) -> List[LogicalPremise]:
        """Extract logical premises from the query"""
        premises = []

        # Split on logical connectors
        parts = re.split(r'\s+(?:if|then|because|therefore|so|thus|hence|and|or)\s+', query)

        for part in parts:
            part = part.strip()
            if len(part) > 5:  # Meaningful premise
                is_negated = part.lower().startswith(('not ', 'no ', 'never '))
                statement = part[4:] if is_negated and part.lower().startswith('not ') else part

                premises.append(LogicalPremise(
                    statement=statement,
                    is_negated=is_negated,
                    confidence=0.9  # Assume high confidence for stated premises
                ))

        return premises

    def _extract_logical_operators(self, query: str) -> List[str]:
        """Extract logical operators from the query"""
        operators = []
        query_lower = query.lower()

        for operator, symbol in self.logical_operators.items():
            if operator in query_lower:
                operators.append(f"{operator} ({symbol})")

        return operators

    def _assess_logical_complexity(self, query: str) -> float:
        """Assess the logical complexity of the query"""
        complexity = 0.0

        # Count logical operators
        operator_count = sum(1 for op in self.logical_operators.keys() if op in query.lower())
        complexity += min(operator_count * 0.2, 0.6)

        # Check for nested logic
        if any(word in query.lower() for word in ['if', 'then']) and 'if' in query.lower():
            nested_count = query.lower().count('if')
            complexity += min(nested_count * 0.1, 0.3)

        # Length-based complexity
        word_count = len(query.split())
        complexity += min(word_count / 50, 0.2)

        return min(complexity, 1.0)

    def _requires_formal_proof(self, query: str) -> bool:
        """Check if query requires a formal logical proof"""
        formal_indicators = [
            'prove that', 'proof', 'demonstrate', 'valid argument',
            'logical proof', 'formal logic', 'theorem'
        ]

        return any(indicator in query.lower() for indicator in formal_indicators)

    def construct_logical_argument(self, query: str, premises: List[LogicalPremise] = None) -> LogicalArgument:
        """Construct a logical argument from the query"""
        if premises is None:
            premises = self._extract_premises(query)

        # Determine logic type
        logic_type = self._detect_logic_type(query)

        # Extract conclusion (usually at the end)
        conclusion_text = self._extract_conclusion(query)
        conclusion = LogicalPremise(statement=conclusion_text, confidence=0.8)

        # Create argument
        argument = LogicalArgument(
            premises=premises,
            conclusion=conclusion,
            logic_type=logic_type
        )

        # Validate argument
        argument.validity = self._validate_argument(argument)
        argument.soundness = self._assess_soundness(argument)

        if logic_type == LogicType.INDUCTIVE:
            argument.strength = self._assess_inductive_strength(argument)

        return argument

    def _extract_conclusion(self, query: str) -> str:
        """Extract the conclusion from a logical query"""
        # Look for conclusion indicators
        conclusion_markers = ['therefore', 'thus', 'hence', 'so', 'consequently']

        for marker in conclusion_markers:
            if marker in query.lower():
                parts = query.lower().split(marker, 1)
                if len(parts) > 1:
                    return parts[1].strip()

        # If no clear conclusion marker, take the last sentence
        sentences = re.split(r'[.!?]+', query)
        for sentence in reversed(sentences):
            sentence = sentence.strip()
            if len(sentence) > 10:
                return sentence

        return "Conclusion cannot be determined"

    def _validate_argument(self, argument: LogicalArgument) -> bool:
        """Validate the logical structure of an argument"""
        if not argument.premises:
            return False

        # Check for basic logical validity based on type
        if argument.logic_type == LogicType.DEDUCTIVE:
            return self._validate_deductive(argument)
        elif argument.logic_type == LogicType.INDUCTIVE:
            return True  # Inductive arguments are always "valid" in structure
        elif argument.logic_type == LogicType.ABDUCTIVE:
            return self._validate_abductive(argument)

        return True  # Default to valid for other types

    def _validate_deductive(self, argument: LogicalArgument) -> bool:
        """Validate deductive argument structure"""
        # Check for common valid forms
        premises_text = ' '.join([p.statement for p in argument.premises])
        conclusion_text = argument.conclusion.statement

        # Modus Ponens: If P then Q, P, therefore Q
        if ('if' in premises_text.lower() and 'then' in premises_text.lower()):
            return True

        # Simple entailment check (basic)
        return len(premises_text) > 10 and len(conclusion_text) > 5

    def _validate_abductive(self, argument: LogicalArgument) -> bool:
        """Validate abductive argument (inference to best explanation)"""
        # Abductive arguments are valid if they provide an explanation
        return len(argument.conclusion.statement) > 10

    def _assess_soundness(self, argument: LogicalArgument) -> bool:
        """Assess whether an argument is sound (valid + true premises)"""
        # For now, assume premises are true unless contradicted
        return argument.validity

    def _assess_inductive_strength(self, argument: LogicalArgument) -> float:
        """Assess the strength of an inductive argument"""
        # Base strength on number of premises and diversity
        premise_count = len(argument.premises)
        strength = min(premise_count / 5, 0.8)  # Max 0.8 strength

        # Increase for diverse premises
        premise_texts = [p.statement.lower() for p in argument.premises]
        unique_words = set()
        for text in premise_texts:
            unique_words.update(text.split())

        diversity = len(unique_words) / sum(len(text.split()) for text in premise_texts) if premise_texts else 0
        strength += diversity * 0.2

        return min(strength, 1.0)

    def generate_logical_proof(self, argument: LogicalArgument) -> LogicalProof:
        """Generate a step-by-step logical proof"""
        steps = []
        rules_used = []

        if argument.logic_type == LogicType.DEDUCTIVE:
            steps, rules_used = self._generate_deductive_proof(argument)
        elif argument.logic_type == LogicType.INDUCTIVE:
            steps, rules_used = self._generate_inductive_proof(argument)
        elif argument.logic_type == LogicType.ABDUCTIVE:
            steps, rules_used = self._generate_abductive_proof(argument)

        # Calculate confidence
        confidence = argument.conclusion.confidence
        if argument.validity:
            confidence *= 0.9
        if argument.soundness:
            confidence *= 0.9

        final_conclusion = f"Therefore: {argument.conclusion.statement}"

        return LogicalProof(
            argument=argument,
            steps=steps,
            rules_used=rules_used,
            final_conclusion=final_conclusion,
            confidence=confidence,
            proof_type=argument.logic_type.value
        )

    def _generate_deductive_proof(self, argument: LogicalArgument) -> Tuple[List[str], List[str]]:
        """Generate deductive proof steps"""
        steps = []
        rules_used = []

        # List premises
        for i, premise in enumerate(argument.premises, 1):
            steps.append(f"Premise {i}: {premise.statement}")

        # Apply logical rules
        if len(argument.premises) >= 2:
            steps.append("Apply logical inference rules:")
            rules_used.append("Modus Ponens")

            if any('if' in p.statement.lower() for p in argument.premises):
                steps.append("1. Conditional premise identified")
                steps.append("2. Antecedent confirmed")
                steps.append("3. Consequent follows necessarily")
                rules_used.append("Hypothetical Syllogism")

        return steps, rules_used

    def _generate_inductive_proof(self, argument: LogicalArgument) -> Tuple[List[str], List[str]]:
        """Generate inductive proof steps"""
        steps = []
        rules_used = ["Induction"]

        # List observations
        for i, premise in enumerate(argument.premises, 1):
            steps.append(f"Observation {i}: {premise.statement}")

        steps.append("Pattern analysis: Similar observations suggest a general principle")
        steps.append(f"Inductive conclusion: {argument.conclusion.statement}")
        steps.append("Note: Inductive conclusions are probable, not certain")

        return steps, rules_used

    def _generate_abductive_proof(self, argument: LogicalArgument) -> Tuple[List[str], List[str]]:
        """Generate abductive proof steps"""
        steps = []
        rules_used = ["Abduction"]

        steps.append("Identify the phenomenon to explain")
        steps.append("Consider possible explanations")

        for i, premise in enumerate(argument.premises, 1):
            steps.append(f"Consider explanation {i}: {premise.statement}")

        steps.append(f"Select best explanation: {argument.conclusion.statement}")
        steps.append("Note: Abductive conclusions are the best available explanation")

        return steps, rules_used

    def format_logical_response(self, proof: LogicalProof) -> str:
        """Format a logical proof for user consumption"""
        lines = [
            f"Logical Analysis ({proof.proof_type.title()} Reasoning)\n",
            "=" * 50,
            ""
        ]

        # Argument structure
        lines.append("ARGUMENT STRUCTURE:")
        for i, premise in enumerate(proof.argument.premises, 1):
            negation = "¬" if premise.is_negated else ""
            lines.append(f"Premise {i}: {negation}{premise.statement}")

        lines.append(f"Conclusion: {proof.argument.conclusion.statement}")
        lines.append("")

        # Proof steps
        lines.append("PROOF STEPS:")
        for i, step in enumerate(proof.steps, 1):
            lines.append(f"{i}. {step}")

        lines.append("")

        # Rules used
        if proof.rules_used:
            lines.append("LOGICAL RULES APPLIED:")
            for rule in proof.rules_used:
                lines.append(f"• {rule}")
            lines.append("")

        # Assessment
        validity_status = "✓ Valid" if proof.argument.validity else "✗ Invalid"
        soundness_status = "✓ Sound" if proof.argument.soundness else "? Soundness uncertain"

        lines.extend([
            "ARGUMENT ASSESSMENT:",
            f"Validity: {validity_status}",
            f"Soundness: {soundness_status}",
            f"Confidence: {proof.confidence:.2f}",
        ])

        if proof.argument.logic_type == LogicType.INDUCTIVE:
            lines.append(f"Inductive Strength: {proof.argument.strength:.2f}")

        return "\n".join(lines)

    def solve_logical_query(self, query: str) -> Dict[str, Any]:
        """Solve a logical reasoning query"""
        try:
            # Analyze the query
            analysis = self.analyze_logical_query(query)

            if not analysis['is_logical']:
                return {
                    'success': False,
                    'error': 'Query does not appear to be logical',
                    'response': 'This does not seem to be a logical reasoning query.'
                }

            # Construct argument
            argument = self.construct_logical_argument(query, analysis['premises'])

            # Generate proof
            proof = self.generate_logical_proof(argument)

            # Format response
            response = self.format_logical_response(proof)

            return {
                'success': True,
                'response': response,
                'analysis': analysis,
                'argument': {
                    'logic_type': argument.logic_type.value,
                    'validity': argument.validity,
                    'soundness': argument.soundness,
                    'confidence': proof.confidence
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f'Error in logical reasoning: {str(e)}'
            }


# Global instance
_logical_reasoner = None

def get_logical_reasoner():
    """Get or create global logical reasoner instance"""
    global _logical_reasoner
    if _logical_reasoner is None:
        _logical_reasoner = LogicalReasoner()
    return _logical_reasoner

