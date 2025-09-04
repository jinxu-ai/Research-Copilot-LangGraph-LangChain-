# tools/local_rag.py
"""
基于 FAISS 的本地文档检索工具。
- 启动时从 data/ 目录加载文本/PDF（可扩展）
- 使用 RecursiveCharacterTextSplitter 切块
- 存入 FAISS 向量库
- 提供 retriever 工具：local_search(query, k=4)

支持多种Embedding选项：
1. OpenAI Embedding (需要OPENAI_API_KEY)
2. HuggingFace本地模型 (无需API密钥，但需要下载模型)
3. 其他兼容OpenAI API的Embedding服务
"""

import os
import time
from typing import List, Optional
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_INDEX = None  # type: Optional[FAISS]
_LAST_INDEX_TIME = 0
_INDEX_REFRESH_INTERVAL = 300  # 5分钟索引刷新间隔

def _load_documents() -> List[Document]:
    """从 data/ 目录加载 .txt 与 .pdf 文档。"""
    docs: List[Document] = []
    if not os.path.isdir(_DATA_DIR):
        logger.warning(f"数据目录不存在: {_DATA_DIR}")
        return docs

    supported_extensions = ('.txt', '.pdf')
    file_count = 0
    
    for name in os.listdir(_DATA_DIR):
        path = os.path.join(_DATA_DIR, name)
        if os.path.isfile(path) and name.lower().endswith(supported_extensions):
            try:
                if name.lower().endswith(".txt"):
                    loader = TextLoader(path, autodetect_encoding=True)
                    file_docs = loader.load()
                    docs.extend(file_docs)
                    file_count += 1
                    logger.info(f"成功加载文本文件: {name}")
                elif name.lower().endswith(".pdf"):
                    loader = PyPDFLoader(path)
                    file_docs = loader.load()
                    docs.extend(file_docs)
                    file_count += 1
                    logger.info(f"成功加载PDF文件: {name}")
            except Exception as e:
                logger.error(f"加载文件失败 {name}: {e}")
    
    logger.info(f"共加载 {file_count} 个文档，{len(docs)} 个文档片段")
    return docs

def _get_embeddings():
    """获取Embedding模型，支持多种选项，优先使用本地模型"""
    # 选项1: 优先使用HuggingFace本地模型 (无需API密钥)
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        # 使用轻量级模型
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        logger.info(f"使用HuggingFace本地模型: {model_name}")
        return embeddings
    except ImportError:
        logger.error("未安装HuggingFace相关依赖，请运行: pip install sentence-transformers")
    except Exception as e:
        logger.error(f"HuggingFace Embedding初始化失败: {e}")
    
    # 选项2: 使用OpenAI Embedding (需要OPENAI_API_KEY)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            # 测试embedding连接
            test_embedding = embeddings.embed_query("test")
            if not test_embedding or len(test_embedding) == 0:
                raise ValueError("OpenAI Embedding测试失败")
            logger.info("使用OpenAI Embedding")
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI Embedding初始化失败: {e}")
    
    # 选项3: 其他兼容OpenAI API的服务
    other_api_key = os.getenv("OTHER_EMBEDDING_API_KEY")
    other_base_url = os.getenv("OTHER_EMBEDDING_BASE_URL")
    if other_api_key and other_base_url:
        try:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",  # 或其他模型名
                api_key=other_api_key,
                base_url=other_base_url,
            )
            test_embedding = embeddings.embed_query("test")
            if not test_embedding or len(test_embedding) == 0:
                raise ValueError("其他Embedding服务测试失败")
            logger.info(f"使用其他Embedding服务: {other_base_url}")
            return embeddings
        except Exception as e:
            logger.error(f"其他Embedding服务初始化失败: {e}")
    
    # 所有选项都失败
    raise RuntimeError("没有可用的Embedding服务，请配置至少一种Embedding选项")

def _build_index() -> FAISS:
    """加载+切块文档并构建 FAISS 索引（内存级）。"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=80,
        separators=["\n\n", "\n", "。", "！", "？", "．", "!", "?", " ", ""]
    )
    docs = _load_documents()
    
    if not docs:
        # 构造一个兜底文档，避免空索引
        logger.warning("未找到任何文档，创建默认文档")
        docs = [Document(page_content="No local documents found in data/.")]
    
    splits = text_splitter.split_documents(docs)
    logger.info(f"文档分割为 {len(splits)} 个块")

    # 获取Embedding模型
    embeddings = _get_embeddings()
    
    return FAISS.from_documents(splits, embeddings)

def _get_index() -> FAISS:
    """懒加载索引（首次调用时构建），支持定期刷新。"""
    global _INDEX, _LAST_INDEX_TIME
    
    current_time = time.time()
    
    # 检查是否需要刷新索引（首次加载或超过刷新间隔）
    if _INDEX is None or (current_time - _LAST_INDEX_TIME > _INDEX_REFRESH_INTERVAL):
        logger.info("构建或刷新FAISS索引")
        _INDEX = _build_index()
        _LAST_INDEX_TIME = current_time
    else:
        logger.info("使用现有FAISS索引")
    
    return _INDEX

@tool("local_search", return_direct=False)
def local_search(query: str, k: int = 4) -> List[str]:
    """
    在本地文档中检索相似片段。

    Args:
        query (str): 查询文本。
        k (int): 返回片段数量（默认 4）。

    Returns:
        List[str]: 命中的文档片段文本。
    """
    try:
        index = _get_index()
        docs = index.similarity_search(query, k=k)
        
        results = []
        for i, d in enumerate(docs):
            # 保留更多上下文，但限制总长度
            content = d.page_content
            if len(content) > 1200:
                # 智能截断：尝试在句子边界处截断
                if "." in content[1000:1200]:
                    cutoff = content.rfind(".", 1000, 1200) + 1
                    content = content[:cutoff] + " [截断...]"
                else:
                    content = content[:1200] + " [截断...]"
            
            # 添加来源信息（如果有）
            source_info = f" [来源: {d.metadata.get('source', '未知')}]" if d.metadata.get('source') else ""
            results.append(f"{content}{source_info}")
        
        logger.info(f"检索查询: '{query}'，返回 {len(results)} 个结果")
        return results
        
    except Exception as e:
        logger.error(f"检索过程中发生错误: {e}")
        return [f"检索失败: {str(e)}"]

def get_tools():
    """返回可挂载到 Agent/Graph 的工具列表。"""
    return [local_search]

def refresh_index():
    """强制刷新索引（当数据目录有更新时调用）"""
    global _INDEX, _LAST_INDEX_TIME
    _INDEX = None
    _LAST_INDEX_TIME = 0
    logger.info("索引刷新已安排，将在下次查询时重建")