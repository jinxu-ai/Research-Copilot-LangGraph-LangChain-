# app/run_graph.py
import argparse
import logging
from chains.research_graph import build_graph

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--q", required=True, help="research question")
    args = parser.parse_args()

    app = build_graph()
    # 初始状态
    state = {"input": args.q}

    try:
        # 增加递归限制并提供更详细的配置
        result = app.invoke(state, config={"recursion_limit": 20})  # 增加递归限制
        print(result.get("output") or result)
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        # 输出当前状态以便调试
        print(f"Error: {e}")
        print("Current state:", state)

if __name__ == "__main__":
    main()