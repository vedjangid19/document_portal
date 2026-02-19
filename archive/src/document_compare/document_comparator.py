import sys
import pandas as pd
from dotenv import load_dotenv
from utils.model_loader import ModelLoader
from model.models import *
from prompt.prompt_library import PROMPT_REGISTRY
from langchain_core.output_parsers import JsonOutputParser
from langchain_classic.output_parsers import OutputFixingParser  #type: ignore
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger



class DocumentComparaorLLM:
    def __init__(self):
        load_dotenv()
        self.log = CustomLogger().get_logger(__name__)
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)

        self.prompt = PROMPT_REGISTRY["document_comparison_prompt"]
        self.chain = self.prompt | self.llm | self.parser

        self.log.info("DocumentComparatorLLM initialized with model and parser.")

    def compare_documents(self, combined_docs:str):
        """
        Compares two documents and returns a structured comparison.
        """
        print("==============================")
        print(combined_docs)
        print("==============================")
        try:
            inputs = {
                "combined_docs": combined_docs,
                "format_instructions": self.parser.get_format_instructions()
            }

            self.log.info("Starting document comparison.", inputs=inputs)
            response = self.chain.invoke(inputs)
            print("response:::",response)
            self.log.info("Document comparison completed.", response=response)

            return self._format_response(response)
            
        except Exception as e:
            raise DocumentPortalException("An Error occurred while comparing documents.", sys)
        

    def _format_response(self, response_parsed: list[dict])->pd.DataFrame:
        """
        Formats the response from the LLM into a structured format.
        """
        try:
            df = pd.DataFrame(response_parsed)
            self.log.info("response formated into Dataframe.", dataframe=df)
            return df
        except Exception as e:
            self.log.error("Error formatting response into DataFrame", error=str(e))
            raise DocumentPortalException("Error formatting response",sys)