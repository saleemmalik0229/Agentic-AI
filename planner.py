from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from deep_research_backend.config import get_settings
from deep_research_backend.models import ResearchPlan

settings = get_settings()

class Planner:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.parser = JsonOutputParser(pydantic_object=ResearchPlan)

    def verify_plan(self, plan: ResearchPlan) -> ResearchPlan:
         # Optional: Check if plan is valid or optimized
         return plan

    def create_plan(self, user_query: str) -> ResearchPlan:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a Technical Research Planner.
            Create a step-by-step research plan to answer the user's request.
            Each step must use a specific tool (search, arxiv, analysis).
            
            User Request: {query}
            
            Hash out the specific queries for each step.
            
            {format_instructions}
            """
        )
        
        chain = prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "query": user_query,
                "format_instructions": self.parser.get_format_instructions()
            })
            # Convert dict back to Pydantic if needed (JsonOutputParser returns dict)
            return ResearchPlan(**result)
        except Exception as e:
            # Fallback plan
            from deep_research_backend.models import ResearchStep
            return ResearchPlan(
                goal=user_query,
                steps=[
                    ResearchStep(step_id=1, description="Search general info", tool="search", query=user_query)
                ]
            )
