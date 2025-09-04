# tools/calc.py
"""
安全的计算器工具：使用 SymPy 解析数学表达式并求值。
示例支持：基础四则、幂、sqrt、sin/cos 等。


========================================================================================================
作用：封装 计算器工具。

功能：

使用 sympy 解析并安全计算数学表达式（支持加减乘除、幂、平方根、三角函数等）。

calculator(expression)：返回结果或报错信息。

get_tools()：返回 LangChain Tool 接口。

场景：让 Agent 在遇到算术/公式问题时能调用计算器获得准确结果。
"""

from typing import Union
from sympy import sympify
from langchain_core.tools import tool


@tool("calculator", return_direct=False)
def calculator(expression: str) -> Union[int, float, str]:
    """
    计算数学表达式并返回数值结果。

    Args:
        expression (str): 如 "2*(3+5) - sqrt(9)"、"sin(3.14/2)"

    Returns:
        Union[int, float, str]: 结果；若解析失败，返回错误信息字符串。
    """
    try:
        val = sympify(expression).evalf()
        # 尝试转成 float/int，便于下游使用
        try:
            f = float(val)
            if f.is_integer():
                return int(f)
            return f
        except Exception:
            return str(val)
    except Exception as e:
        return f"CalculatorError: {e}"


def get_tools():
    """返回可挂载到 Agent/Graph 的工具列表。"""
    return [calculator]
