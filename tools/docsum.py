# tools/docsum.py
"""
文档读取 + 切分 + 摘要（支持 PDF / HTML）
- read_pdf(path): 读取 PDF -> 切分 -> 返回 Document 列表
- read_html(url): 抓取 HTML -> 纯文本提取 -> 切分 -> 返回 Document 列表
- summarize_docs(docs, summary_words, chunk_words): 用 LangChain 的 map_reduce 摘要链生成摘要，支持长度控制
- summarize_pdf(path, summary_words, chunk_words): PDF 一步到位生成摘要
- summarize_html(url, summary_words, chunk_words): HTML 一步到位生成摘要
"""

import os
import re
import requests
from typing import List, Optional
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# ------------no logging history---------------
# import logging
# logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

# --------- 基础：文本切分器 ----------
_TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100, separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "]
)

def _llm(max_tokens: Optional[int] = None):
    """DeepSeek 的 Chat LLM（兼容 OpenAI 协议）。"""
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.2,
        # 辅助限长：可选 max_tokens（不同版本也可能叫 max_completion_tokens）
        max_tokens=max_tokens,
    )

# --------- 读取 PDF ----------
def read_pdf(path: str) -> List[Document]:
    loader = PyPDFLoader(path)
    docs = loader.load()
    return _TEXT_SPLITTER.split_documents(docs)

# --------- 读取 HTML ----------
_HTML_TAG_RE = re.compile(r"<[^>]+>")

def _html_to_text(html: str) -> str:
    # 粗粒度去标签 + 压缩空白（不额外引入 bs4，够用）
    text = _HTML_TAG_RE.sub(" ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def read_html(url: str) -> List[Document]:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    text = _html_to_text(resp.text)
    docs = [Document(page_content=text, metadata={"source": url})]
    return _TEXT_SPLITTER.split_documents(docs)

# --------- 摘要（带字数控制） ----------
def summarize_docs(
    docs: List[Document],
    summary_words: int = 150,
    chunk_words: int = 60,
    llm_max_tokens: Optional[int] = None,
) -> str:
    """
    使用 map_reduce 方式做长文摘要（LangChain 0.2+ 标准调用），支持字数控制。

    Args:
        docs: Document 列表（已切分）
        summary_words: 最终摘要字数上限（中文“字数”）
        chunk_words: 每个分块摘要字数上限
        llm_max_tokens: 可选，硬限制生成 token（兜底防溢出）
    """
    llm = _llm(max_tokens=llm_max_tokens)

    # map 阶段提示词：对每个分块做短摘要
    map_prompt = PromptTemplate.from_template(
        "请针对下列内容生成要点摘要，使用中文，"
        "长度最多 {chunk_words} 字，省略赘述，保留关键信息与数字。\n\n"
        "文本：\n{text}\n\n"
        "要求：\n- 不要扩写或发挥\n- 不要加入未出现的信息\n- 直接给出摘要"
    )

    # reduce 阶段提示词：合并多个分块摘要为一个整体摘要
    combine_prompt = PromptTemplate.from_template(
        "下面是多个分块摘要，请合并为一个整体摘要，使用中文：\n\n"
        "{text}\n\n"
        "要求：\n- 长度最多 {summary_words} 字\n- 保留核心结论与数字\n- 去重并合并同类项\n- 不要加入原文没有的信息\n\n"
        "现在给出最终摘要："
    )

    chain = load_summarize_chain(
        llm,
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        verbose=False,
    )

    # 新写法：invoke，并显式传入 input_documents + 自定义变量
    result = chain.invoke({
        "input_documents": docs,
        "chunk_words": chunk_words,
        "summary_words": summary_words,
    })

    if isinstance(result, str):
        return result.strip()
    return (result.get("output_text") or result.get("text") or str(result)).strip()

# ------ 封装为 Tool：一步到位（加入可调字数参数） -------
class SummarizePDFArgs(BaseModel):
    path: str = Field(..., description="本地 PDF 路径")
    summary_words: int = Field(150, ge=30, le=2000, description="最终摘要字数上限")
    chunk_words: int = Field(60, ge=30, le=600, description="分块摘要字数上限")
    llm_max_tokens: int | None = Field(None, description="可选：生成 token 上限（兜底防溢出）")

@tool("summarize_pdf", args_schema=SummarizePDFArgs)
def summarize_pdf(
    path: str,
    summary_words: int = 150,
    chunk_words: int = 60,
    llm_max_tokens: Optional[int] = None,
) -> str:
    """对 PDF 生成摘要：传入本地 PDF 路径，并可控制摘要字数。"""
    docs = read_pdf(path)
    return summarize_docs(
        docs,
        summary_words=summary_words,
        chunk_words=chunk_words,
        llm_max_tokens=llm_max_tokens,
    )

class SummarizeHTMLArgs(BaseModel):
    url: str = Field(..., description="网页 URL")
    summary_words: int = Field(150, ge=30, le=2000, description="最终摘要字数上限")
    chunk_words: int = Field(60, ge=30, le=600, description="分块摘要字数上限")
    llm_max_tokens: int | None = Field(None, description="可选：生成 token 上限（兜底防溢出）")

@tool("summarize_html", args_schema=SummarizeHTMLArgs)
def summarize_html(
    url: str,
    summary_words: int = 150,
    chunk_words: int = 60,
    llm_max_tokens: Optional[int] = None,
) -> str:
    """对网页生成摘要：传入 URL，并可控制摘要字数。"""
    docs = read_html(url)
    return summarize_docs(
        docs,
        summary_words=summary_words,
        chunk_words=chunk_words,
        llm_max_tokens=llm_max_tokens,
    )

def get_tools():
    return [summarize_pdf, summarize_html]


# python -c "from tools.docsum import summarize_pdf; print(summarize_pdf.invoke({'path': r'D:\ResearchCopilot\Research-Copilot-LangGraph-LangChain-\data\G-Memory —— Tracing Hierarchical Memory for Multi-Agent Systems.pdf', 'summary_words': 200, 'chunk_words': 80, 'llm_max_tokens': 300})[:800])"
# python -c "from tools.docsum import summarize_html; print(summarize_html.invoke({'url': 'https://python.langchain.com', 'summary_words': 180, 'chunk_words': 70}))"


# 想更短：把 summary_words 和 chunk_words 调小，比如 120 / 50
# 想更长：把它们调大，并（可选）同步调大 llm_max_tokens（比如 512）