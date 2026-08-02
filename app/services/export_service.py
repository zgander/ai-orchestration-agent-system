import json
import zipfile
import io
from app.models.investigation_models import InvestigationResult
from app.models.history_models import ExportConfig, ExportFormat

class ExportService:
    def export(self, result: InvestigationResult, config: ExportConfig) -> tuple[str, bytes]:
        if config.format == ExportFormat.JSON:
            return self._export_json(result)
        elif config.format == ExportFormat.MARKDOWN:
            return self._export_markdown(result, config)
        elif config.format == ExportFormat.BUNDLE:
            return self._export_bundle(result, config)
            
    def _export_json(self, result: InvestigationResult) -> tuple[str, bytes]:
        filename = f"{result.plan.repository_name}_investigation.json"
        content = result.model_dump_json(indent=2).encode('utf-8')
        return filename, content
        
    def _export_markdown(self, result: InvestigationResult, config: ExportConfig) -> tuple[str, bytes]:
        filename = f"{result.plan.repository_name}_guide.md"
        guide = result.onboarding_guide
        
        md = f"# Onboarding Guide: {result.plan.repository_name}\n\n"
        if not guide:
            md += "No onboarding guide available."
            return filename, md.encode('utf-8')
            
        md += f"## Mental Model\n{guide.mental_model}\n\n"
        
        if "Architecture" in config.sections:
            md += "## Architecture\n"
            if config.include_diagrams and guide.architecture_diagram:
                md += f"```mermaid\n{guide.architecture_diagram}\n```\n\n"
            md += f"{guide.architecture_explanation}\n\n"
            
        if "Execution Flows" in config.sections and guide.execution_flows:
            md += "## Execution Flows\n"
            for flow in guide.execution_flows:
                md += f"### {flow.name}\n"
                if config.include_diagrams and flow.mermaid_diagram:
                    md += f"```mermaid\n{flow.mermaid_diagram}\n```\n\n"
                for i, step in enumerate(flow.steps):
                    md += f"{i+1}. **{step.get('component', 'Unknown')}** ({step.get('file', '')}): {step.get('description', '')}\n"
                md += "\n"
                
        if "API Explorer" in config.sections and guide.api_explorer:
            md += "## APIs\n"
            for api in guide.api_explorer:
                md += f"### {api.method} {api.path}\n"
                md += f"- **Handler:** {api.handler_function}\n"
                md += f"- **Description:** {api.purpose}\n\n"
                
        return filename, md.encode('utf-8')
        
    def _export_bundle(self, result: InvestigationResult, config: ExportConfig) -> tuple[str, bytes]:
        filename = f"{result.plan.repository_name}_bundle.zip"
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. JSON
            _, json_bytes = self._export_json(result)
            zip_file.writestr("investigation.json", json_bytes)
            
            # 2. Markdown
            _, md_bytes = self._export_markdown(result, config)
            zip_file.writestr("guide.md", md_bytes)
            
        return filename, buffer.getvalue()
