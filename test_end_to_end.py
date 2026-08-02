import sys
from pathlib import Path
from datetime import datetime

# Setup paths
root_path = Path(__file__).parent.absolute()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.config.settings import settings
from app.services.repository_service import RepositoryService
from app.services.investigation_service import InvestigationService
from app.models.repository import RepositoryInfo, SourceType

def trace_workflow():
    print(f"[{datetime.now().time()}] Phase 3 E2E Trace Started")
    print(f"[{datetime.now().time()}] LLM Provider: {settings.llm_provider}")
    print(f"[{datetime.now().time()}] LLM Model: {settings.ollama_model}")
    
    # We construct a real RepositoryInfo pointing to a small directory
    test_dir = root_path / "app" / "models"
    repo_info = RepositoryInfo(
        name="test-models",
        source={"source_type": SourceType.ZIP, "url": "", "local_path": str(test_dir)},
        root_path=str(test_dir),
        size_bytes=1000,
        cloned_at=datetime.now()
    )
    
    repo_service = RepositoryService(settings)
    inv_service = InvestigationService(settings)
    
    # 3. Analyze real directory
    print(f"[{datetime.now().time()}] Analyzing {test_dir}...")
    try:
        analysis = repo_service.analyse(repo_info)
        print(f"[{datetime.now().time()}] Analysis complete. Found {analysis.statistics.total_files} files.")
    except Exception as e:
        print(f"[{datetime.now().time()}] Analysis Failed: {e}")
        import traceback
        traceback.print_exc()
        return
        
    # 4. Investigate
    print(f"[{datetime.now().time()}] Investigating...")
    def prog_cb(events):
        if events:
            print(f"   -> Progress: {events[-1].agent_type.value} - {events[-1].event}")
            
    try:
        inv_result = inv_service.investigate(
            analysis_result=analysis,
            user_role="Software Engineer",
            user_question="Explain the core models.",
            progress_callback=prog_cb
        )
        print(f"[{datetime.now().time()}] Investigation Complete. Errors: {inv_result.errors}")
    except Exception as e:
        print(f"[{datetime.now().time()}] Investigation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_workflow()
