from typing import TypedDict, Annotated, List, Dict, Any
import operator
from langgraph.graph import StateGraph, END

from deep_research_backend.models import ResearchPlan, ResearchStep
from deep_research_backend.agents.agents import ResearchAgent, FilterAgent, SynthesisAgent
from deep_research_backend.planner import Planner
from deep_research_backend.memory.history import get_history_manager

# Define State
class AgentState(TypedDict):
    user_query: str
    plan: ResearchPlan
    current_step_index: int
    context: Annotated[List[str], operator.add]
    final_answer: str
    from_cache: bool
    ignore_cache: bool  # New flag

# Initialize components
planner = Planner()
research_agent = ResearchAgent()
filter_agent = FilterAgent()
synthesis_agent = SynthesisAgent()
from deep_research_backend.config import get_settings

settings = get_settings()
# Initialize with scalable factory
history_manager = get_history_manager(settings.DATABASE_URL if "postgres" in settings.DATABASE_URL else None)

async def check_history_node(state: AgentState):
    if state.get("ignore_cache"):
        return {"from_cache": False}

    query = state["user_query"]
    cached_answer = await history_manager.get(query)
    
    if cached_answer:
        return {"final_answer": cached_answer, "from_cache": True}
    return {"from_cache": False}

def plan_node(state: AgentState):
    # Only plan if not found in cache
    if state.get("from_cache"):
        return {}
        
    query = state["user_query"]
    plan = planner.create_plan(query)
    return {"plan": plan, "current_step_index": 0}

def execute_step_node(state: AgentState):
    if state.get("from_cache"):
        return {}
        
    plan = state["plan"]
    index = state["current_step_index"]
    
    if index >= len(plan.steps):
        return {"current_step_index": index} 
        
    step = plan.steps[index]
    result_text = ""
    
    # Execute Agent based on tool
    if step.tool in ["search", "arxiv"]:
        res = research_agent.run({"query": step.query, "tool": step.tool})
        # Basic filtering
        filtered = filter_agent.run({"results": res["results"], "query": step.query})
        
        # Format results
        for item in filtered["filtered_results"]:
            result_text += f"Source: {item.get('title')} ({item.get('url')})\nContent: {item.get('content')}\n\n"
    elif step.tool == "analysis":
         result_text = f"Analysis step: {step.description}\n" # Placeholder for AnalysisAgent

    step.result = result_text
    step.status = "completed"
    
    return {
        "context": [result_text],
        "current_step_index": index + 1
    }

async def synthesize_node(state: AgentState):
    if state.get("from_cache"):
        return {}

    context_str = "\n".join(state["context"])
    res = synthesis_agent.run({"query": state["user_query"], "context": context_str})
    
    # Async Save
    await history_manager.set(state["user_query"], res["answer"])
    
    return {"final_answer": res["answer"]}

def route_start(state: AgentState):
    if state.get("from_cache"):
        return "end"
    return "planner"

def should_continue(state: AgentState):
    if state.get("from_cache"):
        return "end"
    if state["current_step_index"] < len(state["plan"].steps):
        return "execute_step"
    return "synthesize"

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("check_history", check_history_node)
workflow.add_node("planner", plan_node)
workflow.add_node("execute_step", execute_step_node)
workflow.add_node("synthesize", synthesize_node)

workflow.set_entry_point("check_history")

workflow.add_conditional_edges(
    "check_history",
    route_start,
    {
        "end": END,
        "planner": "planner"
    }
)

workflow.add_conditional_edges(
    "execute_step",
    should_continue,
    {
        "execute_step": "execute_step",
        "synthesize": "synthesize",
        "end": END
    }
)

workflow.add_edge("planner", "execute_step")
workflow.add_edge("synthesize", END)

app = workflow.compile()
