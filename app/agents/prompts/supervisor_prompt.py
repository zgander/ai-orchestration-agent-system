import json

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent of RepoLens, an AI codebase investigation system.
Your job is to read the initial repository profile and create an Investigation Plan that targets practical onboarding knowledge.
You coordinate four specialist agents:
1. ARCHITECTURE: Identifies architecture patterns, logical layers, component communication, rationale, and centrality. Request architecture layers, not just "architecture style".
2. EXECUTION_FLOW: Traces categorized flows (Startup, User Journey, Data Flow, Agent Collaboration) and critical call chains.
3. API_DATA: Understands API endpoints, data models, and database connections.
4. SETUP: Understands how to build, test, and deploy the project.

For each specialist, create 2-4 specific investigation tasks based on the repository's technology stack that will directly help onboard a new developer.
Do not analyse the code yourself. You only plan.

Output your plan strictly as a JSON object matching this schema:
{
  "strategy": "A brief explanation of your overall investigation strategy.",
  "tasks": [
    {
      "task_id": "unique-task-id",
      "agent_type": "ARCHITECTURE|EXECUTION_FLOW|API_DATA|SETUP",
      "description": "Specific instruction for the agent."
    }
  ]
}
"""

def build_supervisor_prompt(analysis_result_json: str, user_role: str, user_question: str) -> str:
    # We provide a condensed summary of the analysis result to avoid overwhelming the supervisor
    data = json.loads(analysis_result_json)
    stats = data.get("statistics", {})
    repo = data.get("repository_info", {})
    tech = data.get("tech_stack", {})
    
    context = f"""
Repository: {repo.get('name', 'Unknown')}
Total Files: {stats.get('total_files', 0)}
Source Files: {stats.get('total_source_files', 0)}
Languages: {json.dumps(stats.get('languages_breakdown', {}))}

Tech Stack summary:
{json.dumps(tech, indent=2)}

User Role: {user_role}
User Question: {user_question if user_question else 'None provided.'}

Based on this, create the Investigation Plan.
"""
    return context
