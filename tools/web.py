# tools/web.py
"""
Web 搜索工具（DuckDuckGo），无需 API Key。
提供两个函数：
- web_search(query, max_results=5): 返回若干条搜索结果（title, href, snippet）
- get_tools(): 返回 LangChain Tool 列表，供 Agent/Graph 挂载

依赖：
    pip install duckduckgo-search

========================================================================================================
作用：封装 Web 搜索工具。

使用 duckduckgo-search 库，调用 DuckDuckGo 的搜索接口，无需 API Key。

提供函数：

web_search(query, max_results)：返回若干条搜索结果（标题、链接、摘要）。

get_tools()：返回符合 LangChain Tool 接口的封装，用于在 Agent/Graph 中挂载。

场景：当 Agent 需要联网查资料时调用。
"""

from typing import List, Dict
from duckduckgo_search import DDGS
from langchain_core.tools import tool


@tool("web_search", return_direct=False)
def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    进行 Web 搜索并返回简要结果。

    Args:
        query (str): 搜索关键词。
        max_results (int): 返回的条数（默认 5）。

    Returns:
        List[Dict[str, str]]: 每条包含 {"title","href","snippet"}。
    """
    results: List[Dict[str, str]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "href": r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    return results


def get_tools():
    """返回可挂载到 Agent/Graph 的工具列表。"""
    return [web_search]
