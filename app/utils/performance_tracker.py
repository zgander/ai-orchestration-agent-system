import time
from typing import Dict, Optional, List
from datetime import datetime, timezone
import streamlit as st

from app.models.history_models import PerformanceMetrics
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceTracker:
    def __init__(self):
        # We store the active metrics in session state to persist across reruns
        if "performance_metrics" not in st.session_state:
            st.session_state.performance_metrics = PerformanceMetrics(recorded_at=datetime.now(timezone.utc))
        self._active_timers: Dict[str, float] = {}

    @property
    def metrics(self) -> PerformanceMetrics:
        return st.session_state.performance_metrics

    def start_timer(self, name: str) -> None:
        self._active_timers[name] = time.time()

    def stop_timer(self, name: str, category: str = "general") -> float:
        if name not in self._active_timers:
            logger.warning(f"Timer {name} was not started.")
            return 0.0
            
        duration = time.time() - self._active_timers.pop(name)
        
        # Update specific metric based on category/name
        if category == "repo_load":
            self.metrics.repo_load_time_seconds = duration
        elif category == "analysis":
            self.metrics.analysis_duration_seconds = duration
        elif category == "agent":
            self.metrics.agent_durations[name] = duration
        elif category == "reviewer":
            self.metrics.reviewer_duration_seconds = duration
        elif category == "synthesis":
            self.metrics.synthesis_duration_seconds = duration
        elif category == "chat":
            self.metrics.chat_latencies.append(duration)
            
        return duration

    def record_cache_hit(self) -> None:
        self.metrics.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.metrics.cache_misses += 1

    def get_metrics(self) -> PerformanceMetrics:
        return self.metrics

    def reset(self) -> None:
        st.session_state.performance_metrics = PerformanceMetrics(recorded_at=datetime.now(timezone.utc))
        self._active_timers.clear()
