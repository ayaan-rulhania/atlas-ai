"""
Safe mathematical expression evaluator.
Replaces unsafe eval() with a safe parsing approach.
"""
import re
import math
from typing import Optional, Union


def safe_evaluate_math(expression: str) -> Optional[Union[int, float]]:
    """
    Evaluate simple math expressions safely without using eval().
    
    This function uses a safe tokenizer and evaluator approach instead of eval(),
    which prevents arbitrary code execution vulnerabilities.
    
    Args:
        expression: The mathematical expression to evaluate
        
    Returns:
        The result of the evaluation, or None if the expression is invalid
    """
    if not expression:
        return None
    
    # Remove common question words and normalize
    expr = expression.lower().strip()
    
    # Patterns: "what is 2 + 2", "calculate 10 * 5", "2+2", etc.
    # Extract math expression
    math_patterns = [
        r'what\s+is\s+(.+?)(?:\?|$)',
        r'calculate\s+(.+?)(?:\?|$)',
        r'compute\s+(.+?)(?:\?|$)',
        r'solve\s+(.+?)(?:\?|$)',
        r'^\s*([0-9+\-*/().\s]+)\s*$',  # Pure math expression
        r'=\s*([0-9+\-*/().\s]+)',  # "equals ..."
    ]
    
    math_expr = None
    for pattern in math_patterns:
        match = re.search(pattern, expr)
        if match:
            math_expr = match.group(1).strip()
            break
    
    if not math_expr:
        # Check if it looks like a math expression directly
        if re.match(r'^[\d+\-*/().\s]+$', expr):
            math_expr = expr
        else:
            return None
    
    # Clean and validate the expression
    math_expr = math_expr.replace(' ', '')
    
    # Only allow safe characters: digits, operators, parentheses, decimal point
    if not re.match(r'^[\d+\-*/().]+$', math_expr):
        return None
    
    # Check for dangerous operations (only allow basic math)
    dangerous_patterns = ['__', 'import', 'exec', 'eval', 'open', 'file', 'input', 'raw_input']
    if any(pattern in math_expr for pattern in dangerous_patterns):
        return None
    
    try:
        # Replace common math functions
        math_expr = math_expr.replace('^', '**')  # Power operator
        
        # Use safe tokenizer and evaluator
        result = _safe_eval_expression(math_expr)
        
        # Return formatted result
        if isinstance(result, float):
            if result.is_integer():
                return int(result)
            return round(result, 10)
        return result
    except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
        return None


def _safe_eval_expression(expr: str) -> Union[int, float]:
    """
    Safely evaluate a mathematical expression using a tokenizer approach.
    
    This function parses and evaluates expressions without using eval(),
    making it safe from code injection attacks.
    """
    # Remove whitespace
    expr = expr.replace(' ', '')
    
    # Handle parentheses recursively
    while '(' in expr:
        # Find innermost parentheses
        start = expr.rfind('(')
        end = expr.find(')', start)
        if end == -1:
            raise ValueError("Unmatched parentheses")
        
        # Evaluate expression inside parentheses
        inner_expr = expr[start + 1:end]
        inner_result = _safe_eval_expression(inner_expr)
        
        # Replace parentheses expression with result
        expr = expr[:start] + str(inner_result) + expr[end + 1:]
    
    # Tokenize the expression into numbers and operators
    tokens = _tokenize(expr)
    
    # Evaluate using operator precedence
    return _evaluate_tokens(tokens)


def _tokenize(expr: str) -> list:
    """
    Tokenize a mathematical expression into numbers and operators.
    
    Returns a list of tokens (numbers as floats, operators as strings).
    """
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isdigit() or expr[i] == '.':
            # Parse number
            num_str = ''
            while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                num_str += expr[i]
                i += 1
            try:
                tokens.append(float(num_str))
            except ValueError:
                raise ValueError(f"Invalid number: {num_str}")
        elif expr[i] in '+-*/':
            # Handle unary minus/plus
            if expr[i] == '-' and (not tokens or isinstance(tokens[-1], str)):
                # Unary minus
                i += 1
                num_str = '-'
                if i < len(expr) and expr[i].isdigit():
                    while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                        num_str += expr[i]
                        i += 1
                    try:
                        tokens.append(float(num_str))
                    except ValueError:
                        raise ValueError(f"Invalid number: {num_str}")
                else:
                    tokens.append('-')
            elif expr[i] == '+' and (not tokens or isinstance(tokens[-1], str)):
                # Unary plus (ignore it)
                i += 1
            else:
                tokens.append(expr[i])
                i += 1
        elif expr[i] == ' ':
            i += 1
        else:
            raise ValueError(f"Invalid character: {expr[i]}")
    
    return tokens


def _evaluate_tokens(tokens: list) -> Union[int, float]:
    """
    Evaluate tokens using operator precedence.
    
    Handles: *, /, +, - with proper precedence.
    """
    if not tokens:
        raise ValueError("Empty expression")
    
    # Handle power operator (**)
    tokens = _evaluate_operator(tokens, '**')
    
    # Handle multiplication and division
    tokens = _evaluate_operator(tokens, '*')
    tokens = _evaluate_operator(tokens, '/')
    
    # Handle addition and subtraction
    tokens = _evaluate_operator(tokens, '+')
    tokens = _evaluate_operator(tokens, '-')
    
    if len(tokens) != 1 or not isinstance(tokens[0], (int, float)):
        raise ValueError("Invalid expression")
    
    return tokens[0]


def _evaluate_operator(tokens: list, op: str) -> list:
    """
    Evaluate all occurrences of a specific operator in the token list.
    
    Returns a new token list with the operator evaluated.
    """
    result = []
    i = 0
    while i < len(tokens):
        if isinstance(tokens[i], str) and tokens[i] == op:
            if i == 0 or i == len(tokens) - 1:
                raise ValueError(f"Invalid operator position: {op}")
            
            left = result[-1] if result else tokens[i - 1]
            right = tokens[i + 1]
            
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                raise ValueError(f"Invalid operands for {op}")
            
            if op == '**':
                value = left ** right
            elif op == '*':
                value = left * right
            elif op == '/':
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                value = left / right
            elif op == '+':
                value = left + right
            elif op == '-':
                value = left - right
            else:
                raise ValueError(f"Unknown operator: {op}")
            
            if result:
                result[-1] = value
            else:
                result.append(value)
            i += 2  # Skip operator and right operand
        else:
            if i == 0 or tokens[i - 1] != op:
                result.append(tokens[i])
            i += 1
    
    return result

