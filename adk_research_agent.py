"""
Research agent: parallel search tools → summary → analysis.
Uses Google ADK (LlmAgent, ParallelAgent, SequentialAgent, Runner).
Configure EXA_API_KEY, TAVILY_API_KEY, LINKUP_API_KEY in .env for full search; one is enough to run.
Set USE_LOCAL_LLM=1 or run app with --local-llm to use a local open-source LLM (e.g. Ollama / Hugging Face).
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from config import use_local_llm, local_llm_base_url, local_llm_model, openai_api_key

# Google ADK
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


def _get_llm():
    """LiteLlm for cloud (Nebius) or local OpenAI-compatible server (Ollama, vLLM, HF)."""
    if use_local_llm():
        return LiteLlm(
            model=local_llm_model(),
            api_base=local_llm_base_url(),
            api_key=openai_api_key(),
        )
    return LiteLlm(
        model=os.getenv("NEBIUS_CHAT_MODEL", "nebius/Qwen/Qwen3-235B-A22B"),
        api_base=os.getenv("NEBIUS_API_BASE"),
        api_key=os.getenv("NEBIUS_API_KEY"),
    )


# --- Search tools (add EXA_API_KEY, TAVILY_API_KEY, LINKUP_API_KEY as needed) ---

def exa_search_ai(topic: str) -> dict:
    """Search using Exa API for recent content on the topic."""
    try:
        from exa_py import Exa
        client = Exa(api_key=os.getenv("EXA_API_KEY"))
        results = client.search_and_contents(
            query=f"Latest developments and discussions about {topic}",
            num_results=5,
            text=True,
            type="auto",
            start_published_date=(datetime.now() - timedelta(days=90)).isoformat(),
        )
        return {"type": "exa", "results": [r.__dict__ for r in results.results]}
    except Exception as e:
        return {"type": "exa", "results": [], "error": str(e)}


def tavily_search_ai_analysis(topic: str) -> dict:
    """Search social/community sentiment via Tavily."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(
            query=f"Community sentiment and technical discussions about {topic}",
            search_depth="advanced",
            time_range="month",
            include_domains=["x.com", "reddit.com", "dev.to"],
        )
        return {"type": "tavily", "results": response.get("results", [])}
    except Exception as e:
        return {"type": "tavily", "results": [], "error": str(e)}


def linkup_search_ai(topic: str) -> dict:
    """Deep technical search (e.g. YC, GitHub, Stack Overflow)."""
    try:
        from linkup import LinkupClient
        client = LinkupClient(api_key=os.getenv("LINKUP_API_KEY"))
        search_response = client.search(
            query=f"Technical articles and code on {topic}",
            depth="deep",
            output_type="searchResults",
            include_domains=["https://github.com", "https://stackoverflow.com"],
        )
        results = getattr(search_response, "results", []) or []
        return {"type": "linkup", "results": [r.__dict__ for r in results]}
    except Exception as e:
        return {"type": "linkup", "results": [], "error": str(e)}


def run_adk_research(topic: str) -> str:
    """
    Run the ADK pipeline: parallel search → summary → (optional) analysis.
    Returns the final text (summary or analysis) for use in the RAG app.
    """
    model = _get_llm()

    # Build list of agents that have API keys
    search_agents = []
    if os.getenv("EXA_API_KEY"):
        search_agents.append(
            LlmAgent(
                name="ExaAgent",
                model=model,
                instruction=f"Use exa_search_ai to fetch latest news and developments about '{topic}'.",
                tools=[exa_search_ai],
                output_key="exa_results",
            )
        )
    if os.getenv("TAVILY_API_KEY"):
        search_agents.append(
            LlmAgent(
                name="TavilyAgent",
                model=model,
                instruction=f"Use tavily_search_ai_analysis to get community sentiment about '{topic}'.",
                tools=[tavily_search_ai_analysis],
                output_key="tavily_results",
            )
        )
    if os.getenv("LINKUP_API_KEY"):
        search_agents.append(
            LlmAgent(
                name="LinkupAgent",
                model=model,
                instruction=f"Use linkup_search_ai to find technical content about '{topic}'.",
                tools=[linkup_search_ai],
                output_key="linkup_results",
            )
        )

    if not search_agents:
        return (
            f"No search API keys set (EXA_API_KEY, TAVILY_API_KEY, LINKUP_API_KEY). "
            f"Placeholder analysis for topic: **{topic}**. Add keys and re-run for real research."
        )

    parallel_agent = ParallelAgent(
        name="ParallelSearchAgent",
        sub_agents=search_agents,
    )

    summary_agent = LlmAgent(
        name="SummaryAgent",
        model=model,
        instruction="""You are a research summarizer. Combine the information from the search results
into a single, coherent summary. Focus on latest trends, key points, and emerging tech. Use markdown.""",
        output_key="final_summary",
    )

    analysis_agent = LlmAgent(
        name="AnalysisAgent",
        model=model,
        instruction=f"""As an expert analyst, provide actionable insights about '{topic}'.
Use the 'final_summary' (and raw data if needed). Structure your response with:
1. **Key Trends** (2–3)
2. **Novel Angles**
3. **Gaps / Unanswered Questions**
4. **Contrarian or debated viewpoints**
This will be used to brainstorm a conference talk proposal. Be clear and structured.""",
        output_key="final_analysis",
    )

    pipeline = SequentialAgent(
        name="AIPipelineAgent",
        sub_agents=[parallel_agent, summary_agent, analysis_agent],
    )

    app_name = "adk_research_app"
    user_id = "streamlit_user"
    session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    session_service = InMemorySessionService()
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        )
        loop.close()
    except Exception:
        pass

    runner = Runner(agent=pipeline, app_name=app_name, session_service=session_service)
    content = types.Content(role="user", parts=[types.Part(text=f"Start analysis for {topic}")])
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    for event in events:
        if event.is_final_response():
            return getattr(event.content.parts[0], "text", str(event.content))

    return "ADK research agent did not return a final response."
