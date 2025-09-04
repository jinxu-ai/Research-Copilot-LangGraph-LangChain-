# tools/__init__.py
"""
作用：工具集合的入口。

功能：
- 从 web.py、local_rag.py、calc.py、docsum.py、synth.py 各自导入 get_tools()
- 提供 get_all_tools()：一次性返回所有工具，形成一个工具列表。

场景：
在 Agent/Graph 里，只需要 from tools import get_all_tools 就能拿到所有工具。
"""

from .web import get_tools as web_tools
from .local_rag import get_tools as rag_tools
from .calc import get_tools as calc_tools
from .docsum import get_tools as docsum_tools
from .synth import get_tools as synth_tools


def get_all_tools():
    """一次性拿到所有工具（列表拼接）。"""
    return (
        web_tools()
        + rag_tools()
        + calc_tools()
        + docsum_tools()
        + synth_tools()
    )
