"""
Multi-Step Problem Solver - Decomposes complex problems and solves them step-by-step
Integrates with reasoning engine for comprehensive problem solving
"""
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .reasoning_engine import get_reasoning_engine, ReasoningChain
from .query_intent_analyzer import get_query_intent_analyzer, ReasoningType


@dataclass
class ProblemStep:
    """Represents a single step in problem solving"""
    step_number: int
    description: str
    sub_problem: str
    solution_approach: str
    dependencies: List[int]  # Step numbers this step depends on
    estimated_complexity: float  # 0-1 scale
    success_criteria: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    confidence: float = 0.0
    execution_time: Optional[float] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class SolutionPlan:
    """Complete solution plan for a problem"""
    problem: str
    steps: List[ProblemStep]
    estimated_total_complexity: float
    solution_strategy: str
    risk_assessment: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ProblemSolution:
    """Complete solution to a problem"""
    problem: str
    plan: SolutionPlan
    final_answer: str
    confidence: float
    solution_quality: float
    execution_summary: Dict[str, Any]
    completed_at: datetime = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now()


class ProblemSolver:
    """Multi-step problem solver with decomposition and planning capabilities"""

    def __init__(self):
        self.reasoning_engine = get_reasoning_engine()
        self.query_analyzer = get_query_intent_analyzer()
        self.max_steps = 10
        self.min_step_confidence = 0.6

    def solve_problem(
        self,
        problem: str,
        context: str = "",
        knowledge: List[Dict] = None,
        max_steps: int = None
    ) -> ProblemSolution:
        """
        Solve a complex problem using multi-step decomposition and reasoning.

        Args:
            problem: The problem statement
            context: Additional context
            knowledge: Relevant knowledge items
            max_steps: Maximum number of solution steps

        Returns:
            Complete problem solution
        """
        if max_steps:
            self.max_steps = max_steps

        # Analyze the problem
        problem_analysis = self.query_analyzer.analyze(problem)

        # Create solution plan
        plan = self._create_solution_plan(problem, problem_analysis, context, knowledge)

        # Execute the plan
        solution = self._execute_solution_plan(plan, problem, context, knowledge)

        return solution

    def _create_solution_plan(
        self,
        problem: str,
        problem_analysis: Dict,
        context: str,
        knowledge: List[Dict]
    ) -> SolutionPlan:
        """Create a comprehensive solution plan for the problem"""

        # Determine solution strategy based on problem type
        strategy = self._determine_solution_strategy(problem_analysis)

        # Decompose problem into steps
        steps = self._decompose_problem(problem, problem_analysis, strategy)

        # Calculate dependencies between steps
        self._establish_step_dependencies(steps)

        # Estimate complexity and assess risks
        total_complexity = sum(step.estimated_complexity for step in steps)
        risk_assessment = self._assess_solution_risks(steps, problem_analysis)

        return SolutionPlan(
            problem=problem,
            steps=steps,
            estimated_total_complexity=min(total_complexity, 1.0),
            solution_strategy=strategy,
            risk_assessment=risk_assessment
        )

    def _determine_solution_strategy(self, problem_analysis: Dict) -> str:
        """Determine the best solution strategy based on problem analysis"""
        reasoning_type = problem_analysis.get('reasoning_type', ReasoningType.NONE)
        intent = problem_analysis.get('intent', 'general')
        complexity = problem_analysis.get('query_complexity', 0.0)

        if complexity > 0.7:
            return "decomposition_and_synthesis"
        elif reasoning_type == ReasoningType.DEDUCTIVE:
            return "logical_deduction"
        elif reasoning_type == ReasoningType.MATHEMATICAL:
            return "mathematical_reasoning"
        elif reasoning_type == ReasoningType.CAUSAL:
            return "causal_analysis"
        elif reasoning_type == ReasoningType.COMPARATIVE:
            return "comparative_analysis"
        elif intent == 'how_to':
            return "procedural_solution"
        elif problem_analysis.get('decomposed_queries'):
            return "multi_part_solution"
        else:
            return "analytical_reasoning"

    def _decompose_problem(self, problem: str, analysis: Dict, strategy: str) -> List[ProblemStep]:
        """Decompose the problem into solvable steps"""
        steps = []

        if strategy == "decomposition_and_synthesis":
            steps = self._decompose_complex_problem(problem, analysis)
        elif strategy == "logical_deduction":
            steps = self._decompose_logical_problem(problem, analysis)
        elif strategy == "mathematical_reasoning":
            steps = self._decompose_mathematical_problem(problem, analysis)
        elif strategy == "causal_analysis":
            steps = self._decompose_causal_problem(problem, analysis)
        elif strategy == "comparative_analysis":
            steps = self._decompose_comparative_problem(problem, analysis)
        elif strategy == "procedural_solution":
            steps = self._decompose_procedural_problem(problem, analysis)
        elif strategy == "multi_part_solution":
            steps = self._decompose_multi_part_problem(problem, analysis)
        else:
            steps = self._decompose_general_problem(problem, analysis)

        return steps

    def _decompose_complex_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose very complex problems into fundamental components"""
        steps = []

        # Step 1: Understand the core problem
        steps.append(ProblemStep(
            step_number=1,
            description="Analyze and understand the core problem statement",
            sub_problem=f"What is the fundamental question being asked in: {problem}",
            solution_approach="Break down the problem statement into its essential components",
            dependencies=[],
            estimated_complexity=0.3,
            success_criteria="Clear identification of the main problem and key components"
        ))

        # Step 2: Identify constraints and requirements
        steps.append(ProblemStep(
            step_number=2,
            description="Identify all constraints, requirements, and boundary conditions",
            sub_problem=f"What are the constraints and requirements for solving: {problem}",
            solution_approach="Extract explicit and implicit constraints from the problem",
            dependencies=[1],
            estimated_complexity=0.4,
            success_criteria="Complete list of constraints and requirements identified"
        ))

        # Step 3: Gather relevant information
        steps.append(ProblemStep(
            step_number=3,
            description="Gather all relevant information and knowledge",
            sub_problem=f"What information is needed to solve: {problem}",
            solution_approach="Collect data, facts, and knowledge relevant to the problem",
            dependencies=[1, 2],
            estimated_complexity=0.5,
            success_criteria="All necessary information collected and organized"
        ))

        # Step 4: Develop solution approach
        steps.append(ProblemStep(
            step_number=4,
            description="Develop a systematic approach to solve the problem",
            sub_problem=f"What approach should be used to solve: {problem}",
            solution_approach="Design a step-by-step solution methodology",
            dependencies=[1, 2, 3],
            estimated_complexity=0.6,
            success_criteria="Clear, systematic solution approach developed"
        ))

        # Step 5: Execute solution
        steps.append(ProblemStep(
            step_number=5,
            description="Execute the solution approach",
            sub_problem=f"Apply the solution approach to: {problem}",
            solution_approach="Implement the designed solution step by step",
            dependencies=[4],
            estimated_complexity=0.7,
            success_criteria="Solution approach successfully executed"
        ))

        # Step 6: Validate and verify
        steps.append(ProblemStep(
            step_number=6,
            description="Validate the solution and verify correctness",
            sub_problem=f"Is the solution to {problem} correct and complete?",
            solution_approach="Check solution against constraints and requirements",
            dependencies=[5],
            estimated_complexity=0.4,
            success_criteria="Solution validated and verified as correct"
        ))

        return steps

    def _decompose_logical_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose logical problems into reasoning steps"""
        steps = [
            ProblemStep(1, "Identify premises and assumptions", f"What are the given premises in: {problem}",
                       "Extract stated and implicit assumptions", [], 0.3, "All premises identified"),
            ProblemStep(2, "Determine logical relationships", f"What logical connections exist in: {problem}",
                       "Map relationships between premises", [1], 0.4, "Logical structure understood"),
            ProblemStep(3, "Apply logical rules", f"What logical rules apply to: {problem}",
                       "Apply appropriate logical principles", [1, 2], 0.5, "Logical rules correctly applied"),
            ProblemStep(4, "Draw conclusion", f"What is the logical conclusion for: {problem}",
                       "Derive conclusion from premises", [3], 0.4, "Valid conclusion reached")
        ]
        return steps

    def _decompose_mathematical_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose mathematical problems into calculation steps"""
        steps = [
            ProblemStep(1, "Parse mathematical expressions", f"What are the mathematical components in: {problem}",
                       "Identify variables, operations, and relationships", [], 0.3, "All mathematical elements identified"),
            ProblemStep(2, "Choose appropriate method", f"What mathematical approach solves: {problem}",
                       "Select correct mathematical technique", [1], 0.4, "Appropriate method selected"),
            ProblemStep(3, "Perform calculations", f"Execute the mathematical operations for: {problem}",
                       "Apply mathematical operations step by step", [1, 2], 0.6, "Calculations completed accurately"),
            ProblemStep(4, "Verify result", f"Is the mathematical solution to {problem} correct?",
                       "Check calculations and validate result", [3], 0.3, "Result verified as correct")
        ]
        return steps

    def _decompose_causal_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose causal analysis problems"""
        steps = [
            ProblemStep(1, "Identify observed effects", f"What effects are observed in: {problem}",
                       "List all observed outcomes and changes", [], 0.3, "Effects clearly identified"),
            ProblemStep(2, "Consider potential causes", f"What could cause the effects in: {problem}",
                       "Brainstorm possible causal factors", [1], 0.4, "Potential causes identified"),
            ProblemStep(3, "Evaluate causal relationships", f"Which causes best explain the effects in: {problem}",
                       "Assess strength of causal connections", [1, 2], 0.5, "Strongest causal relationships identified"),
            ProblemStep(4, "Determine most likely cause", f"What is the most probable cause for: {problem}",
                       "Select most supported causal explanation", [3], 0.4, "Most likely cause determined")
        ]
        return steps

    def _decompose_comparative_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose comparison problems"""
        steps = [
            ProblemStep(1, "Identify comparison subjects", f"What entities are being compared in: {problem}",
                       "Clearly define items being compared", [], 0.2, "Comparison subjects identified"),
            ProblemStep(2, "Determine comparison criteria", f"What aspects should be compared in: {problem}",
                       "Establish relevant comparison dimensions", [1], 0.3, "Comparison criteria established"),
            ProblemStep(3, "Gather information for each subject", f"What information is needed for comparison in: {problem}",
                       "Collect data for each comparison subject", [1, 2], 0.4, "Information gathered for all subjects"),
            ProblemStep(4, "Perform systematic comparison", f"How do the subjects compare in: {problem}",
                       "Compare subjects across all criteria", [2, 3], 0.5, "Systematic comparison completed"),
            ProblemStep(5, "Synthesize comparison results", f"What are the key findings from comparing: {problem}",
                       "Summarize comparison outcomes", [4], 0.3, "Comparison results synthesized")
        ]
        return steps

    def _decompose_procedural_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose how-to/procedural problems"""
        steps = [
            ProblemStep(1, "Define the goal", f"What is the desired outcome of: {problem}",
                       "Clearly state the objective", [], 0.2, "Goal clearly defined"),
            ProblemStep(2, "Identify prerequisites", f"What is needed before starting: {problem}",
                       "List required resources and knowledge", [1], 0.3, "Prerequisites identified"),
            ProblemStep(3, "Outline high-level steps", f"What are the main phases of: {problem}",
                       "Break down into major steps", [1, 2], 0.4, "High-level steps outlined"),
            ProblemStep(4, "Detail each step", f"What are the specific actions for each step in: {problem}",
                       "Provide detailed instructions for each step", [3], 0.5, "Each step fully detailed"),
            ProblemStep(5, "Identify potential issues", f"What problems might occur when doing: {problem}",
                       "Anticipate common difficulties", [3, 4], 0.4, "Potential issues identified")
        ]
        return steps

    def _decompose_multi_part_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """Decompose problems with multiple distinct parts"""
        decomposed_queries = analysis.get('decomposed_queries', [])
        steps = []

        for i, sub_query in enumerate(decomposed_queries, 1):
            steps.append(ProblemStep(
                step_number=i,
                description=f"Address part {i} of the multi-part question",
                sub_problem=sub_query,
                solution_approach="Solve this component of the overall problem",
                dependencies=list(range(1, i)),  # Depends on all previous steps
                estimated_complexity=0.4,
                success_criteria=f"Part {i} successfully addressed"
            ))

        # Add synthesis step
        steps.append(ProblemStep(
            step_number=len(steps) + 1,
            description="Synthesize answers from all parts",
            sub_problem=f"Combine solutions to all parts of: {problem}",
            solution_approach="Integrate results from all sub-problems",
            dependencies=list(range(1, len(steps) + 1)),
            estimated_complexity=0.3,
            success_criteria="All parts successfully integrated"
        ))

        return steps

    def _decompose_general_problem(self, problem: str, analysis: Dict) -> List[ProblemStep]:
        """General problem decomposition for unspecified types"""
        steps = [
            ProblemStep(1, "Understand the problem", f"What is being asked in: {problem}",
                       "Analyze and comprehend the problem statement", [], 0.3, "Problem fully understood"),
            ProblemStep(2, "Identify key information", f"What information is provided in: {problem}",
                       "Extract relevant facts and data", [1], 0.4, "Key information identified"),
            ProblemStep(3, "Determine solution approach", f"What method should be used for: {problem}",
                       "Select appropriate problem-solving strategy", [1, 2], 0.5, "Solution approach determined"),
            ProblemStep(4, "Apply the solution", f"Execute the solution for: {problem}",
                       "Implement the chosen approach", [3], 0.6, "Solution successfully applied"),
            ProblemStep(5, "Review and validate", f"Is the solution to {problem} correct?",
                       "Check solution for accuracy and completeness", [4], 0.3, "Solution validated")
        ]
        return steps

    def _establish_step_dependencies(self, steps: List[ProblemStep]):
        """Establish dependencies between problem-solving steps"""
        # Most steps already have dependencies set during creation
        # This method can be enhanced to automatically detect additional dependencies
        pass

    def _assess_solution_risks(self, steps: List[ProblemStep], analysis: Dict) -> Dict[str, Any]:
        """Assess risks associated with the solution plan"""
        total_complexity = sum(step.estimated_complexity for step in steps)
        high_complexity_steps = [step for step in steps if step.estimated_complexity > 0.7]

        risks = {
            'high_complexity_steps': len(high_complexity_steps),
            'total_estimated_complexity': total_complexity,
            'dependency_risks': self._calculate_dependency_risks(steps),
            'knowledge_gaps': self._identify_knowledge_gaps(steps, analysis),
            'failure_points': [step.step_number for step in steps if step.estimated_complexity > 0.8]
        }

        return risks

    def _calculate_dependency_risks(self, steps: List[ProblemStep]) -> float:
        """Calculate risk based on step dependencies"""
        max_dependencies = max(len(step.dependencies) for step in steps) if steps else 0
        avg_dependencies = sum(len(step.dependencies) for step in steps) / len(steps) if steps else 0

        # Higher dependency counts increase risk
        risk = min(avg_dependencies / 3, 1.0)
        return risk

    def _identify_knowledge_gaps(self, steps: List[ProblemStep], analysis: Dict) -> List[str]:
        """Identify potential knowledge gaps in the solution"""
        gaps = []

        # Check for steps that require specialized knowledge
        specialized_terms = ['quantum', 'neural', 'algorithm', 'theorem', 'calculus', 'differential']

        for step in steps:
            step_text = step.sub_problem.lower()
            for term in specialized_terms:
                if term in step_text and analysis.get('query_complexity', 0) > 0.5:
                    gaps.append(f"Specialized knowledge required for step {step.step_number}: {term}")

        return gaps

    def _execute_solution_plan(
        self,
        plan: SolutionPlan,
        problem: str,
        context: str,
        knowledge: List[Dict]
    ) -> ProblemSolution:
        """Execute the solution plan step by step"""
        executed_steps = []
        step_results = []

        for step in plan.steps:
            step.status = "in_progress"

            # Execute the step using reasoning engine
            step_result = self._execute_step(step, context, knowledge, executed_steps)

            step.status = "completed" if step_result['success'] else "failed"
            step.result = step_result['result']
            step.confidence = step_result['confidence']
            step.execution_time = step_result.get('execution_time', 0.0)

            executed_steps.append(step)
            step_results.append(step_result)

            # Check if we should continue (stop on critical failures)
            if not step_result['success'] and step.estimated_complexity > 0.7:
                break

        # Synthesize final answer
        final_answer = self._synthesize_final_answer(plan, executed_steps, step_results)

        # Calculate solution quality
        solution_quality = self._calculate_solution_quality(executed_steps, step_results)

        # Calculate overall confidence
        avg_confidence = sum(step.confidence for step in executed_steps) / len(executed_steps) if executed_steps else 0.0

        execution_summary = {
            'total_steps': len(plan.steps),
            'completed_steps': len([s for s in executed_steps if s.status == 'completed']),
            'failed_steps': len([s for s in executed_steps if s.status == 'failed']),
            'average_step_confidence': avg_confidence,
            'execution_time': sum(step.execution_time or 0 for step in executed_steps)
        }

        return ProblemSolution(
            problem=problem,
            plan=plan,
            final_answer=final_answer,
            confidence=avg_confidence,
            solution_quality=solution_quality,
            execution_summary=execution_summary
        )

    def _execute_step(
        self,
        step: ProblemStep,
        context: str,
        knowledge: List[Dict],
        previous_steps: List[ProblemStep]
    ) -> Dict[str, Any]:
        """Execute a single solution step"""
        import time
        start_time = time.time()

        try:
            # Create enhanced context including previous step results
            enhanced_context = context
            if previous_steps:
                previous_results = []
                for prev_step in previous_steps:
                    if prev_step.result:
                        previous_results.append(f"Step {prev_step.step_number}: {prev_step.result}")
                if previous_results:
                    enhanced_context += "\n\nPrevious steps completed:\n" + "\n".join(previous_results)

            # Use reasoning engine to solve the step
            reasoning_chain = self.reasoning_engine.generate_reasoning_chain(
                step.sub_problem, enhanced_context, knowledge
            )

            execution_time = time.time() - start_time

            success = reasoning_chain.verification_result and reasoning_chain.confidence > self.min_step_confidence

            return {
                'success': success,
                'result': reasoning_chain.conclusion,
                'confidence': reasoning_chain.confidence,
                'reasoning_chain': reasoning_chain,
                'execution_time': execution_time,
                'step_details': {
                    'step_number': step.step_number,
                    'description': step.description,
                    'approach': step.solution_approach
                }
            }

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'result': f"Failed to execute step: {str(e)}",
                'confidence': 0.0,
                'error': str(e),
                'execution_time': execution_time,
                'step_details': {
                    'step_number': step.step_number,
                    'description': step.description
                }
            }

    def _synthesize_final_answer(
        self,
        plan: SolutionPlan,
        executed_steps: List[ProblemStep],
        step_results: List[Dict]
    ) -> str:
        """Synthesize the final answer from all executed steps"""
        successful_steps = [step for step in executed_steps if step.status == 'completed']

        if not successful_steps:
            return "Unable to solve the problem. All solution steps failed."

        # Combine results from successful steps
        step_summaries = []
        for step in successful_steps:
            if step.result:
                step_summaries.append(f"Step {step.step_number} ({step.description}): {step.result}")

        # Create comprehensive answer
        answer_parts = [
            f"Solution to: {plan.problem}\n",
            f"Approach used: {plan.solution_strategy}\n",
            "Step-by-step results:",
            "\n".join(step_summaries),
            f"\nFinal Conclusion: The problem has been addressed through systematic analysis with {len(successful_steps)} successful steps."
        ]

        return "\n".join(answer_parts)

    def _calculate_solution_quality(
        self,
        executed_steps: List[ProblemStep],
        step_results: List[Dict]
    ) -> float:
        """Calculate the overall quality of the solution"""
        if not executed_steps:
            return 0.0

        # Base quality on completion rate and confidence
        completion_rate = len([s for s in executed_steps if s.status == 'completed']) / len(executed_steps)
        avg_confidence = sum(step.confidence for step in executed_steps) / len(executed_steps)

        # Factor in solution coherence (how well steps connect)
        coherence_score = self._calculate_solution_coherence(executed_steps)

        # Weighted combination
        quality = (
            completion_rate * 0.4 +
            avg_confidence * 0.4 +
            coherence_score * 0.2
        )

        return min(quality, 1.0)

    def _calculate_solution_coherence(self, steps: List[ProblemStep]) -> float:
        """Calculate how coherent the solution steps are"""
        if len(steps) < 2:
            return 1.0

        # Check if results reference previous steps
        coherence_indicators = 0
        total_checks = 0

        for i, step in enumerate(steps[1:], 1):  # Start from second step
            if step.result and steps[i-1].result:
                total_checks += 1
                # Check if current step result references previous step
                if f"step {i}" in step.result.lower() or f"previous" in step.result.lower():
                    coherence_indicators += 1

        return coherence_indicators / total_checks if total_checks > 0 else 0.5

    def get_solution_summary(self, solution: ProblemSolution) -> Dict[str, Any]:
        """Get a summary of the solution for reporting"""
        return {
            'problem': solution.problem,
            'strategy': solution.plan.solution_strategy,
            'total_steps': len(solution.plan.steps),
            'completed_steps': solution.execution_summary['completed_steps'],
            'failed_steps': solution.execution_summary['failed_steps'],
            'confidence': solution.confidence,
            'quality': solution.solution_quality,
            'execution_time': solution.execution_summary['execution_time'],
            'risks_identified': len(solution.plan.risk_assessment.get('failure_points', [])),
            'complexity': solution.plan.estimated_total_complexity
        }


# Global instance
_problem_solver = None

def get_problem_solver():
    """Get or create global problem solver instance"""
    global _problem_solver
    if _problem_solver is None:
        _problem_solver = ProblemSolver()
    return _problem_solver

