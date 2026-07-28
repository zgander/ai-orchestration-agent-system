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

Extract the core purpose of the application ("What does this actually do?"), identify the languages, frameworks, architecture style, and any database or testing framework.
"""

def build_architecture_prompt(findings: str, role: str) -> str:
    return f"""
Generate the Architecture Overview section for a {role}.

Approved Findings:
{findings}

Explain the high-level architecture. If applicable, generate a valid Mermaid graph flowchart (TB or LR) showing the components and data flow.
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

For each distinct execution flow (e.g., Request lifecycle, Data processing pipeline), describe the steps. If applicable, generate a valid Mermaid sequence diagram for the flow.
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
