# Init
# Resolve forward references after all models are imported
from app.models.investigation_models import InvestigationResult
from app.models.review_models import ReviewReport
from app.models.onboarding_models import OnboardingGuide

InvestigationResult.model_rebuild()
