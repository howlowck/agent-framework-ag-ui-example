import datetime
import logging
import os
import random

import fastapi
import fastapi.responses
import fastapi.staticfiles
import opentelemetry.instrumentation.fastapi as otel_fastapi
import telemetry
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional, cast

import uvicorn
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIClient, AzureOpenAIChatClient, AzureAIAgentClient
from agent_framework.observability import setup_observability
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

class ChatRequest(BaseModel):
	query: str


@dataclass
class AppState:
	_azure_credential: Optional[DefaultAzureCredential] = None
	_project_client_ctx: Optional[AIProjectClient] = None
	_project_client: Optional[AIProjectClient] = None
	_azure_ai_agent: Optional[Any] = None
	_chat_client: Optional[AzureAIClient] = None
	_agent_ctx: Optional[ChatAgent] = None
	_agent: Optional[ChatAgent] = None
	_agui_registered: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
	required_env = ["AZURE_AI_PROJECT_ENDPOINT", "AZURE_AI_AGENT_NAME"]
	missing = [env for env in required_env if env not in os.environ]
	if missing:
		raise RuntimeError(f"Required Azure environment variables are not set: {', '.join(missing)}")

	telemetry.configure_opentelemetry()

	azure_credential = DefaultAzureCredential()
	await azure_credential.__aenter__()

	project_client_ctx = AIProjectClient(
		endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
		credential=azure_credential,
	)
	
	project_client = await project_client_ctx.__aenter__()
	agent_name = os.environ["AZURE_AI_AGENT_NAME"]

	agent = await project_client.agents.get(agent_name=agent_name)

	chat_client = AzureAIClient(
		project_client=project_client,
		agent_name=agent.name,
		async_credential=azure_credential,
		use_latest_version=True,
	)

	agent_ctx = ChatAgent(chat_client=chat_client)
	agent = await agent_ctx.__aenter__()

	state = cast(AppState, app.state)
	state._azure_credential = azure_credential
	state._chat_client = chat_client
	state._agent_ctx = agent_ctx
	state._agent = agent

	if not getattr(state, "_agui_registered", False):
		add_agent_framework_fastapi_endpoint(app, agent, "/")
		state._agui_registered = True

	try:
		yield
	finally:
		await agent_ctx.__aexit__(None, None, None)
		await project_client_ctx.__aexit__(None, None, None)
		await azure_credential.__aexit__(None, None, None)

app = FastAPI(title="Azure AI Chat Agent with AG-UI", lifespan=lifespan)

otel_fastapi.FastAPIInstrumentor.instrument_app(app, exclude_spans=["send"])


logger = logging.getLogger(__name__)


if not os.path.exists("static"):
    @app.get("/", response_class=fastapi.responses.HTMLResponse)
    async def root():
        """Root endpoint."""
        return "API service is running. Navigate to <a href='/api/weatherforecast'>/api/weatherforecast</a> to see sample data."

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
	state = cast(AppState, app.state)
	if state._agent is None:
		raise HTTPException(status_code=500, detail="Agent is not initialized")

	if not req.query.strip():
		return {"status": "ignored", "reason": "empty_query"}

	state._agent.run_stream(req.query)
	return {"status": "started"}


@app.get("/health", response_class=fastapi.responses.PlainTextResponse)
async def health_check():
    """Health check endpoint."""
    return "Healthy"


# Serve static files directly from root, if the "static" directory exists
if os.path.exists("static"):
    app.mount(
        "/",
        fastapi.staticfiles.StaticFiles(directory="static", html=True),
        name="static"
    )

if __name__ == "__main__":
	port = int(os.environ.get("PORT", "8000"))
	uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
