import re
from typing import List
from app.models.chat_models import KnowledgeFragment, QueryClassification, QueryCategory, CitationType
from app.models.analysis_models import AnalysisResult
from app.models.investigation_models import InvestigationResult

class KnowledgeRetriever:
    def __init__(self, max_fragments: int = 5):
        self.max_fragments = max_fragments

    def retrieve(self, 
                 query: str, 
                 classification: QueryClassification, 
                 analysis_result: AnalysisResult, 
                 investigation_result: InvestigationResult) -> List[KnowledgeFragment]:
        fragments = []
        
        # ALWAYS include base context
        if investigation_result.onboarding_guide:
            guide = investigation_result.onboarding_guide
            fragments.append(KnowledgeFragment(
                source_type=CitationType.SECTION,
                content=f"Repository Overview: {guide.repository_overview.description}\nMental Model: {guide.mental_model}",
                relevance_score=0.8,
                section_name="Overview"
            ))
            
            if classification.category == QueryCategory.ARCHITECTURE:
                fragments.append(KnowledgeFragment(
                    source_type=CitationType.SECTION,
                    content=f"Architecture Explanation:\n{guide.architecture_explanation}",
                    relevance_score=1.0,
                    section_name="Architecture Explanation"
                ))
            elif classification.category == QueryCategory.EXECUTION_FLOW:
                for flow in guide.execution_flows:
                    content = f"Execution Flow: {flow.name}\n"
                    for step in flow.steps:
                        content += f"- {step.get('step', '')}: {step.get('detail', '')}\n"
                    fragments.append(KnowledgeFragment(
                        source_type=CitationType.SECTION,
                        content=content,
                        relevance_score=0.9,
                        section_name=f"Execution Flow: {flow.name}",
                        evidence=[e.content for e in flow.evidence] if flow.evidence else None
                    ))
            elif classification.category == QueryCategory.API:
                content = "API Endpoints:\n"
                for api in guide.api_explorer:
                    content += f"- {api.method} {api.path} (Handled by {api.handler_function} in {api.handler_file}): {api.purpose}\n"
                if guide.api_explorer:
                    fragments.append(KnowledgeFragment(
                        source_type=CitationType.SECTION,
                        content=content,
                        relevance_score=0.9,
                        section_name="API Explorer"
                    ))
            elif classification.category == QueryCategory.SETUP:
                content = "Setup Guide:\nInstallation:\n"
                for step in guide.setup_guide.installation_steps:
                    content += f"- {step}\n"
                if guide.setup_guide.environment_variables:
                    content += "\nEnvironment Variables:\n"
                    for env in guide.setup_guide.environment_variables:
                        content += f"- {env.get('name', '')}\n"
                if guide.setup_guide.run_commands:
                    content += "\nRun Commands:\n"
                    for cmd in guide.setup_guide.run_commands:
                        content += f"- {cmd.get('command', '')}\n"
                
                fragments.append(KnowledgeFragment(
                    source_type=CitationType.SECTION,
                    content=content,
                    relevance_score=0.9,
                    section_name="Setup Guide",
                    evidence=[e.content for e in guide.setup_guide.evidence] if guide.setup_guide.evidence else None
                ))
            elif classification.category == QueryCategory.GENERAL:
                if guide.ai_insights:
                    fragments.append(KnowledgeFragment(
                        source_type=CitationType.SECTION,
                        content=f"AI Insights:\n" + "\n".join(f"- {i}" for i in guide.ai_insights),
                        relevance_score=0.85,
                        section_name="AI Insights"
                    ))
        else:
            # Fallback if no onboarding guide
            tech_stack = ", ".join(l.name for l in analysis_result.tech_stack.languages)
            fragments.append(KnowledgeFragment(
                source_type=CitationType.SECTION,
                content=f"Repository {analysis_result.repository_info.name} is a software project using {tech_stack}.",
                relevance_score=0.8,
                section_name="Overview (Fallback)"
            ))
                
        # 2. Agent Findings Search
        query_terms = [t.lower() for t in classification.sub_topics] + [word.lower() for word in query.split() if len(word) > 3]
        query_terms = list(set(query_terms)) # deduplicate
        
        for agent_type, report in investigation_result.agent_reports.items():
            if report.findings:
                for finding in report.findings:
                    title_desc = f"{finding.title} {finding.description}".lower()
                    
                    # Calculate a simple match score
                    match_score = sum(1 for term in query_terms if term in title_desc)
                    if match_score > 0:
                        # Boost score if finding was explicitly approved
                        boost = 0.2 if finding.review_status == "APPROVED" else 0.0
                        score = min(0.95, (match_score / len(query_terms)) * 0.6 + boost)
                        
                        fragments.append(KnowledgeFragment(
                            source_type=CitationType.FINDING,
                            content=f"Finding ({agent_type.value}): {finding.title}\n{finding.description}",
                            relevance_score=score,
                            section_name=finding.title,
                            evidence=[e.content for e in finding.evidence] if finding.evidence else None
                        ))
        
        # 3. Evidence Lookup
        # We implicitly capture evidence by including it inside findings, but we could also search raw evidence here
        # (Omitted for brevity, Agent Findings usually cover the relevant evidence)

        # 4. Analysis Data Lookup (for CODE or API categories)
        if classification.category == QueryCategory.CODE or classification.requires_code_lookup:
            for term in query_terms:
                results = analysis_result.symbol_index.lookup(term)
                if results:
                    for sym in results:
                        fragments.append(KnowledgeFragment(
                            source_type=CitationType.FILE,
                            content=f"Symbol '{sym.name}' (Kind: {sym.kind.value}) is defined in {sym.file_path} at line {sym.line_number}",
                            relevance_score=0.85,
                            section_name=sym.file_path
                        ))
                        
            # We can also check dependency graph edges if sub_topics suggest imports
            if any("import" in t or "depend" in t for t in query_terms):
                edges = analysis_result.dependency_graph.edges
                content = "Dependencies:\n"
                match_found = False
                for edge in edges:
                    if any(term in edge.source_file.lower() or term in edge.target_file.lower() for term in query_terms):
                        content += f"- {edge.source_file} imports {edge.target_file} ({edge.import_name})\n"
                        match_found = True
                if match_found:
                    fragments.append(KnowledgeFragment(
                        source_type=CitationType.FILE,
                        content=content,
                        relevance_score=0.7,
                        section_name="Dependency Graph"
                    ))

        # Rank and return top K
        fragments.sort(key=lambda x: x.relevance_score, reverse=True)
        return fragments[:self.max_fragments]
