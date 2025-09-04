# chains/research_graph.py
from __future__ import annotations
import os
import json
from typing import TypedDict, List, Dict, Any
from urllib.parse import urlparse
import logging

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 复用你已有工具
from tools.web import web_search       # Tool
from tools.docsum import read_html     # 函数，返回 Document[]
from tools.synth import synth_notes_tool  # Tool

# 配置日志
logger = logging.getLogger(__name__)

"""
使用已实现的工具：web_search、read_html、synth_notes_tool；
DeepSeek 作为 LLM；
含 decide 回环规则（条件边严格返回 path key）
"""

# -------------------- 状态定义 --------------------
class ResearchState(TypedDict, total=False):
    input: str                       # 用户问题
    plan: str                        # 规划说明
    queries: List[str]               # 搜索查询
    search_results: List[Dict[str, Any]]  # 搜索结果（title/url/snippet）
    selected_urls: List[str]         # 选中的若干 URL
    chunks: List[str]                # 读取到的文本分块（字符串）
    sources: List[str]               # 用于引用的 URL 列表
    notes_json: str                  # 结构化 JSON（字符串）
    notes: Dict[str, Any]            # 结构化 JSON（对象）
    output: str                      # Markdown 输出
    iter: int                        # 迭代计数
    need_more_evidence: bool         # 决策结果
    seen_urls: List[str]             # 已见过的证据 URL（用于"有无进展"判断）
    debug_decide: Dict[str, Any]     # 调试信息
    no_progress_count: int           # 连续无进展计数

def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.2,
        max_tokens=300
    )

# -------------------- decide iteration control --------------------
MAX_ITERS = 5  # 兜底的最大回环次数
MAX_NO_PROGRESS = 2  # 连续无进展的最大次数

def _safe_int(x, default=0):
    return x if isinstance(x, int) and x >= 0 else default

def _extract_domains(urls: List[str]) -> set[str]:
    doms: List[str] = []
    for u in urls:
        try:
            netloc = urlparse(u).netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            if netloc:
                doms.append(netloc)
        except Exception:
            continue
    return set(doms)

# -------------------- 各节点 --------------------
def plan(state: ResearchState) -> ResearchState:
    """生成简单计划 + 搜索词"""
    q = (state.get("input") or "").strip()
    llm = _llm()
    
    # 根据迭代次数调整搜索策略
    iteration = _safe_int(state.get("iter"), 0)
    if iteration == 0:
        # 第一轮：基础搜索
        prompt = (
            "You are a research planning assistant. Please generate 2-3 English search queries based on the user's question, "
            "covering definition, principles, and official documentation.\n"
            f"User question: {q}\n"
            "Return only one search query per line, without any explanation."
        )
    else:
        # 后续迭代：更具体的搜索
        prompt = (
            "You are a research planning assistant. Based on previous research, generate 2-3 more specific search queries "
            "to find additional evidence for the following question.\n"
            f"User question: {q}\n"
            "Return only one search query per line, without any explanation."
        )
    
    resp_lines = llm.invoke(prompt).content.strip().splitlines()
    # 基础兜底
    queries = [s.strip(" -•\t") for s in resp_lines if s.strip()] or [q, f"{q} official", f"{q} tutorial"]

    plan_text = (
        "Plan:\n"
        "1) Generate search queries and search\n"
        "2) Select 2-3 links from different domains\n"
        "3) Scrape and chunk content\n"
        "4) Synthesize into structured notes (summary/key_points/claims/open_questions)\n"
        "5) If evidence is insufficient, search again\n"
    )

    it0 = _safe_int(state.get("iter"), 0)
    # 初始化 seen_urls，保证 decide 能正常做"有无进展"判断
    return {
        "plan": plan_text, 
        "queries": queries, 
        "iter": it0, 
        "seen_urls": state.get("seen_urls") or [],
        "no_progress_count": state.get("no_progress_count") or 0
    }

def search(state: ResearchState) -> ResearchState:
    """调用 web_search 工具"""
    results: List[Dict[str, Any]] = []
    queries = state.get("queries") or []
    
    logger.info(f"Searching with queries: {queries}")
    
    for qi in queries[:3]:
        try:
            out = web_search.invoke({"query": qi, "k": 5})  # 返回 JSON 字符串或对象（取决于你实现）
            if isinstance(out, str):
                try:
                    out = json.loads(out)
                except Exception:
                    out = []
            if isinstance(out, list):
                results.extend(out)
        except Exception as e:
            logger.error(f"Search failed for query '{qi}': {e}")
            continue
    
    logger.info(f"Found {len(results)} search results")
    return {"search_results": results}

def select(state: ResearchState) -> ResearchState:
    """去重域名，选 2-3 个链接"""
    results = state.get("search_results") or []
    seen_domains = set()
    picked: List[str] = []
    
    logger.info(f"Raw search results: {json.dumps(results[:2], indent=2)}")  # 添加调试信息
    
    for r in results:
        # 尝试多种可能的URL字段名称
        url = (
            r.get("url") or 
            r.get("link") or 
            r.get("href") or 
            r.get("URL") or 
            r.get("LINK") or 
            r.get("HREF")
        )
        
        if not url:
            logger.warning(f"No URL found in result: {r}")
            continue
            
        # 确保URL是有效的HTTP/HTTPS URL
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid URL format: {url}")
            continue
            
        try:
            dom = urlparse(url).netloc
        except Exception as e:
            logger.error(f"URL parsing failed for {url}: {e}")
            continue
            
        if dom and (dom not in seen_domains):
            seen_domains.add(dom)
            picked.append(url)
            logger.info(f"Added URL: {url} (domain: {dom})")
        else:
            logger.info(f"Skipped URL (duplicate domain): {url}")
            
        if len(picked) >= 3:
            break
    
    logger.info(f"Selected URLs: {picked}")
    # sources 与 selected_urls 对齐
    return {"selected_urls": picked, "sources": picked}

def read(state: ResearchState) -> ResearchState:
    """抓取所选 URL 的内容并切分为 chunks"""
    urls = (state.get("selected_urls") or [])[:3]
    chunks: List[str] = []
    
    logger.info(f"Reading URLs: {urls}")
    
    for u in urls:
        try:
            docs = read_html(u)  # List[Document]
            chunks.extend([d.page_content for d in docs[:4]])  # 每站取前 4 段，防过长
            logger.info(f"Read {len(docs)} documents from {u}")
        except Exception as e:
            logger.error(f"Failed to read {u}: {e}")
            continue
    
    logger.info(f"Extracted {len(chunks)} chunks")
    return {"chunks": chunks}

def synthesize(state: ResearchState) -> ResearchState:
    """用 Pydantic 结构化输出综合结果"""
    chunks = (state.get("chunks") or [])[:12]
    sources = state.get("sources") or []
    
    logger.info(f"Synthesizing {len(chunks)} chunks from {len(sources)} sources")
    
    # tool 内部已做健壮解析，不满足格式会抛错；这里尽量兜底
    try:
        notes_json = synth_notes_tool.invoke({
            "chunks": chunks,
            "sources": sources,
            "topic": state.get("input", ""),
            "target_words": 200
        })
        notes = json.loads(notes_json)
        logger.info(f"Synthesis successful: {len(notes.get('claims', []))} claims")
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        notes_json = json.dumps({
            "summary": "Failed to synthesize notes", 
            "key_points": [], 
            "claims": [], 
            "open_questions": []
        }, ensure_ascii=False)
        notes = json.loads(notes_json)

    return {"notes_json": notes_json, "notes": notes}

def decide(state: ResearchState) -> ResearchState:
    """
    决策是否继续回环：
    - 完成条件：claims>=3 且 证据的去重域名>=2 且 每条 claim 至少 1 个 evidence
    - 进展判断：若无新增 URL（与 seen_urls 对比），则停止
    - 兜底：达到最大迭代次数或连续无证据时停止
    """
    it = _safe_int(state.get("iter"), 0)
    no_progress_count = _safe_int(state.get("no_progress_count"), 0)

    # 读取综合结果（上个节点 synthesize 写入）
    if isinstance(state.get("notes"), dict):
        notes_obj = state["notes"]
    else:
        try:
            notes_obj = json.loads(state.get("notes_json") or "{}")
        except Exception:
            notes_obj = {}

    claims = notes_obj.get("claims") or []
    # 展开所有 evidence_urls
    all_urls: List[str] = []
    for c in claims:
        urls = c.get("evidence_urls") or []
        if isinstance(urls, str):
            urls = [urls]
        all_urls.extend([u for u in urls if isinstance(u, str) and u.strip()])

    domains = _extract_domains(all_urls)

    # 基本完成条件
    has_enough_claims = len(claims) >= 3
    every_claim_has_evidence = all(len((c.get("evidence_urls") or [])) >= 1 for c in claims)
    has_diverse_sources = len(domains) >= 2
    meets_done = has_enough_claims and every_claim_has_evidence and has_diverse_sources

    # 进展检测：若无新增 URL 则认为没有进展
    seen_urls = set(state.get("seen_urls") or [])
    new_urls = set(all_urls) - seen_urls
    has_progress = len(new_urls) > 0

    # 更新无进展计数
    if not has_progress:
        new_no_progress_count = no_progress_count + 1
    else:
        new_no_progress_count = 0

    # 兜底上限
    hit_limit = (it + 1) >= MAX_ITERS
    hit_no_progress_limit = new_no_progress_count >= MAX_NO_PROGRESS

    # ------- 收敛策略（更"保守"）-------
    # 1) 达到完成条件 -> 停
    # 2) 到达上限 -> 停
    # 3) 连续无进展次数达到限制 -> 停
    # 4) 否则，只有在"有进展"时才继续
    if meets_done or hit_limit or hit_no_progress_limit:
        need_more = False
    else:
        # 第一轮允许没有证据也再试一次；后续必须有进展才继续
        need_more = (it == 0 and not all_urls) or has_progress

    next_seen = list(seen_urls.union(set(all_urls)))
    
    debug_info = {
        "iteration": it,
        "claims": len(claims),
        "domains": len(domains),
        "every_claim_has_evidence": every_claim_has_evidence,
        "has_progress": has_progress,
        "hit_limit": hit_limit,
        "hit_no_progress_limit": hit_no_progress_limit,
        "meets_done": meets_done,
        "need_more_evidence": need_more,
    }
    
    logger.info(f"Decision debug: {debug_info}")
    
    return {
        "need_more_evidence": need_more,
        "iter": it + 1,
        "seen_urls": next_seen,
        "no_progress_count": new_no_progress_count,
        "debug_decide": debug_info,
    }


def write(state: ResearchState) -> ResearchState:
    """将 notes 渲染为 Markdown"""
    n = state.get("notes", {}) or {}
    lines = ["# Research Copilot Report\n"]
    if n.get("summary"):
        lines += ["## Summary", n["summary"], ""]
    if n.get("key_points"):
        lines += ["## Key Points"] + [f"- {p}" for p in n["key_points"]] + [""]
    if n.get("claims"):
        lines += ["## Claims & Evidence"]
        for c in n["claims"]:
            evs = c.get("evidence_urls", []) or []
            ev_join = ", ".join(evs)
            lines.append(f"- {c.get('text','')}  \n  evidence: {ev_join}")
        lines.append("")
    if n.get("open_questions"):
        lines += ["## Open Questions"] + [f"- {q}" for q in n["open_questions"]] + [""]
    return {"output": "\n".join(lines)}

# --- 装配图 ---
def build_graph():
    g = StateGraph(ResearchState)

    # 避免与 state key 冲突：节点名使用 plan_node
    g.add_node("plan_node", plan)
    g.add_node("search", search)
    g.add_node("select", select)
    g.add_node("read", read)
    g.add_node("synthesize", synthesize)
    g.add_node("decide", decide)
    g.add_node("write", write)

    g.set_entry_point("plan_node")

    g.add_edge("plan_node", "search")
    g.add_edge("search", "select")
    g.add_edge("select", "read")
    g.add_edge("read", "synthesize")
    g.add_edge("synthesize", "decide")

    # 关键：让 decide 返回 path key -> 决定走向
    def after_decide(state: ResearchState) -> str:
        # 一律用布尔强制取值，避免 None 等"真值陷阱"
        need_more = bool(state.get("need_more_evidence"))
        logger.info(f"After decide: need_more_evidence = {need_more}")
        return "need_more" if need_more else "done"

    g.add_conditional_edges(
        "decide",
        after_decide,
        {
            "need_more": "search",
            "done": "write",
        },
    )

    g.add_edge("write", END)
    return g.compile()