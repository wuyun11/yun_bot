"""
RAG 总结服务：用户提问 → 向量检索参考资料 → 与提问一并提交模型 → 模型总结回复。
"""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from agent_app.model.factory import chat_model
from agent_app.rag.vector_store import VectorStoreService
from agent_app.utils.prompt_loader import load_rag_summarize_prompt
from agent_app.utils.logger_handler import logger


def print_prompt(prompt):
    """调试用：在控制台打印 prompt 内容后原样返回。"""
    print("-" * 20)
    print(logger.debug(f"[prompt] {prompt.to_string()}"))
    print("-" * 20)
    return prompt


class RagSummarizeService:
    """基于向量检索与 LLM 的参考资料总结服务。"""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_summarize_prompt()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        """组装 prompt → 模型 → 字符串解析 的链。"""
        chain = self.prompt_template | RunnableLambda(print_prompt) | self.model | StrOutputParser()
        return chain

    def retriever_docs(self, query: str) -> list[Document]:
        """根据 query 检索参考资料文档列表。"""
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        """检索参考资料并调用模型生成总结回复。"""
        context_docs: list[Document] = self.retriever_docs(query)
        context_text = ""
        counter = 0
        for doc in context_docs:
            counter += 1
            context_text += f"参考资料{counter}:\n{doc.page_content}\n参考资料{counter}源数据:{doc.metadata}\n"
        return self.chain.invoke({
            "input": query,
            "context": context_text
        })


if __name__ == "__main__":
    rag_summarize_service = RagSummarizeService()
    result = rag_summarize_service.rag_summarize("首次使用扫地机器人需要做什么？")
    print(result)
