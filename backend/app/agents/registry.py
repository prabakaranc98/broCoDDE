"""
BroCoDDE — Agent Registry
Registers all four agents with Agno AgentOS for named-service access, HTTP streaming,
and the AgentOS control plane (monitoring, session inspection, error tracking).
"""

from agno.agent import Agent

from app.agents.analyst import build_analyst
from app.agents.interviewer import build_interviewer
from app.agents.shaper import build_shaper
from app.agents.strategist import build_strategist


def get_all_agents(user_id: str = "default_user") -> list[Agent]:
    """Return all four agents — used when registering with AgentOS."""
    return [
        build_strategist(stage="discovery", user_id=user_id),
        build_interviewer(role="researcher", user_id=user_id),
        build_shaper(mode="vetting", user_id=user_id),
        build_analyst(user_id=user_id),
    ]


def get_agent_api():
    """
    Build and return the Agno AgentAPI app (mounts at /agentapi in main.py).
    This gives AgentOS's control plane UI, streaming endpoints, and session management.
    """
    from agno.app.agentapi import AgentAPI

    agents = get_all_agents()
    return AgentAPI(agents=agents, prefix="/agentapi")
