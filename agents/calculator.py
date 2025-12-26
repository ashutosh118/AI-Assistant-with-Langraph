import re
import math
import numpy as np
from typing import Dict, Any, Union
import streamlit as st
from config.settings import settings
from utils.models import model_manager

class CalculatorAgent:
    """Agent for mathematical calculations and problem solving"""
    
    def __init__(self):
        self.name = "Calculator Agent"
        self.description = "Performs mathematical calculations and problem solving"
    
    def safe_eval(self, expression: str) -> Union[float, int, str]:
        """Safely evaluate mathematical expressions"""
        try:
            # Remove spaces and convert to lowercase
            expression = expression.replace(" ", "").lower()
            
            # Define allowed functions
            allowed_names = {
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'sum': sum, 'pow': pow, 'sqrt': math.sqrt,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'log10': math.log10, 'exp': math.exp,
                'pi': math.pi, 'e': math.e,
                'floor': math.floor, 'ceil': math.ceil,
                'factorial': math.factorial
            }
            
            # Replace common mathematical expressions
            expression = expression.replace('^', '**')  # Power operator
            expression = expression.replace('√', 'sqrt')  # Square root
            
            # Check for disallowed characters/functions
            if any(char in expression for char in ['import', 'exec', 'eval', 'open', 'file']):
                return "Invalid expression: contains disallowed operations"
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            # Format the result
            if isinstance(result, float):
                if result.is_integer():
                    return int(result)
                else:
                    return round(result, 8)
            
            return result
            
        except Exception as e:
            return f"Error evaluating expression: {e}"
    
    def extract_calculation(self, text: str) -> list:
        """Extract mathematical expressions from text"""
        # Patterns for mathematical expressions
        patterns = [
            r'[\d\+\-\*/\(\)\.\s\^√]+',  # Basic arithmetic
            r'\d+\s*[\+\-\*/\^]\s*\d+',  # Simple operations
            r'sqrt\(\d+\)',  # Square root
            r'sin\(\d+\)|cos\(\d+\)|tan\(\d+\)',  # Trigonometric
            r'\d+\s*\^\s*\d+',  # Powers
        ]
        
        expressions = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            expressions.extend(matches)
        
        return list(set(expressions))  # Remove duplicates
    
    def solve_word_problem(self, problem: str) -> str:
        """Solve mathematical word problems"""
        try:
            prompt = f"""Please solve the following mathematical word problem step by step:

{problem}

Please provide:
1. Understanding of the problem
2. Step-by-step solution
3. Final answer with appropriate units
4. Verification if possible

Solution:"""
            
            solution = model_manager.azure_llm.invoke(prompt)
            return solution
            
        except Exception as e:
            return f"Error solving word problem: {e}"
    
    def calculate_statistics(self, numbers: list) -> Dict[str, float]:
        """Calculate basic statistics for a list of numbers"""
        try:
            numbers = [float(x) for x in numbers if str(x).replace('.', '').replace('-', '').isdigit()]
            
            if not numbers:
                return {"error": "No valid numbers provided"}
            
            stats = {
                "count": len(numbers),
                "sum": sum(numbers),
                "mean": np.mean(numbers),
                "median": np.median(numbers),
                "std_dev": np.std(numbers),
                "min": min(numbers),
                "max": max(numbers),
                "range": max(numbers) - min(numbers)
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Error calculating statistics: {e}"}
    
    def process_query(self, query: str) -> str:
        """Process a calculation query"""
        try:
            query_lower = query.lower()
            
            # Check if it's a direct mathematical expression
            if any(op in query for op in ['+', '-', '*', '/', '^', '=', 'sqrt', 'sin', 'cos', 'tan']):
                # Extract and evaluate expressions
                expressions = self.extract_calculation(query)
                
                if expressions:
                    results = []
                    for expr in expressions:
                        result = self.safe_eval(expr)
                        results.append(f"{expr} = {result}")
                    
                    return "**Calculation Results:**\n" + "\n".join(results)
            
            # Check for statistics keywords
            if any(word in query_lower for word in ['average', 'mean', 'median', 'statistics', 'std', 'deviation']):
                # Extract numbers from the query
                numbers = re.findall(r'-?\d+(?:\.\d+)?', query)
                
                if numbers:
                    stats = self.calculate_statistics(numbers)
                    
                    if "error" in stats:
                        return stats["error"]
                    
                    result = f"""**Statistical Analysis:**
- Count: {stats['count']}
- Sum: {stats['sum']:.2f}
- Mean: {stats['mean']:.2f}
- Median: {stats['median']:.2f}
- Standard Deviation: {stats['std_dev']:.2f}
- Minimum: {stats['min']:.2f}
- Maximum: {stats['max']:.2f}
- Range: {stats['range']:.2f}"""
                    
                    return result
            
            # Check if it's a word problem
            if any(word in query_lower for word in ['problem', 'calculate', 'find', 'how many', 'what is']):
                return self.solve_word_problem(query)
            
            # General mathematical query
            prompt = f"""Please help with the following mathematical query: "{query}"

If this involves calculations, please:
1. Show step-by-step work
2. Provide the final answer
3. Explain the approach used

If this is a mathematical concept question, please explain it clearly with examples.

Response:"""
            
            response = model_manager.azure_llm.invoke(prompt)
            # Only return the content if response is a message object
            if hasattr(response, 'content'):
                return response.content
            return response
            
        except Exception as e:
            st.error(f"Failed to process calculation query: {e}")
            return "Sorry, I couldn't process your calculation request at the moment."

# Global calculator agent instance
calculator_agent = CalculatorAgent()
