import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set

from app.models.analysis_models import TechStack, TechStackItem, TechCategory
from app.config.settings import Settings
from app.utils.file_utils import find_files, get_file_extension, safe_read_text

class StackDetector:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        self.language_extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".cpp": "C++",
            ".c": "C",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS"
        }
        
        self.framework_signatures = {
            "requirements.txt": [
                (r"(?i)fastapi", "FastAPI"),
                (r"(?i)flask", "Flask"),
                (r"(?i)django", "Django"),
            ],
            "package.json": [
                (r"(?i)\"react\"", "React"),
                (r"(?i)\"vue\"", "Vue"),
                (r"(?i)\"@angular/core\"", "Angular"),
                (r"(?i)\"next\"", "Next.js"),
                (r"(?i)\"express\"", "Express"),
            ],
            "pom.xml": [
                (r"(?i)spring-boot-starter", "Spring Boot"),
            ]
        }
        
        self.db_signatures = {
            "requirements.txt": [
                (r"(?i)psycopg2", "PostgreSQL"),
                (r"(?i)asyncpg", "PostgreSQL"),
                (r"(?i)pymysql", "MySQL"),
                (r"(?i)pymongo", "MongoDB"),
                (r"(?i)sqlalchemy", "SQLAlchemy ORM"),
            ],
            "package.json": [
                (r"(?i)\"pg\"", "PostgreSQL"),
                (r"(?i)\"mysql2\"", "MySQL"),
                (r"(?i)\"mongoose\"", "MongoDB"),
                (r"(?i)\"prisma\"", "Prisma ORM"),
            ]
        }
        
        self.package_managers = {
            "requirements.txt": "pip",
            "Pipfile": "pipenv",
            "pyproject.toml": "poetry (or other PEP-517)",
            "package.json": "npm/yarn",
            "yarn.lock": "yarn",
            "pnpm-lock.yaml": "pnpm",
            "pom.xml": "Maven",
            "build.gradle": "Gradle",
            "go.mod": "Go Modules",
            "Cargo.toml": "Cargo"
        }
        
        self.testing_signatures = {
            "pytest.ini": "pytest",
            "conftest.py": "pytest",
            "jest.config.js": "Jest",
            "jest.config.ts": "Jest",
            "requirements.txt": [
                (r"(?i)pytest", "pytest"),
            ],
            "package.json": [
                (r"(?i)\"jest\"", "Jest"),
                (r"(?i)\"mocha\"", "Mocha"),
            ]
        }
        
        self.ci_cd_signatures = {
            ".gitlab-ci.yml": "GitLab CI",
        }

    def analyse(self, root_path: Path) -> TechStack:
        items: List[TechStackItem] = []
        
        # 1. Languages (by extension frequency)
        lang_counts: Dict[str, int] = defaultdict(int)
        lang_files: Dict[str, List[str]] = defaultdict(list)
        
        # 2. File-based signatures
        detected_files: Set[str] = set()
        
        for file_path in find_files(root_path, self.settings):
            ext = get_file_extension(file_path)
            if ext in self.language_extensions:
                lang = self.language_extensions[ext]
                lang_counts[lang] += 1
                if len(lang_files[lang]) < 5:  # Keep up to 5 examples
                    lang_files[lang].append(str(file_path.relative_to(root_path)))
            
            # Record signature files
            detected_files.add(file_path.name)
            
            # Detailed file content checks for certain signature files
            rel_path_str = str(file_path.relative_to(root_path))
            
            if file_path.name in self.framework_signatures:
                content = safe_read_text(file_path)
                if content:
                    for pattern, name in self.framework_signatures[file_path.name]:
                        if re.search(pattern, content):
                            items.append(TechStackItem(
                                name=name,
                                category=TechCategory.FRAMEWORK,
                                confidence=0.9,
                                evidence_files=[rel_path_str]
                            ))
                            
            if file_path.name in self.db_signatures:
                content = safe_read_text(file_path)
                if content:
                    for pattern, name in self.db_signatures[file_path.name]:
                        if re.search(pattern, content):
                            items.append(TechStackItem(
                                name=name,
                                category=TechCategory.DATABASE,
                                confidence=0.8,
                                evidence_files=[rel_path_str]
                            ))
                            
            if file_path.name in self.testing_signatures and isinstance(self.testing_signatures[file_path.name], list):
                content = safe_read_text(file_path)
                if content:
                    for pattern, name in self.testing_signatures[file_path.name]:
                        if re.search(pattern, content):
                            items.append(TechStackItem(
                                name=name,
                                category=TechCategory.TESTING,
                                confidence=0.8,
                                evidence_files=[rel_path_str]
                            ))
                            
            # Check for GitHub actions specifically since it's a folder pattern
            if ".github/workflows" in str(file_path.as_posix()):
                items.append(TechStackItem(
                    name="GitHub Actions",
                    category=TechCategory.CI_CD,
                    confidence=1.0,
                    evidence_files=[rel_path_str]
                ))

        # Add detected languages
        total_source_files = sum(lang_counts.values())
        for lang, count in lang_counts.items():
            items.append(TechStackItem(
                name=lang,
                category=TechCategory.LANGUAGE,
                confidence=min(1.0, count / max(1, total_source_files)),
                evidence_files=lang_files[lang]
            ))
            
        # Add package managers
        for filename, pm_name in self.package_managers.items():
            if filename in detected_files:
                items.append(TechStackItem(
                    name=pm_name,
                    category=TechCategory.PACKAGE_MANAGER,
                    confidence=1.0,
                    evidence_files=[filename]
                ))
                
        # Add testing tools from strict filenames
        for filename, test_name in self.testing_signatures.items():
            if isinstance(test_name, str) and filename in detected_files:
                items.append(TechStackItem(
                    name=test_name,
                    category=TechCategory.TESTING,
                    confidence=1.0,
                    evidence_files=[filename]
                ))
                
        # Add CI/CD
        for filename, cicd_name in self.ci_cd_signatures.items():
            if filename in detected_files:
                items.append(TechStackItem(
                    name=cicd_name,
                    category=TechCategory.CI_CD,
                    confidence=1.0,
                    evidence_files=[filename]
                ))
                
        # Containers
        if "Dockerfile" in detected_files:
            items.append(TechStackItem(
                name="Docker",
                category=TechCategory.CONTAINER,
                confidence=1.0,
                evidence_files=["Dockerfile"]
            ))
        if any(f in detected_files for f in ["docker-compose.yml", "docker-compose.yaml", "compose.yml"]):
            items.append(TechStackItem(
                name="Docker Compose",
                category=TechCategory.CONTAINER,
                confidence=1.0,
                evidence_files=["docker-compose.yml"] # Generic label
            ))

        # Deduplicate items (in case multiple files trigger the same framework)
        unique_items = {}
        for item in items:
            key = (item.name, item.category)
            if key not in unique_items:
                unique_items[key] = item
            else:
                # Merge evidence
                existing = unique_items[key]
                new_evidence = list(set(existing.evidence_files + item.evidence_files))
                unique_items[key] = TechStackItem(
                    name=item.name,
                    category=item.category,
                    confidence=max(existing.confidence, item.confidence),
                    evidence_files=new_evidence[:5] # limit evidence
                )

        return TechStack(items=list(unique_items.values()))
