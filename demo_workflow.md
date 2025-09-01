# Research Copilot 工作计划（版本 A）

本计划旨在快速完成一个基于 **LangChain + LangGraph** 的 Research Copilot Demo，覆盖大部分核心技术点，适合作为求职作品展示。

---

## 第 0 步：项目初始化
- 在 GitHub 创建仓库并 clone 到本地。  
- 按结构建文件夹：`app/`, `chains/`, `tools/`, `data/`, `tests/`, `docs/`。  
- 在每个文件夹下写 `README.md` 说明用途。  
- 创建 `.gitignore`，排除 `.venv/`、`.env`、`__pycache__/` 等。  
- 提交并推送第一次 commit。  

---

## 第 1 步：环境配置
- 创建 Python 虚拟环境：  
  ```bash
  python -m venv .venv
  ```
- 安装依赖：  
  ```bash
  pip install -r requirements.txt
  ```
- 配置 VS Code 使用 `.venv` 解释器。  
- 在项目根目录写 `.env` 文件，保存 API Key（OpenAI / DeepSeek）。  
- 验证：写一个 `test_env.py`，用 `dotenv` 加载 `.env`，确认 key 可读取。  

---

## 第 2 步：API & SDK 验证
- 使用 `openai` SDK 测试 OpenAI / DeepSeek 是否可用。  
- 验证 `langchain_openai.ChatOpenAI` 能正常调用。  
- 验证 `langgraph.StateGraph` 能构建最小图。  
- 输出 “环境 OK” 确认信息。  

---

## 第 3 步：最小 Agent 流程
- 在 `chains/` 写 `deepseek_chain.py`：封装一个简单的对话链（输入问题 → 输出答案）。  
- 在 `app/main.py` 调用该 chain，确保可以运行：  
  ```bash
  python app/main.py
  ```
- 确认整个 pipeline 可跑通。  

---

## 第 4 步：工具集成
- 在 `tools/` 下实现几个基础工具：  
  - **Web 搜索工具**（requests / API）  
  - **本地文档检索工具**（faiss / langchain text splitters）  
  - **计算器工具**（eval / sympy）  
- 用 LangChain 的 `Tool` 接口包装这些工具。  

---

## 第 5 步：Agent 架构（LangGraph）
- 定义 **状态机**：  
  - `plan`（规划）  
  - `search`（调用工具）  
  - `select`（选择信息）  
  - `read`（阅读/抽取）  
  - `synthesize`（综合）  
  - `decide`（输出/迭代）  
- 在 `graph/` 下写 `copilot_graph.py`，用 LangGraph 构建上述流程并编译。  

---

## 第 6 步：对话循环 & Memory
- 加入对话记忆（短期/长期）。  
- 测试连续问答时能保持上下文。  
- 在 `tests/` 写测试用例验证记忆功能。  

---

## 第 7 步：前端接口
- 用 `streamlit` 写一个最小 UI。  
- 输入框输入问题 → 后台调用 LangGraph → 输出显示在网页上。  

---

## 第 8 步：文档与总结
- 在 `docs/` 写使用说明：如何安装、如何运行、如何扩展。  
- 在 `README.md` 写项目介绍、架构图、示例输入输出。  
- 最终提交并推送到 GitHub，形成完整展示项目。  

---

✅ 至此，一个完整的 Research Copilot Demo 即可完成。
