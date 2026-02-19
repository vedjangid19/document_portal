import sys
import os
import uuid
from typing import List, Optional
from operator import itemgetter
from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType

from langchain_core.messages import BaseMessage
from langchain_community.vectorstores import FAISS #type: ignore
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


class ConversationalRAG:
    def __init__(self,session_id:str, retriever=None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.llm = self._load_llm()

            self.contextualize_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]

            if retriever is None:
                raise ValueError("Retriever can not be None.")
            
            self.retriever = retriever
            self._build_lcel_chain()
            self.log.info("ConversationalRAG intialized.", session_id=self.session_id)

        except Exception as e:
            self.log.error("Failed to initialize COnversationalRAG.", error=str(e))
            raise DocumentPortalException("Initialization error in ConversationalRAG", session_id=str(self.session_id))

    def load_retriever_from_faiss(self):
        try:
            pass
        except Exception as e:
            self.log.error("Failed to initialize COnversationalRAG.", error=str(e))
            raise DocumentPortalException("Initialization error in ConversationalRAG", session_id=str(self.session_id))

    def invoke(self, user_input:str, chat_history: Optional[List[BaseMessage]] = None) -> str:
        try:
            chat_history = chat_history or []
            payload = {"input": user_input, "chat_history": chat_history}

            answer = self.chain.invoke(payload)

            if not answer:
                self.log.warning("No answer generated.", user_input=user_input, session_id=self.session_id)

                return "no answer generated."
            
            self.log.info(
                "Chain invoke successfully.", session_id=self.session_id,
                user_input=user_input,
                answer_preview = answer[:150]
                )
            
            return answer
        except Exception as e:
            self.log.error("Failed to initialize COnversationalRAG.", error=str(e))
            raise DocumentPortalException("Initialization error in ConversationalRAG", session_id=str(self.session_id))

    def _load_llm(self):
        try:
            model_loader = ModelLoader()
            llm = model_loader.load_llm()

            if not llm:
                raise ValueError("LLM Could not be loaded.")
            
            self.log.info("LLM loaded successfully.", session_id=self.session_id)

            return llm
        
        except Exception as e:
            self.log.error("Failed to load LLM.", error=str(e))
            raise DocumentPortalException("LLM loading error in ConversationalRAG.", session_id=str(self.session_id))
    
    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    def _build_lcel_chain(self):
        try:
            # 1. Rewrite question using chat history
            question_rewriter = (
                {"input": itemgetter("input"), "chat_history": itemgetter("chat_history")}
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )
            
            # 2. Retrieved docs for rewritten question
            retrieve_docs = question_rewriter | self.retriever | self._format_docs

            # 3. feed context + original input + chat history into answer prompt
            self.chain = (
                {
                    "input": itemgetter("input"),
                    "context": retrieve_docs,
                    "chat_history": itemgetter("chat_history")
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )

            self.log.info("LCEL graph built successfully.", session_id = self.session_id)
        except Exception as e:
            self.log.error("Failed to build LCEL chain in ConversationalRAG.", error=str(e))
            raise DocumentPortalException("Failed to build LCEL chain in ConversationalRAG", session_id=str(self.session_id))
