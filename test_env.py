# step 2.1 test openai SDK 
# 验证 DeepSeek 官方 API（OpenAI 协议兼容） 是否能直接工作。
# 这是最底层的调用测试，保证 “SDK 能连上 DeepSeek 并返回结果”。
# 相当于在做连通性测试，确保 API Key + 端点没问题。
# Please install OpenAI SDK first: `pip3 install openai`
import os 
from dotenv import load_dotenv


load_dotenv()


from openai import OpenAI

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello, Who are you?"},
    ],
    stream=False
)

print(response.choices[0].message.content)


# step 2.2 verify langchain_openai.ChatOpenAI 
# 验证 LangChain 的 ChatOpenAI 封装 能否通过 DeepSeek 的 OpenAI 协议端点正常工作。
# 这是为后续构建 LangGraph + Chain + Agent 做准备。只有 LangChain 调用确认可用，后续的 Agent 才能跑。
# 相当于在做框架集成测试，确保 DeepSeek 能嵌入到 LangChain 的生态里。
# 打印输出，验证整个调用链（API Key → DeepSeek 服务 → LangChain 封装）是否正常。



print("OPENAI-API-Key: ", os.getenv("OPENAI_API_KEY"))
print("DEEPSEEK-API-Key: ", os.getenv("DEEPSEEK_API_KEY"))

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph


print("LangChain & LangGraph imported successfully!")

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0,
)

# 向模型发送请求，输入是 "Reply with exactly: OK"
resp = llm.invoke("Reply with exactly: OK")
print("ChatOpenAI via DeepSeek:", resp.content)  # result: OK




# step 2.3 verify langgraph.StateGraph to construct the min-graph
from typing import TypedDict
from langgraph.graph import StateGraph, END

class MiniState(TypedDict):
    input: str
    output: str

def echo_node(state: MiniState) -> MiniState:
    return {"output": f"ECHO: {state['input']}"}


# 构建state图： 

#g = StateGraph(MiniState) → 创建一个有向图，要求状态遵循 MiniState 格式。
g = StateGraph(MiniState)

# g.add_node("echo", echo_node) → 添加一个名为 "echo" 的节点，绑定到 echo_node 函数。
g.add_node("echo", echo_node)

# g.set_entry_point("echo") → 设置 "echo" 为入口节点。
g.set_entry_point("echo")

# g.add_edge("echo", END) → 指定 "echo" 节点执行完后直接进入结束节点 END。
g.add_edge("echo", END)

# app = g.compile() → 将图编译成一个可执行的应用。
app = g.compile()


# 执行图，从入口节点开始运行。
result = app.invoke({"input": "hello"})
print("LangGraph:", result["output"])  # 期望：ECHO: hello



