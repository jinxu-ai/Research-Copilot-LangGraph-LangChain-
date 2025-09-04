# combine docsum and synth as a minimal pipeline

# chains/mini_pipeline.py
import os
from dotenv import load_dotenv

load_dotenv()

from tools.docsum import read_html
from tools.synth import synth_notes_tool

def run_html_to_notes(url: str, target_words: int = 180) -> str:
    # 1) 抓取 + 切分
    docs = read_html(url)
    chunks = [d.page_content for d in docs[:6]]  # 控制前 6 个分块，避免太长

    # 2) 综合为结构化笔记
    notes_json = synth_notes_tool.invoke({
        "chunks": chunks,
        "sources": [url],
        "topic": "自动网页摘要与要点",
        "target_words": target_words
    })
    return notes_json

if __name__ == "__main__":
    test_url = "https://langchain-ai.github.io/langgraph/"
    print(run_html_to_notes(test_url, target_words=180))


# python -m chains.mini_pipeline