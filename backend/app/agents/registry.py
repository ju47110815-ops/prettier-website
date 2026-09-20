from __future__ import annotations

from app.models.core import AgentDefinition, ModelTier


AGENT_IDS = [
    ("website_content_researcher", "Content researcher", "Extract and summarize important page content."),
    ("website_url_researcher", "URL researcher", "Analyze URL structure and redirects."),
    ("website_asset_researcher", "Asset researcher", "Inventory migration-relevant assets."),
    ("website_ux_auditor", "UX auditor", "Identify UX and accessibility concerns."),
    ("website_research_integrator", "Research integrator", "Combine specialist research into a bundle."),
    ("website_information_architect", "Information architect", "Design the new information architecture."),
    ("website_content_model_architect", "Content model architect", "Design a lightweight content model."),
    ("website_technical_architect", "Technical architect", "Recommend implementation architecture."),
    ("website_ux_design_strategist", "UX design strategist", "Define UX and design strategy."),
    ("website_architecture_integrator", "Architecture integrator", "Integrate architecture recommendations."),
    ("website_migration_executor", "Migration executor", "Prepare migrated content and assets."),
    ("website_builder", "Website builder", "Build the generated website workspace."),
    ("website_content_integrator", "Content integrator", "Integrate migrated content into the build."),
    ("website_qa_reviewer", "QA reviewer", "Review deterministic results and identify defects."),
    ("website_bug_fixer", "Bug fixer", "Fix reported defects in the job workspace."),
]


class AgentRegistry:
    def __init__(self):
        self._agents = {agent_id: AgentDefinition(id=agent_id, name=name, purpose=purpose) for agent_id, name, purpose in AGENT_IDS}
        self._agents["website_research_integrator"].preferred_model_tier = ModelTier.STANDARD
        self._agents["website_architecture_integrator"].preferred_model_tier = ModelTier.STANDARD
        self._agents["website_builder"].preferred_model_tier = ModelTier.STANDARD

    def get(self, agent_id: str) -> AgentDefinition:
        return self._agents[agent_id]

    def all(self) -> list[AgentDefinition]:
        return list(self._agents.values())
