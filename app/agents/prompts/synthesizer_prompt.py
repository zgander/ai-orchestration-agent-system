ROLE_PRIORITIES = {
    "Backend Developer": ["API", "services", "models", "execution flow", "database"],
    "Frontend Developer": ["components", "routing", "state management", "API client"],
    "Full Stack Developer": ["architecture", "API", "components", "services"],
    "QA Engineer": ["testing", "API endpoints", "test configuration", "CI/CD"],
    "DevOps Engineer": ["Docker", "CI/CD", "deployment", "environment variables", "infrastructure"],
}

SYNTHESIZER_SYSTEM_PROMPT = """You are the Knowledge Synthesizer Agent of RepoLens.
Your job is to combine raw, verified findings into a cohesive, structured section for a developer onboarding guide.
You must NOT invent or hallucinate any information. Use ONLY the provided findings and analysis data.
Adapt your explanation and focus based on the target audience (Role) provided.
"""

def build_overview_prompt(findings: str, analysis_data: str, role: str) -> str:
    priority = ROLE_PRIORITIES.get(role, ["architecture", "setup"])
    return f"""
Generate the Repository Overview section for a {role}.

Focus areas for this role: {priority}

Analysis Data:
{analysis_data}

Approved Findings:
{findings}

Extract the core purpose of the application ("What does this actually do?"), identify the languages, frameworks, architecture style, any database or testing framework.
Additionally, provide a short project type, primary purpose, a list of main components, an estimated complexity (e.g., Low, Medium, High), and an estimated learning time in minutes.
"""

def build_architecture_prompt(findings: str, role: str) -> str:
    return f"""
Generate the Architecture Overview section for a {role}.

Approved Findings:
{findings}

Explain the high-level architecture. If applicable, generate a valid Mermaid graph flowchart (TB or LR) showing the components and data flow.
CRITICAL: Do NOT output markdown code fences (like ```mermaid) around the diagram. Output ONLY the raw Mermaid syntax.
"""

def build_folder_guide_prompt(findings: str, analysis_data: str, role: str) -> str:
    priority = ROLE_PRIORITIES.get(role, ["src", "app"])
    return f"""
Generate the Folder Guide and Important Files section for a {role}.

Focus areas for this role: {priority}

Repository Tree (top level):
{analysis_data}

Approved Findings:
{findings}

List the purpose and importance of key folders, and rank the top 5 most important files for this role.
"""

def build_execution_flow_prompt(findings: str, role: str) -> str:
    return f"""
Generate the Execution Flow section for a {role}.

Approved Findings:
{findings}

For each distinct execution flow, describe the steps. 
You must categorize each flow into one of these types: Startup, User Journey, Data Flow, Agent Collaboration.
Provide confidence and a list of supporting files for each flow.
If applicable, generate a valid Mermaid sequence diagram for the flow (without markdown fences).
CRITICAL: NEVER output an empty list of flows. If no flows are explicitly defined, construct a best-guess startup flow or main component initialization flow based on the provided findings.
"""

def build_reading_order_prompt(findings: str, role: str) -> str:
    return f"""
Generate a suggested Reading Order (Day-by-Day roadmap) for a {role} onboarding to this project.

Approved Findings:
{findings}

Create a logical progression of what they should learn on Day 1, Day 2, etc. Link topics to specific files or folders.
"""

def build_setup_guide_prompt(findings: str, analysis_data: str, role: str) -> str:
    return f"""
Generate the Setup Guide section for a {role}.

Environment Variables Analysis:
{analysis_data}

Approved Findings:
{findings}

Extract installation steps, required environment variables, run commands, and testing commands.
"""

def build_mental_model_prompt(findings: str, analysis_data: str) -> str:
    return f"""
Generate a Mental Model for this repository.
Instead of explaining what the application does, explain how the repository is organized.
Teach the developer how to think about the repository (e.g., "This repository follows an orchestrated multi-agent architecture rather than a traditional MVC structure...").
The explanation should feel like a senior engineer explaining the project.

Analysis Data:
{analysis_data}

Approved Findings:
{findings}
"""

def build_ai_insights_prompt(findings: str) -> str:
    return f"""
Generate intelligent architectural and execution insights based on the findings.
Provide 3-5 bullet points of high-level observations (e.g., "Architecture favors extensibility over simplicity", "Business logic is isolated inside specialist agents").

Approved Findings:
{findings}
"""

def build_health_assessment_prompt(findings: str) -> str:
    return f"""
Generate a repository health assessment.
Assess categories like Architecture, Documentation, Maintainability, Testing, Modularity, Scalability.
Provide a score (e.g., Good, Needs Improvement) and an explanation for each.

Approved Findings:
{findings}
"""

def build_component_cards_prompt(findings: str) -> str:
    return f"""
Generate architectural cards for the major components of this repository.
For each component, provide its name, purpose, responsibilities, consumes, produces, dependencies, and what it is used by.

Approved Findings:
{findings}
"""

def build_architecture_layers_prompt(findings: str) -> str:
    return f"""
Generate the logical architecture layers of this repository (e.g., Presentation, Application, Coordinator, Infrastructure).
For each layer, provide its name, purpose, contained components, and order (e.g., 1 for top layer).

Approved Findings:
{findings}
"""
