"""
Filename: MetaGPT-Ewan/Ewan_tools/calculate_factorial.py
Created Date: Wednesday, December 17th 2025, 5:35 pm
Author: Ewan Su
"""
import math
from metagpt.tools.tool_registry import register_tool

@register_tool()
def calculate_factorial(n):
    """
    Calculate the factorial of a non-negative integer.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    return math.factorial(n)