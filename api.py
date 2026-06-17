from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from deep_research_backend.models import UserQueryRequest, AgentResponse
from deep_research_backend.execution_engine import app as runner
from deep_research_backend.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.APP_NAME)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.post("/query", response_model=AgentResponse)
async def run_query(request: UserQueryRequest):
    try:
        inputs = {"user_query": request.query}
        result = await runner.ainvoke(inputs)
        
        return AgentResponse(
            query=request.query,
            answer=result["final_answer"],
            trace=result["plan"].steps if result.get("plan") else []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
