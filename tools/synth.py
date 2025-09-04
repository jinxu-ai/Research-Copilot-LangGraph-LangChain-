# tools/synth.py
"""
将若干 chunks（文本分块）与 sources（来源 URL）综合为结构化笔记 Notes(JSON)：
- 字段：summary, key_points[], claims[{text, evidence_urls[]}], open_questions[]
- 使用 PydanticOutputParser 做强约束输出，自动校验 claims.evidence_urls 非空
- 提供 Tool：synth_notes
"""

from __future__ import annotations

import os
import json
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, AnyUrl, model_validator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.tools import tool

load_dotenv()

# ---------------- Pydantic 模型（强约束） ----------------

class Claim(BaseModel):
    text: str = Field(..., description="可验证的陈述")
    evidence_urls: List[AnyUrl] = Field(..., description="支持该陈述的引用 URL 列表，至少 1 条")

    @model_validator(mode="after")
    def check_evidence(self):
        if not self.evidence_urls:
            raise ValueError("each claim must include at least one evidence url")
        return self


class Notes(BaseModel):
    summary: str = Field(..., description="对主题的简要综合总结")
    key_points: List[str] = Field(..., description="要点列表（3-7条）")
    claims: List[Claim] = Field(..., description="带有可验证引用的陈述列表")
    open_questions: List[str] = Field(..., description="仍未解决/需要进一步研究的问题")

# 方便外部做类型提示
NotesDict = dict

# ---------------- LLM 工厂（DeepSeek） ----------------

def _llm(max_tokens: Optional[int] = 512):
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.2,
        max_tokens=max_tokens,  # 兜底限长
    )

# ---------------- 综合链（Prompt + Parser） ----------------

def _build_prompt(parser: PydanticOutputParser) -> ChatPromptTemplate:
    """
    约束模型必须输出 parser 指定的 JSON 结构。
    输入变量：
      - topic: 本次综合的主题描述（可空）
      - chunks: 文本分块列表（用于综合）
      - sources: URL 列表（用于引用）
      - target_words: 希望的 summary 最大字数
      - format_instructions: 结构化输出的格式说明（已做花括号转义）
    """
    # 1) 获取格式说明，并转义花括号，避免被 PromptTemplate 当做变量
    raw_fi = parser.get_format_instructions()
    fi_escaped = raw_fi.replace("{", "{{").replace("}", "}}")

    system = (
        "你是一位严谨的研究助理。请基于提供的文本分块（chunks）和来源（sources）"
        "综合出结构化的研究笔记。严格遵守格式约束与事实，不要编造引用。"
    )

    # 2) target_words 使用单花括号 {target_words} 让其参与变量替换
    human = (
        "主题（可选）：{topic}\n\n"
        "【材料 - chunks】（可能被截断，需去重、合并同类项）：\n{chunks}\n\n"
        "【来源 - sources】（可选，用于引用）：\n{sources}\n\n"
        "请完成：\n"
        "- 生成 JSON，字段：summary、key_points、claims(带 evidence_urls)、open_questions\n"
        "- summary 最多约 {target_words} 字；key_points 3-7 条；claims 每条必须包含至少 1 个 evidence_urls\n"
        "- 只使用给定 sources 或 chunks 中可推断的链接作为 evidence，不要虚构\n\n"
        "必须严格输出以下格式：\n"
        "{format_instructions}"
    )

    # 3) 用 partial 方式把已转义的 format_instructions 注入（避免再次作为变量参与替换）
    prompt = ChatPromptTemplate.from_messages(
        [("system", system), ("human", human)]
    ).partial(format_instructions=fi_escaped)

    return prompt

def synthesize_notes(
    chunks: List[str] | List[Document],
    sources: List[str] | None = None,
    topic: str | None = None,
    target_words: int = 200,
) -> Notes:
    """
    综合 chunks + sources，返回 Notes（Pydantic 对象）。
    - chunks: 文本分块（str 或 Document 均可）
    - sources: URL 列表
    - topic: 主题（可选）
    - target_words: summary 最大字数（建议 150~300）
    """
    # 统一把 Document 转为字符串
    _chunks: List[str] = []
    for c in chunks:
        if isinstance(c, Document):
            _chunks.append(c.page_content)
        else:
            _chunks.append(str(c))

    _sources = sources or []

    parser = PydanticOutputParser(pydantic_object=Notes)
    prompt = _build_prompt(parser)
    llm = _llm()

    chain = prompt | llm | parser  # LCEL：提示 -> 模型 -> 结构化解析

    result: Notes = chain.invoke(
        {
            "topic": topic or "",
            "chunks": "\n\n---\n\n".join(_chunks[:30]),  # 防止一次性喂太多
            "sources": "\n".join(_sources[:30]),
            "target_words": target_words,
        }
    )
    return result

# ---------------- Tool 封装（可在 Graph/Agent 中直接用） ----------------

class SynthArgs(BaseModel):
    chunks: List[str] = Field(..., description="文本分块列表")
    sources: List[str] = Field(default_factory=list, description="可选：引用 URL 列表")
    topic: str | None = Field(default=None, description="可选：主题说明")
    target_words: int = Field(200, ge=80, le=600, description="summary 目标最大字数")

def _convert_anyurl_to_str(obj):
    """递归转换对象中的 AnyUrl 为字符串，以便 JSON 序列化"""
    if isinstance(obj, list):
        return [_convert_anyurl_to_str(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _convert_anyurl_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, AnyUrl):
        return str(obj)
    elif hasattr(obj, 'model_dump'):
        # 处理 Pydantic 模型对象
        return _convert_anyurl_to_str(obj.model_dump())
    else:
        return obj

@tool("synth_notes", args_schema=SynthArgs)
def synth_notes_tool(chunks: List[str], sources: List[str] | None = None, topic: str | None = None, target_words: int = 200) -> str:
    """
    综合输出 Notes(JSON 字符串)。用于在 Agent/Graph 中作为工具调用。
    """
    notes = synthesize_notes(chunks=chunks, sources=sources or [], topic=topic, target_words=target_words)
    
    # 转换 AnyUrl 为字符串以便 JSON 序列化
    notes_dict = _convert_anyurl_to_str(notes)
    
    return json.dumps(notes_dict, indent=2, ensure_ascii=False)

def get_tools():
    return [synth_notes_tool]