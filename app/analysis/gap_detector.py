import re
from pathlib import Path
from typing import List

from app.models.analysis_models import AnalysisResult
from app.models.onboarding_models import DocumentationGap
from app.config.settings import Settings


class GapDetector:
    def __init__(self, settings: Settings):
        self.settings = settings

    def detect(self, root_path: Path | str, analysis_result: AnalysisResult) -> List[DocumentationGap]:
        root_path = Path(root_path)
        gaps = []

        # 1. Check for README
        if not self._file_exists(root_path, "README.md"):
            gaps.append(
                DocumentationGap(
                    gap_type="Missing README",
                    description="The repository does not have a README.md file at the root.",
                    severity="high",
                    affected_path="README.md"
                )
            )

        # 2. Check for environment example
        if analysis_result.env_variables and not self._file_exists(root_path, ".env.example"):
            gaps.append(
                DocumentationGap(
                    gap_type="Missing .env.example",
                    description="Environment variables were detected in the code, but no .env.example file was found.",
                    severity="medium",
                    affected_path=".env.example"
                )
            )

        # 3. Check for tests
        has_tests = False
        for node in analysis_result.tree.root.children:
            if node.name.lower() in ["tests", "test", "spec", "specs"]:
                has_tests = True
                break
        
        if not has_tests:
            # Check if testing framework was detected
            testing_frameworks = getattr(analysis_result.tech_stack, "testing", []) # We need to check if testing framework is there based on tech stack
            testing_detected = False
            for framework in analysis_result.tech_stack.items:
                 if framework.category.value == "TESTING":
                      testing_detected = True
                      break

            if not testing_detected:
                 gaps.append(
                    DocumentationGap(
                        gap_type="Missing Tests",
                        description="No test directory or testing framework could be confidently identified.",
                        severity="high"
                    )
                )

        # 4. Check for undocumented APIs
        undocumented_apis = 0
        for api in analysis_result.api_endpoints:
            # Simple heuristic: if we can't find a docstring near the handler
            if not self._has_docstring(root_path, api.file_path, api.line_number):
                undocumented_apis += 1
        
        if undocumented_apis > 0:
             gaps.append(
                DocumentationGap(
                    gap_type="Undocumented APIs",
                    description=f"Found {undocumented_apis} API endpoint handlers without apparent docstrings or comments.",
                    severity="medium"
                )
            )

        # 5. Missing CONTRIBUTING.md
        if not self._file_exists(root_path, "CONTRIBUTING.md"):
            gaps.append(
                DocumentationGap(
                    gap_type="Missing CONTRIBUTING.md",
                    description="No contribution guidelines provided for new developers.",
                    severity="low",
                    affected_path="CONTRIBUTING.md"
                )
            )

        return gaps

    def _file_exists(self, root_path: Path, filename: str) -> bool:
        # Case insensitive match
        for f in root_path.iterdir():
            if f.is_file() and f.name.lower() == filename.lower():
                return True
        return False

    def _has_docstring(self, root_path: Path, file_path: str, line_number: int) -> bool:
        target = root_path / file_path
        if not target.exists() or not target.is_file():
            return False
            
        try:
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            if line_number > len(lines) or line_number < 1:
                return False
                
            # Check next 3 lines for docstrings (''' or """) or comments (//, #)
            start_idx = max(0, line_number - 1)
            end_idx = min(len(lines), start_idx + 4)
            
            for line in lines[start_idx:end_idx]:
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''") or stripped.startswith('#') or stripped.startswith('//'):
                    return True
            return False
        except Exception:
            return False
