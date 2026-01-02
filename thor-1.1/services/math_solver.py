"""
Mathematical Problem Solver - Handles mathematical calculations and proofs
Provides step-by-step mathematical reasoning and validation
"""
import re
import math
import sympy as sp
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class MathType(Enum):
    """Types of mathematical problems"""
    ALGEBRA = "algebra"
    CALCULUS = "calculus"
    GEOMETRY = "geometry"
    TRIGONOMETRY = "trigonometry"
    STATISTICS = "statistics"
    ARITHMETIC = "arithmetic"
    LOGIC_PROOFS = "logic_proofs"


@dataclass
class MathExpression:
    """Represents a mathematical expression"""
    expression: str
    variables: List[str]
    complexity: float
    solvable: bool = True


@dataclass
class MathStep:
    """Represents a step in mathematical problem solving"""
    step_number: int
    description: str
    expression: str
    operation: str
    result: str
    justification: str
    confidence: float = 1.0


@dataclass
class MathSolution:
    """Complete mathematical solution"""
    problem: str
    steps: List[MathStep]
    final_answer: str
    math_type: MathType
    confidence: float
    solution_method: str
    assumptions: List[str] = None

    def __post_init__(self):
        if self.assumptions is None:
            self.assumptions = []


class MathSolver:
    """Handles mathematical problem solving and calculations"""

    def __init__(self):
        self.symbols = {}  # Cache for sympy symbols
        self.common_functions = {
            'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'log': sp.log, 'ln': sp.log, 'exp': sp.exp,
            'sqrt': sp.sqrt, 'abs': sp.Abs,
            'pi': sp.pi, 'e': sp.E
        }

    def analyze_math_query(self, query: str) -> Dict[str, Any]:
        """Analyze a mathematical query"""
        query_lower = query.lower()

        analysis = {
            'is_mathematical': self._is_math_query(query),
            'math_type': self._detect_math_type(query),
            'expressions': self._extract_expressions(query),
            'variables': self._extract_variables(query),
            'operations': self._extract_operations(query),
            'complexity': self._assess_math_complexity(query),
            'requires_calculation': self._requires_calculation(query)
        }

        return analysis

    def _is_math_query(self, query: str) -> bool:
        """Check if query involves mathematics"""
        math_indicators = [
            'calculate', 'solve', 'compute', 'evaluate', 'simplify',
            'factor', 'expand', 'integrate', 'differentiate', 'derive',
            'equation', 'formula', 'function', 'variable', 'constant',
            'plus', 'minus', 'times', 'divide', 'equals', 'sum', 'product',
            'square', 'cube', 'root', 'power', 'exponent'
        ]

        # Check for mathematical symbols
        has_symbols = bool(re.search(r'[+\-*/=^√∫∑∏]', query))
        has_numbers = bool(re.search(r'\d', query))
        has_math_words = any(word in query.lower() for word in math_indicators)

        return has_symbols or has_numbers or has_math_words

    def _detect_math_type(self, query: str) -> MathType:
        """Detect the type of mathematical problem"""
        query_lower = query.lower()

        # Calculus
        if any(word in query_lower for word in ['derivative', 'integral', 'differentiate', 'integrate', 'limit']):
            return MathType.CALCULUS

        # Algebra
        if any(word in query_lower for word in ['solve', 'equation', 'factor', 'expand', 'quadratic']):
            return MathType.ALGEBRA

        # Geometry
        if any(word in query_lower for word in ['area', 'volume', 'triangle', 'circle', 'square', 'rectangle']):
            return MathType.GEOMETRY

        # Trigonometry
        if any(word in query_lower for word in ['sin', 'cos', 'tan', 'angle', 'triangle']):
            return MathType.TRIGONOMETRY

        # Statistics
        if any(word in query_lower for word in ['mean', 'median', 'mode', 'average', 'probability']):
            return MathType.STATISTICS

        # Arithmetic
        if any(word in query_lower for word in ['add', 'subtract', 'multiply', 'divide', 'sum']):
            return MathType.ARITHMETIC

        # Logic proofs
        if any(word in query_lower for word in ['prove', 'theorem', 'axiom', 'proof']):
            return MathType.LOGIC_PROOFS

        return MathType.ALGEBRA  # Default

    def _extract_expressions(self, query: str) -> List[MathExpression]:
        """Extract mathematical expressions from the query"""
        expressions = []

        # Find expressions with mathematical symbols
        expr_pattern = r'[^\s]*[+\-*/=^√∫∑∏\d][^\s]*'
        matches = re.findall(expr_pattern, query)

        for match in matches:
            if len(match) > 1:  # Meaningful expression
                variables = self._extract_variables(match)
                complexity = self._assess_expression_complexity(match)

                expressions.append(MathExpression(
                    expression=match,
                    variables=variables,
                    complexity=complexity
                ))

        return expressions

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variable names from text"""
        # Find single letters that could be variables
        variables = re.findall(r'\b[a-zA-Z]\b', text)
        # Filter out common words
        common_words = {'a', 'i', 'e', 'x', 'y', 'z'}  # Keep common variables
        variables = [v for v in variables if v.lower() not in {'a', 'i'} or v.lower() in common_words]

        return list(set(variables))

    def _extract_operations(self, query: str) -> List[str]:
        """Extract mathematical operations from the query"""
        operations = []

        operation_patterns = {
            'addition': r'\+',
            'subtraction': r'-',
            'multiplication': r'[\*×]',
            'division': r'[/÷]',
            'exponentiation': r'\^|\*\*',
            'square_root': r'√|sqrt',
            'integration': r'∫|integral',
            'differentiation': r'd/dx|derivative',
            'equals': r'='
        }

        for op_name, pattern in operation_patterns.items():
            if re.search(pattern, query):
                operations.append(op_name)

        return operations

    def _assess_math_complexity(self, query: str) -> float:
        """Assess the mathematical complexity of the query"""
        complexity = 0.0

        # Count operations
        operation_count = len(self._extract_operations(query))
        complexity += min(operation_count * 0.1, 0.4)

        # Check for advanced functions
        advanced_functions = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt', '∫', 'd/dx']
        for func in advanced_functions:
            if func in query:
                complexity += 0.2
                break

        # Check for equations vs simple calculations
        if '=' in query:
            complexity += 0.3

        # Length-based complexity
        word_count = len(query.split())
        complexity += min(word_count / 30, 0.3)

        return min(complexity, 1.0)

    def _assess_expression_complexity(self, expression: str) -> float:
        """Assess complexity of a single mathematical expression"""
        complexity = 0.0

        # Count operators
        operators = len(re.findall(r'[+\-*/^=]', expression))
        complexity += min(operators * 0.1, 0.5)

        # Check for functions
        functions = len(re.findall(r'(sin|cos|tan|log|ln|exp|sqrt)', expression))
        complexity += min(functions * 0.2, 0.5)

        # Check for variables
        variables = len(set(re.findall(r'\b[a-zA-Z]\b', expression)))
        complexity += min(variables * 0.1, 0.3)

        return min(complexity, 1.0)

    def _requires_calculation(self, query: str) -> bool:
        """Check if query requires actual calculation"""
        calculation_indicators = [
            'calculate', 'compute', 'solve', 'evaluate', 'find',
            'what is', 'how much', 'equals'
        ]

        return any(indicator in query.lower() for indicator in calculation_indicators)

    def solve_mathematical_problem(self, problem: str) -> Dict[str, Any]:
        """Solve a mathematical problem step by step"""
        try:
            # Analyze the problem
            analysis = self.analyze_math_query(problem)

            if not analysis['is_mathematical']:
                return {
                    'success': False,
                    'error': 'Query does not appear to be mathematical',
                    'response': 'This does not seem to be a mathematical problem.'
                }

            # Create solution based on math type
            math_type = analysis['math_type']

            if math_type == MathType.ARITHMETIC:
                solution = self._solve_arithmetic(problem, analysis)
            elif math_type == MathType.ALGEBRA:
                solution = self._solve_algebra(problem, analysis)
            elif math_type == MathType.CALCULUS:
                solution = self._solve_calculus(problem, analysis)
            else:
                solution = self._solve_general_math(problem, analysis)

            # Format the solution
            response = self._format_math_solution(solution)

            return {
                'success': True,
                'response': response,
                'solution': {
                    'math_type': solution.math_type.value,
                    'steps': len(solution.steps),
                    'confidence': solution.confidence,
                    'method': solution.solution_method,
                    'final_answer': solution.final_answer
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f'Error in mathematical calculation: {str(e)}'
            }

    def _solve_arithmetic(self, problem: str, analysis: Dict) -> MathSolution:
        """Solve basic arithmetic problems"""
        steps = []

        # Try to extract and evaluate simple expressions
        expressions = analysis['expressions']

        if expressions:
            for i, expr in enumerate(expressions, 1):
                try:
                    # Simple evaluation for basic arithmetic
                    result = self._evaluate_simple_expression(expr.expression)
                    steps.append(MathStep(
                        step_number=i,
                        description=f"Evaluate expression: {expr.expression}",
                        expression=expr.expression,
                        operation="arithmetic_evaluation",
                        result=str(result),
                        justification="Direct calculation",
                        confidence=0.95
                    ))
                except:
                    steps.append(MathStep(
                        step_number=i,
                        description=f"Parse expression: {expr.expression}",
                        expression=expr.expression,
                        operation="expression_parsing",
                        result="Could not evaluate automatically",
                        justification="Complex expression requires manual calculation",
                        confidence=0.5
                    ))

        final_answer = steps[-1].result if steps else "No solution found"
        confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.5

        return MathSolution(
            problem=problem,
            steps=steps,
            final_answer=final_answer,
            math_type=MathType.ARITHMETIC,
            confidence=confidence,
            solution_method="arithmetic_evaluation"
        )

    def _solve_algebra(self, problem: str, analysis: Dict) -> MathSolution:
        """Solve algebraic problems"""
        steps = []

        # Look for equations to solve
        equations = re.findall(r'[^=]*=[^=]*', problem)

        for i, equation in enumerate(equations, 1):
            steps.append(MathStep(
                step_number=i,
                description=f"Identify equation: {equation.strip()}",
                expression=equation.strip(),
                operation="equation_identification",
                result=f"Equation: {equation.strip()}",
                justification="Extracted equation from problem statement",
                confidence=0.9
            ))

            # Try to solve simple equations
            if '=' in equation:
                try:
                    solution = self._solve_simple_equation(equation)
                    steps.append(MathStep(
                        step_number=i + len(equations),
                        description="Solve equation",
                        expression=equation.strip(),
                        operation="equation_solving",
                        result=f"Solution: {solution}",
                        justification="Applied algebraic methods",
                        confidence=0.85
                    ))
                except:
                    steps.append(MathStep(
                        step_number=i + len(equations),
                        description="Attempt to solve equation",
                        expression=equation.strip(),
                        operation="equation_solving",
                        result="Requires advanced algebraic techniques",
                        justification="Equation too complex for automatic solving",
                        confidence=0.4
                    ))

        final_answer = steps[-1].result if steps else "No algebraic solution found"
        confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.5

        return MathSolution(
            problem=problem,
            steps=steps,
            final_answer=final_answer,
            math_type=MathType.ALGEBRA,
            confidence=confidence,
            solution_method="algebraic_manipulation"
        )

    def _solve_calculus(self, problem: str, analysis: Dict) -> MathSolution:
        """Solve calculus problems"""
        steps = []

        # Identify calculus operations
        if 'derivative' in problem.lower() or 'differentiate' in problem.lower():
            steps.append(MathStep(
                step_number=1,
                description="Identify differentiation problem",
                expression="d/dx[f(x)]",
                operation="derivative_identification",
                result="Differentiation required",
                justification="Problem involves finding derivatives",
                confidence=0.9
            ))

        elif 'integral' in problem.lower() or '∫' in problem:
            steps.append(MathStep(
                step_number=1,
                description="Identify integration problem",
                expression="∫f(x)dx",
                operation="integral_identification",
                result="Integration required",
                justification="Problem involves finding antiderivatives",
                confidence=0.9
            ))

        else:
            steps.append(MathStep(
                step_number=1,
                description="Identify calculus operation",
                expression="Unknown calculus operation",
                operation="calculus_identification",
                result="Requires calculus techniques",
                justification="Problem involves advanced mathematical concepts",
                confidence=0.6
            ))

        final_answer = "Requires manual calculus calculation"
        confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.5

        return MathSolution(
            problem=problem,
            steps=steps,
            final_answer=final_answer,
            math_type=MathType.CALCULUS,
            confidence=confidence,
            solution_method="calculus_techniques"
        )

    def _solve_general_math(self, problem: str, analysis: Dict) -> MathSolution:
        """Solve general mathematical problems"""
        steps = []

        steps.append(MathStep(
            step_number=1,
            description="Analyze mathematical problem",
            expression=problem,
            operation="problem_analysis",
            result=f"Problem type: {analysis['math_type'].value}",
            justification="General mathematical analysis",
            confidence=0.7
        ))

        final_answer = "Mathematical analysis completed - manual calculation may be required"
        confidence = 0.6

        return MathSolution(
            problem=problem,
            steps=steps,
            final_answer=final_answer,
            math_type=analysis['math_type'],
            confidence=confidence,
            solution_method="general_mathematical_analysis"
        )

    def _evaluate_simple_expression(self, expression: str) -> float:
        """Evaluate simple mathematical expressions"""
        # Remove spaces and handle basic operations
        expr = expression.replace(' ', '')

        # Handle basic arithmetic
        try:
            # Use eval with restricted globals for safety
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({"__builtins__": {}})

            result = eval(expr, allowed_names)
            return result
        except:
            raise ValueError(f"Cannot evaluate expression: {expression}")

    def _solve_simple_equation(self, equation: str) -> str:
        """Solve simple algebraic equations"""
        # For now, provide template solutions
        # In a full implementation, this would use sympy or other CAS

        if 'x' in equation:
            return "x = [solution requires algebraic manipulation]"
        elif 'y' in equation:
            return "y = [solution requires algebraic manipulation]"
        else:
            return "Equation solution requires specific algebraic techniques"

    def _format_math_solution(self, solution: MathSolution) -> str:
        """Format a mathematical solution for user consumption"""
        lines = [
            f"Mathematical Solution ({solution.math_type.value.title()})\n",
            "=" * 50,
            f"Problem: {solution.problem}\n",
            f"Method: {solution.solution_method}\n",
            ""
        ]

        # Solution steps
        lines.append("SOLUTION STEPS:")
        for step in solution.steps:
            lines.append(f"Step {step.step_number}: {step.description}")
            lines.append(f"  Expression: {step.expression}")
            lines.append(f"  Operation: {step.operation}")
            lines.append(f"  Result: {step.result}")
            lines.append(f"  Justification: {step.justification}")
            lines.append("")

        # Final answer
        lines.extend([
            "=" * 50,
            "FINAL ANSWER:",
            solution.final_answer,
            "",
            f"Confidence: {solution.confidence:.2f}",
            ""
        ])

        return "\n".join(lines)


# Global instance
_math_solver = None

def get_math_solver():
    """Get or create global math solver instance"""
    global _math_solver
    if _math_solver is None:
        _math_solver = MathSolver()
    return _math_solver

