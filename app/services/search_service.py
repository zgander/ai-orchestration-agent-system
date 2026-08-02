import json
from typing import List, Optional
from app.models.history_models import GlobalSearchResult, SearchResultType
from app.services.investigation_cache import CACHE_DIR

class GlobalSearchService:
    def search(self, query: str, repo_name: Optional[str] = None) -> List[GlobalSearchResult]:
        query = query.lower()
        results = []
        
        if not CACHE_DIR.exists():
            return results
            
        for file_path in CACHE_DIR.glob("*.json"):
            if repo_name and not file_path.name.startswith(f"{repo_name}_"):
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Search across architecture, execution flows, APIs
                guide = data.get("onboarding_guide", {})
                if not guide:
                    continue
                    
                # Arch
                if query in str(guide.get("architecture_explanation", "")).lower() or query in str(guide.get("mental_model", "")).lower():
                    results.append(GlobalSearchResult(
                        title=f"{data['plan']['repository_name']} - Architecture",
                        snippet="Found match in architecture description.",
                        url_fragment="arch_explorer",
                        result_type=SearchResultType.ARCHITECTURE,
                        relevance=0.9
                    ))
                    
                # Flows
                for flow in guide.get("execution_flows", []):
                    if query in flow.get("name", "").lower() or any(query in step.get("description", "").lower() for step in flow.get("steps", [])):
                        results.append(GlobalSearchResult(
                            title=f"{data['plan']['repository_name']} - Flow: {flow.get('name')}",
                            snippet=f"Match in execution flow: {flow.get('name')}",
                            url_fragment="exec_navigator",
                            result_type=SearchResultType.EXECUTION_FLOW,
                            relevance=0.8
                        ))
                        
                # APIs
                for api in guide.get("api_explorer", []):
                    if query in api.get("path", "").lower() or query in api.get("description", "").lower() or query in api.get("handler_file", "").lower():
                        results.append(GlobalSearchResult(
                            title=f"{data['plan']['repository_name']} - API: {api.get('method')} {api.get('path')}",
                            snippet=api.get("description", "API Endpoint Match"),
                            url_fragment="search",
                            result_type=SearchResultType.API,
                            relevance=0.85
                        ))
                        
                # Search Agent findings directly
                for agent, report in data.get("agent_reports", {}).items():
                    for finding in report.get("findings", []):
                        if query in finding.get("title", "").lower() or query in finding.get("description", "").lower():
                            results.append(GlobalSearchResult(
                                title=f"{data['plan']['repository_name']} - Finding: {finding.get('title')}",
                                snippet=finding.get("description", "")[:100] + "...",
                                url_fragment="search",
                                result_type=SearchResultType.DOCUMENTATION_GAP if finding.get("category") == "Missing" else SearchResultType.FILE,
                                source_section=agent,
                                relevance=0.7
                            ))
                            
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Search failed on {file_path}: {e}")
                
        # Sort by relevance desc
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results
