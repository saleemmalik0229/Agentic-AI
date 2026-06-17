from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from deep_research_backend.config import get_settings
from deep_research_backend.tools.search import SearchTool, ArxivTool

settings = get_settings()

class BaseAgent(ABC):
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL, 
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class ResearchAgent(BaseAgent):
    """Fetches data using tools."""
    def __init__(self):
        super().__init__()
        self.search_tool = SearchTool()
        self.arxiv_tool = ArxivTool()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query")
        tool = input_data.get("tool", "search")
        
        results = []
        if tool == "search":
            results = self.search_tool.search(query)
        elif tool == "arxiv":
            results = self.arxiv_tool.search(query)
            
        return {"results": results}

class FilterAgent(BaseAgent):
    """Filters relevance."""
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        results = input_data.get("results", [])
        query = input_data.get("query")
        
        # Simple Logic for now: Pass to LLM to filter
        # Optimization: Batch processing or assume top results are relevant for MVP
        
        prompt = ChatPromptTemplate.from_template(
            "Filter these results for query: {query}. Return only relevant indices. Results: {results}"
        )
        # Placeholder for full LLM filtering logic
        # For efficiency in this build, we just pass through or truncate
        return {"filtered_results": results[:3]} # Return top 3 as "filtered"

class SynthesisAgent(BaseAgent):
    """Synthesizes final answer."""
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        context = input_data.get("context", "")
        query = input_data.get("query")
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a Principal Software Engineer.
            Answer the user query based **only** on the provided context.
            Cite your sources.
            
            Query: {query}
            Context: {context}
            
            Answer:
            """
        )
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"query": query, "context": context})
        return {"answer": answer}
