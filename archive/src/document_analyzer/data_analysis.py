import os
import sys
from model.models import *
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser
# from langchain.output_parsers import OutputFixingParser
from langchain_classic.output_parsers import OutputFixingParser #type: ignore
from prompt.prompt_library import PROMPT_REGISTRY


class DocumentAnalyzer:
    """A class to analyze documents using various language models and prompts.
    Automatically logs all actions and supports dynamic model and prompt selection.
    """

    def __init__(self):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.model_loader = ModelLoader()
            self.llm = self.model_loader.load_llm()
            
            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(llm=self.llm, parser=self.parser)

            self.prompt = PROMPT_REGISTRY["document_analyzer_prompt"]

            self.log.info("DocumentAnalyzer initialized successfully.", llm=str(self.llm))

        except Exception as e:
            log = CustomLogger().get_logger(__name__)
            log.error(f"Error initializing DocumentAnalyzer:", error=str(e))
            raise DocumentPortalException("failed to initialize DocumentAnalyzer", sys)
        
    def analyze_document(self, document_text: str) -> dict:
        """Analyze the given document text and return metadata."""
        try:
            chain = self.prompt | self.llm | self.fixing_parser

            self.log.info("Meta-data analysis chain initialized...")

            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_content": document_text
                })
            self.log.info("Document analyzed successfully.", response=response)

            return response

        except Exception as e:
            self.log.error(f"Error analyzing document:", error=str(e))
            raise DocumentPortalException("failed to analyze document", sys)