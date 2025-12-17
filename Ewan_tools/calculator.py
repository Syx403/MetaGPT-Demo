"""
Filename: MetaGPT-Ewan/Ewan_tools/calculator.py
Created Date: Wednesday, December 17th 2025, 5:37 pm
Author: Ewan Su
"""
import math
from metagpt.tools.tool_registry import register_tool

# The tag "math" is used to categorize the tool and the include_functions list specifies the functions to include, which makes `DataInterpreter` select and understand the tool.
@register_tool(tags=["math"], include_functions=["__init__", "add", "subtract", "multiply", "divide", "factorial"])
class Calculator:
   """
   A simple calculator tool that performs basic arithmetic operations and calculates factorials.
   """

   @staticmethod
   def add(a, b):
       """
       Calculate the sum of two numbers.
       """
       return a + b

   @staticmethod
   def subtract(a, b):
       """
       Calculate the difference of two numbers.
       """
       return a - b

   @staticmethod
   def multiply(a, b):
       """
       Calculate the product of two numbers.
       """
       return a * b

   @staticmethod
   def divide(a, b):
       """
       Calculate the quotient of two numbers.
       """
       if b == 0:
           return "Error: Division by zero"
       else:
           return a / b

   @staticmethod
   def factorial(n):
       """
       Calculate the factorial of a non-negative integer.
       """
       if n < 0:
           raise ValueError("Input must be a non-negative integer")
       return math.factorial(n)