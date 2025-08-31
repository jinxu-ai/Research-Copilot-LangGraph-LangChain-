# Research-Copilot-LangGraph-LangChain-
在 7–10 天内完成一个“Research Copilot”，用 LangGraph 编排实现 Agentic System（规划→工具→反思→记忆→迭代），并在每个节点使用 LangChain 原语（Loaders、Splitters、Summarize、LCEL、Parsers、Retrievers、Callbacks、Streaming），展示二者的完整技术栈。


阶段与步骤
0) 环境与骨架

做什么：初始化工程、依赖、目录与密钥
怎么做：

创建目录结构（app/, chains/, graph/, tools/, eval/, notes/, data/, configs/）。

安装依赖：

pip install "langchain>=0.2,<0.3" "langchain-community>=0.2,<0.3" \
            "langgraph>=0.1,<0.2" "langchain-openai>=0.1,<0.2" \
            "pydantic>=2,<3" "tiktoken" "streamlit" \
            "unstructured[pdf]" "pypdf" "faiss-cpu"


.env 配置 OPENAI_API_KEY。
验收：import langchain, langgraph 正常。

1) LLM 客户端与状态模型

做什么：统一 LLM 接口；定义 Graph 状态与 Pydantic 模型
怎么做：

configs/llm.py：get_llm("gpt-4o-mini")。

graph/state.py：定义 Source、Claim、Notes（Pydantic）、GraphState（TypedDict）。
验收：能成功导入模型，Notes().model_dump() 正常。

2) LCEL 链：plan & queries

做什么：将问题转为原子计划，再生成检索式
怎么做：

plan_chain：ChatPromptTemplate | llm | JsonOutputParser。

gen_queries_chain：输入 question+plan，输出 JSON list[str]。
验收：返回干净的 JSON 列表。

3) Web 搜索工具 & 来源筛选

做什么：搜索→候选→去重/打分→Top-N
怎么做：

tools/web_search.py：伪实现，后接 Tavily/SerpAPI。

rank_and_select：LLM 打分，优先 PDF，多样性。
验收：能输出 Top-5 selected_sources。

4) 文档读取 + 切分 + 摘要

做什么：支持 PDF/HTML，切分，Map-Reduce 摘要
怎么做：

read_pdf：PyPDFLoader → RecursiveCharacterTextSplitter → load_summarize_chain("map_reduce")。

read_html：requests 抓正文+splitter。
验收：能得到 chunks≤50，摘要字符串正常。

5) 综合与结构化输出

做什么：chunks+sources → summary+Notes(JSON)
怎么做：

synth_chain：PydanticOutputParser(Notes)，强约束输出。

Prompt：必须生成 key_points、claims(带 evidence_urls)、open_questions。
验收：Pydantic 校验通过，claims 引文非空。

6) LangGraph 编排与循环

做什么：节点串成图，decide 决定是否回环
怎么做：

节点：plan → search → select → read → synthesize → decide → write

decide 用规则：claims<3 或 引文不足 或 域名<2 → need_more_evidence=True
验收：完整 state 返回，能触发一次迭代。

7) 向量检索与上下文压缩

做什么：chunks 入向量库，二次筛选
怎么做：

用 FAISS.from_documents 建库，retriever = ContextualCompressionRetriever。

用问题检索，替换 state["chunks"]。
验收：chunks 更短更相关；对比时 citations/coverage 提升。

8) 工具安全与 Guardrails

做什么：安全执行 Python 代码
怎么做：

python_exec：白名单模块(math/statistics)，禁止 IO/网络，超时。
验收：正常计算成功，违规代码报错。

9) Streaming 与回调

做什么：展示流式输出与成本/延迟统计
怎么做：

synth_chain 设置 streaming=True。

回调记录 tokens、latency → 写入 state["artifacts"]["metrics"]。
验收：日志输出流式内容，metrics 有记录。

10) 评测与对比实验

做什么：评估 baseline vs iterate vs retriever
怎么做：

eval/dataset.jsonl：10–20 问题+参考要点。

eval/run_eval.py：跑三种模式，记录 Coverage、Citations/claim、Latency、Cost。

eval/report.md：写实验表格。
验收：报告完成，指标有对比。

11) UI 与导出

做什么：可视化输入输出，导出 md
怎么做：

Streamlit ui.py：输入问题，按钮 Run，展示 summary、notes(JSON)、artifacts.markdown。

write_markdown：渲染 Notes 为 md 文件。
验收：UI 可运行，md 文件可下载。

12) 观测与文档打磨

做什么：Tracing 截图，README，架构图
怎么做：

开启 LangSmith tracing（可选），截 workflow。

README 写：目标、架构图、覆盖点清单、运行方法、评测结果、局限与下一步。
验收：README 完整，含图与表。
