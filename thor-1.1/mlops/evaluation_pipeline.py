"""
Model Evaluation Pipeline with standardized benchmarks.
"""
import json
import torch
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class EvaluationPipeline:
    """
    Standardized evaluation pipeline for model benchmarking.
    """
    
    def __init__(self, benchmark_dir: str = "benchmarks"):
        self.benchmark_dir = Path(benchmark_dir)
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self._load_benchmarks()
    
    def _load_benchmarks(self):
        """Load comprehensive benchmark datasets including standard NLP benchmarks."""
        self.benchmarks = {}

        # Create default benchmarks if they don't exist
        default_benchmarks = {
            "qa_benchmark.json": {
                "name": "Question Answering",
                "tasks": [
                    {"question": "What is machine learning?", "expected_keywords": ["algorithm", "data", "learn"]},
                    {"question": "Explain neural networks", "expected_keywords": ["neurons", "layers", "weights"]},
                    {"question": "What is Python?", "expected_keywords": ["programming", "language", "code"]}
                ]
            },
            "summarization_benchmark.json": {
                "name": "Text Summarization",
                "tasks": [
                    {"input": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from and make predictions on data. It is used in various applications including image recognition, natural language processing, and recommendation systems.", "max_length": 50},
                    {"input": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms and has a large standard library. Python is widely used for web development, data science, and automation.", "max_length": 50}
                ]
            },
            "classification_benchmark.json": {
                "name": "Text Classification",
                "tasks": [
                    {"text": "I love this product!", "expected_label": "positive"},
                    {"text": "This is terrible", "expected_label": "negative"},
                    {"text": "It's okay, nothing special", "expected_label": "neutral"}
                ]
            },
            "mmlu_benchmark.json": {
                "name": "MMLU (Massive Multitask Language Understanding) - Sample",
                "description": "Sample questions from MMLU covering various domains",
                "tasks": [
                    {
                        "question": "What is the capital of France?",
                        "options": ["London", "Berlin", "Paris", "Madrid"],
                        "correct_answer": "Paris",
                        "domain": "Geography"
                    },
                    {
                        "question": "In Python, what does 'len()' function do?",
                        "options": ["Create a list", "Get length of sequence", "Convert to string", "Sort elements"],
                        "correct_answer": "Get length of sequence",
                        "domain": "Computer Science"
                    },
                    {
                        "question": "What is the chemical symbol for water?",
                        "options": ["H2O", "CO2", "O2", "N2"],
                        "correct_answer": "H2O",
                        "domain": "Chemistry"
                    }
                ]
            },
            "hellaswag_benchmark.json": {
                "name": "HellaSwag - Sample",
                "description": "Sample commonsense reasoning tasks from HellaSwag",
                "tasks": [
                    {
                        "context": "A man is cooking pasta. He boils water, adds salt, then",
                        "options": [
                            "puts the pasta in the pot.",
                            "puts the pasta on the counter.",
                            "throws the pasta out the window.",
                            "gives the pasta to his dog."
                        ],
                        "correct_answer": "puts the pasta in the pot."
                    },
                    {
                        "context": "Someone is writing a letter. They get a pen, paper, then",
                        "options": [
                            "start writing the letter.",
                            "throw the paper away.",
                            "use the pen as a sword.",
                            "draw pictures instead."
                        ],
                        "correct_answer": "start writing the letter."
                    }
                ]
            },
            "reasoning_benchmark.json": {
                "name": "Reasoning Tasks",
                "description": "Various reasoning and logic tasks",
                "tasks": [
                    {
                        "question": "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
                        "type": "logical_reasoning",
                        "expected_answer": "No, we cannot conclude this"
                    },
                    {
                        "question": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
                        "type": "math_reasoning",
                        "expected_answer": "$0.05"
                    },
                    {
                        "question": "Complete the sequence: 2, 4, 8, 16, ?",
                        "type": "pattern_reasoning",
                        "expected_answer": "32"
                    }
                ]
            },
            "code_benchmark.json": {
                "name": "Code Generation and Understanding",
                "description": "Programming and code-related tasks",
                "tasks": [
                    {
                        "prompt": "Write a Python function to calculate factorial:",
                        "type": "code_generation",
                        "evaluation_criteria": ["correct_syntax", "correct_logic", "efficiency"]
                    },
                    {
                        "code": "def add(a, b): return a + b",
                        "question": "What does this function do?",
                        "expected_answer": "Adds two numbers together",
                        "type": "code_understanding"
                    }
                ]
            },
            "truthfulness_benchmark.json": {
                "name": "Truthfulness and Factuality",
                "description": "Tasks to evaluate factual accuracy and truthfulness",
                "tasks": [
                    {
                        "question": "What is the largest planet in our solar system?",
                        "expected_answer": "Jupiter",
                        "false_options": ["Saturn", "Mars", "Earth"]
                    },
                    {
                        "statement": "The Great Wall of China is visible from space with the naked eye.",
                        "is_true": False,
                        "explanation": "This is a common myth; it's not visible from space without aid"
                    }
                ]
            }
        }
        
        for filename, benchmark_data in default_benchmarks.items():
            benchmark_path = self.benchmark_dir / filename
            if not benchmark_path.exists():
                with open(benchmark_path, 'w') as f:
                    json.dump(benchmark_data, f, indent=2)
            
            with open(benchmark_path, 'r') as f:
                self.benchmarks[filename] = json.load(f)
    
    def evaluate_model(
        self,
        model: Any,
        tokenizer: Any,
        task_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a model on benchmark tasks.
        
        Args:
            model: Model to evaluate
            tokenizer: Tokenizer for the model
            task_types: List of task types to evaluate (None = all)
            
        Returns:
            Dictionary with evaluation results
        """
        if task_types is None:
            task_types = ["qa", "summarization", "classification", "mmlu", "hellaswag", "reasoning", "code", "truthfulness"]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {},
            "overall_score": 0.0
        }
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        model.eval()
        
        # Evaluate each task type
        task_scores = []

        if "qa" in task_types:
            qa_score = self._evaluate_qa(model, tokenizer)
            results["tasks"]["question_answering"] = qa_score
            task_scores.append(qa_score.get("accuracy", 0.0))

        if "summarization" in task_types:
            summ_score = self._evaluate_summarization(model, tokenizer)
            results["tasks"]["summarization"] = summ_score
            task_scores.append(summ_score.get("rouge_score", 0.0))

        if "classification" in task_types:
            cls_score = self._evaluate_classification(model, tokenizer)
            results["tasks"]["classification"] = cls_score
            task_scores.append(cls_score.get("accuracy", 0.0))

        if "mmlu" in task_types:
            mmlu_score = self._evaluate_mmlu(model, tokenizer)
            results["tasks"]["mmlu"] = mmlu_score
            task_scores.append(mmlu_score.get("accuracy", 0.0))

        if "hellaswag" in task_types:
            hellaswag_score = self._evaluate_hellaswag(model, tokenizer)
            results["tasks"]["hellaswag"] = hellaswag_score
            task_scores.append(hellaswag_score.get("accuracy", 0.0))

        if "reasoning" in task_types:
            reasoning_score = self._evaluate_reasoning(model, tokenizer)
            results["tasks"]["reasoning"] = reasoning_score
            task_scores.append(reasoning_score.get("accuracy", 0.0))

        if "code" in task_types:
            code_score = self._evaluate_code(model, tokenizer)
            results["tasks"]["code"] = code_score
            task_scores.append(code_score.get("quality_score", 0.0))

        if "truthfulness" in task_types:
            truth_score = self._evaluate_truthfulness(model, tokenizer)
            results["tasks"]["truthfulness"] = truth_score
            task_scores.append(truth_score.get("accuracy", 0.0))
        
        # Calculate overall score
        if task_scores:
            results["overall_score"] = sum(task_scores) / len(task_scores)
        
        return results
    
    def _evaluate_qa(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate question answering performance."""
        benchmark = self.benchmarks.get("qa_benchmark.json", {})
        tasks = benchmark.get("tasks", [])
        
        correct = 0
        total = len(tasks)
        
        for task in tasks:
            question = task.get("question", "")
            expected_keywords = task.get("expected_keywords", [])
            
            try:
                # Generate answer
                with torch.no_grad():
                    if hasattr(model, 'predict'):
                        answer = model.predict(question, task="question_answering")
                        answer_text = answer.get("answer", "") if isinstance(answer, dict) else str(answer)
                    else:
                        # Fallback: simple forward pass
                        inputs = tokenizer.encode(question)
                        inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                        outputs = model(inputs)
                        answer_text = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])
                
                # Check if expected keywords are present
                answer_lower = answer_text.lower()
                keywords_found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
                
                if keywords_found >= len(expected_keywords) * 0.5:  # At least 50% of keywords
                    correct += 1
            except Exception as e:
                print(f"[Evaluation] Error in QA evaluation: {e}")
        
        accuracy = correct / total if total > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        }
    
    def _evaluate_summarization(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate summarization performance."""
        benchmark = self.benchmarks.get("summarization_benchmark.json", {})
        tasks = benchmark.get("tasks", [])
        
        # Simple evaluation: check if output is shorter than input
        valid_summaries = 0
        total = len(tasks)
        
        for task in tasks:
            input_text = task.get("input", "")
            max_length = task.get("max_length", 50)
            
            try:
                with torch.no_grad():
                    if hasattr(model, 'predict'):
                        summary = model.predict(input_text, task="text_generation")
                        summary_text = summary.get("text", "") if isinstance(summary, dict) else str(summary)
                    else:
                        inputs = tokenizer.encode(input_text)
                        inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                        outputs = model(inputs)
                        summary_text = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])
                
                # Check if summary is shorter
                if len(summary_text.split()) < len(input_text.split()) and len(summary_text) > 0:
                    valid_summaries += 1
            except Exception as e:
                print(f"[Evaluation] Error in summarization evaluation: {e}")
        
        rouge_score = valid_summaries / total if total > 0 else 0.0
        
        return {
            "rouge_score": rouge_score,
            "valid": valid_summaries,
            "total": total
        }
    
    def _evaluate_classification(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate classification performance."""
        benchmark = self.benchmarks.get("classification_benchmark.json", {})
        tasks = benchmark.get("tasks", [])
        
        correct = 0
        total = len(tasks)
        
        for task in tasks:
            text = task.get("text", "")
            expected_label = task.get("expected_label", "")
            
            try:
                with torch.no_grad():
                    if hasattr(model, 'predict'):
                        prediction = model.predict(text, task="sentiment_analysis")
                        predicted_label = prediction.get("label", "") if isinstance(prediction, dict) else str(prediction)
                    else:
                        inputs = tokenizer.encode(text)
                        inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                        outputs = model(inputs)
                        predicted_label = "positive" if outputs.argmax().item() > 0.5 else "negative"
                
                if expected_label.lower() in predicted_label.lower() or predicted_label.lower() in expected_label.lower():
                    correct += 1
            except Exception as e:
                print(f"[Evaluation] Error in classification evaluation: {e}")
        
        accuracy = correct / total if total > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        }

    def _evaluate_mmlu(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate MMLU (Massive Multitask Language Understanding) performance."""
        benchmark = self.benchmarks.get("mmlu_benchmark.json", {})
        tasks = benchmark.get("tasks", [])

        correct = 0
        total = len(tasks)

        for task in tasks:
            question = task.get("question", "")
            options = task.get("options", [])
            correct_answer = task.get("correct_answer", "")

            if not question or not options or not correct_answer:
                continue

            # Create multiple choice prompt
            prompt = f"Question: {question}\n\nOptions:\n"
            for i, option in enumerate(options):
                prompt += f"{chr(65 + i)}. {option}\n"

            prompt += "\nAnswer with the letter of the correct option:"

            try:
                with torch.no_grad():
                    if hasattr(model, 'predict'):
                        prediction = model.predict(prompt, task="text_generation")
                        answer_text = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                    else:
                        inputs = tokenizer.encode(prompt)
                        inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                        outputs = model(inputs)
                        answer_text = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                # Extract answer (look for letter at start of response)
                answer_text = answer_text.strip().upper()
                if answer_text and answer_text[0] in 'ABCD':
                    predicted_letter = answer_text[0]
                    correct_letter = chr(65 + options.index(correct_answer)) if correct_answer in options else None

                    if predicted_letter == correct_letter:
                        correct += 1
            except Exception as e:
                print(f"[Evaluation] Error in MMLU evaluation: {e}")

        accuracy = correct / total if total > 0 else 0.0

        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        }

    def _evaluate_hellaswag(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate HellaSwag commonsense reasoning performance."""
        benchmark = self.benchmarks.get("hellaswag_benchmark.json", {})
        tasks = benchmark.get("tasks", [])

        correct = 0
        total = len(tasks)

        for task in tasks:
            context = task.get("context", "")
            options = task.get("options", [])
            correct_answer = task.get("correct_answer", "")

            if not context or not options or not correct_answer:
                continue

            # Create completion prompt
            prompt = f"Complete the scenario naturally:\n\n{context}"

            try:
                with torch.no_grad():
                    if hasattr(model, 'predict'):
                        prediction = model.predict(prompt, task="text_generation")
                        completion = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                    else:
                        inputs = tokenizer.encode(prompt)
                        inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                        outputs = model(inputs)
                        completion = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                # Find best matching option
                completion = completion.strip().lower()
                best_match = None
                best_score = 0

                for option in options:
                    option_lower = option.lower()
                    # Simple overlap score
                    overlap = len(set(completion.split()) & set(option_lower.split()))
                    score = overlap / len(option_lower.split()) if option_lower.split() else 0

                    if score > best_score:
                        best_score = score
                        best_match = option

                if best_match == correct_answer:
                    correct += 1

            except Exception as e:
                print(f"[Evaluation] Error in HellaSwag evaluation: {e}")

        accuracy = correct / total if total > 0 else 0.0

        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        }

    def _evaluate_reasoning(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate reasoning capabilities."""
        benchmark = self.benchmarks.get("reasoning_benchmark.json", {})
        tasks = benchmark.get("tasks", [])

        correct = 0
        total = len(tasks)

        for task in tasks:
            question = task.get("question", "")
            expected_answer = task.get("expected_answer", "")

            if not question or not expected_answer:
                continue

            # Use chain-of-thought prompting for reasoning
            prompt = f"""Please solve this step by step:

{question}

Let me think through this carefully:
1. First, understand what is being asked
2. Break down the problem
3. Apply logical reasoning
4. Provide the answer

Final answer:"""

            try:
                with torch.no_grad():
                    if hasattr(model, 'predict'):
                        prediction = model.predict(prompt, task="text_generation")
                        answer = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                    else:
                        inputs = tokenizer.encode(prompt)
                        inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                        outputs = model(inputs)
                        answer = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                # Check if expected answer appears in response
                answer_lower = answer.lower()
                expected_lower = expected_answer.lower()

                if expected_lower in answer_lower:
                    correct += 1

            except Exception as e:
                print(f"[Evaluation] Error in reasoning evaluation: {e}")

        accuracy = correct / total if total > 0 else 0.0

        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        }

    def _evaluate_code(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate code generation and understanding capabilities."""
        benchmark = self.benchmarks.get("code_benchmark.json", {})
        tasks = benchmark.get("tasks", [])

        total_quality = 0.0
        total = len(tasks)

        for task in tasks:
            task_type = task.get("type", "")

            if task_type == "code_generation":
                prompt = task.get("prompt", "")

                try:
                    with torch.no_grad():
                        if hasattr(model, 'predict'):
                            prediction = model.predict(prompt, task="text_generation")
                            code = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                        else:
                            inputs = tokenizer.encode(prompt)
                            inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                            outputs = model(inputs)
                            code = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                    # Simple quality scoring based on presence of key elements
                    quality_score = 0.0
                    code_lower = code.lower()

                    if "def" in code_lower and "(" in code and ")" in code:
                        quality_score += 0.5  # Basic function structure

                    if "return" in code_lower:
                        quality_score += 0.3  # Has return statement

                    if len(code.split()) > 5:
                        quality_score += 0.2  # Substantial code

                    total_quality += quality_score

                except Exception as e:
                    print(f"[Evaluation] Error in code evaluation: {e}")

            elif task_type == "code_understanding":
                code = task.get("code", "")
                question = task.get("question", "")
                expected = task.get("expected_answer", "")

                prompt = f"Code:\n{code}\n\nQuestion: {question}\n\nAnswer:"

                try:
                    with torch.no_grad():
                        if hasattr(model, 'predict'):
                            prediction = model.predict(prompt, task="text_generation")
                            answer = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                        else:
                            inputs = tokenizer.encode(prompt)
                            inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                            outputs = model(inputs)
                            answer = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                    # Check if expected answer is mentioned
                    if expected.lower() in answer.lower():
                        total_quality += 1.0
                    else:
                        total_quality += 0.5  # Partial credit

                except Exception as e:
                    print(f"[Evaluation] Error in code understanding evaluation: {e}")

        quality_score = total_quality / total if total > 0 else 0.0

        return {
            "quality_score": quality_score,
            "total_tasks": total
        }

    def _evaluate_truthfulness(self, model: Any, tokenizer: Any) -> Dict[str, float]:
        """Evaluate truthfulness and factual accuracy."""
        benchmark = self.benchmarks.get("truthfulness_benchmark.json", {})
        tasks = benchmark.get("tasks", [])

        correct = 0
        total = len(tasks)

        for task in tasks:
            if "question" in task:
                # Factual question
                question = task.get("question", "")
                expected = task.get("expected_answer", "")

                try:
                    with torch.no_grad():
                        if hasattr(model, 'predict'):
                            prediction = model.predict(question, task="text_generation")
                            answer = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                        else:
                            inputs = tokenizer.encode(question)
                            inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                            outputs = model(inputs)
                            answer = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                    if expected.lower() in answer.lower():
                        correct += 1

                except Exception as e:
                    print(f"[Evaluation] Error in truthfulness evaluation: {e}")

            elif "statement" in task:
                # True/false statement
                statement = task.get("statement", "")
                is_true = task.get("is_true", False)

                prompt = f"Is this statement true or false? Explain your reasoning.\n\nStatement: {statement}\n\nAnswer:"

                try:
                    with torch.no_grad():
                        if hasattr(model, 'predict'):
                            prediction = model.predict(prompt, task="text_generation")
                            response = prediction.get("generated_text", "") if isinstance(prediction, dict) else str(prediction)
                        else:
                            inputs = tokenizer.encode(prompt)
                            inputs = torch.tensor([inputs]).to(next(model.parameters()).device)
                            outputs = model(inputs)
                            response = tokenizer.decode(outputs.argmax(-1).cpu().numpy()[0])

                    # Check if model identifies truth value correctly
                    response_lower = response.lower()
                    if is_true and ("true" in response_lower or "correct" in response_lower):
                        correct += 1
                    elif not is_true and ("false" in response_lower or "incorrect" in response_lower):
                        correct += 1

                except Exception as e:
                    print(f"[Evaluation] Error in truthfulness evaluation: {e}")

        accuracy = correct / total if total > 0 else 0.0

        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total
        }

    def compare_models(self, results1: Dict, results2: Dict) -> Dict[str, Any]:
        """Compare evaluation results of two models."""
        comparison = {
            "model1_score": results1.get("overall_score", 0.0),
            "model2_score": results2.get("overall_score", 0.0),
            "improvement": results2.get("overall_score", 0.0) - results1.get("overall_score", 0.0),
            "task_comparisons": {}
        }
        
        # Compare individual tasks
        for task_name in set(list(results1.get("tasks", {}).keys()) + list(results2.get("tasks", {}).keys())):
            score1 = results1.get("tasks", {}).get(task_name, {}).get("accuracy", results1.get("tasks", {}).get(task_name, {}).get("rouge_score", 0.0))
            score2 = results2.get("tasks", {}).get(task_name, {}).get("accuracy", results2.get("tasks", {}).get(task_name, {}).get("rouge_score", 0.0))
            
            comparison["task_comparisons"][task_name] = {
                "model1": score1,
                "model2": score2,
                "improvement": score2 - score1
            }
        
        return comparison


def get_evaluation_pipeline(benchmark_dir: Optional[str] = None) -> EvaluationPipeline:
    """Get or create an evaluation pipeline instance."""
    if benchmark_dir is None:
        benchmark_dir = "benchmarks"
    return EvaluationPipeline(benchmark_dir)

