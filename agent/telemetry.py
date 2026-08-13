"""
Telemetry & Observability Engine for Looker & BigQuery Optimization Multi-Agent System.
Provides structured execution tracing, tool latency profiling, sub-agent handoff tracking,
and integration with Firestore / JSON persistence.
"""

import time
import uuid
import json
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager

logger = logging.getLogger("looker_healthcheck_telemetry")


class TelemetrySpan:
    """Represents a single timed unit of work (tool call, subagent invocation, LLM step)."""
    def __init__(self, name: str, span_type: str = "tool", parent_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        self.span_id = str(uuid.uuid4())[:8]
        self.parent_id = parent_id
        self.name = name
        self.span_type = span_type  # "tool", "subagent", "llm", "persistence", "skill_lookup"
        self.start_time = time.time()
        self.start_iso = datetime.now(timezone.utc).isoformat()
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
        self.status = "RUNNING"  # "SUCCESS", "ERROR", "WARNING"
        self.error: Optional[str] = None
        self.attributes: Dict[str, Any] = attributes or {}

    def finish(self, status: str = "SUCCESS", error: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        if error:
            self.error = str(error)
        if attributes:
            self.attributes.update(attributes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "span_type": self.span_type,
            "start_time": self.start_iso,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes
        }


class TelemetryTracer:
    """Manages an active trace session spanning root orchestrator and subagents."""
    def __init__(self):
        self.trace_id: str = ""
        self.session_id: str = ""
        self.start_time: float = 0.0
        self.end_time: Optional[float] = None
        self.spans: List[TelemetrySpan] = []
        self.metadata: Dict[str, Any] = {}
        self.is_active: bool = False

    def start_trace(self, session_id: Optional[str] = None, prompt: Optional[str] = None, model_scope: Optional[str] = None) -> str:
        self.trace_id = f"trace_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.end_time = None
        self.spans = []
        self.metadata = {
            "prompt": prompt or "",
            "model_scope": model_scope or "all_models",
            "start_iso": datetime.now(timezone.utc).isoformat()
        }
        self.is_active = True
        return self.trace_id

    def end_trace(self, status: str = "COMPLETED") -> Dict[str, Any]:
        self.end_time = time.time()
        self.is_active = False
        summary = self.get_summary()
        summary["final_status"] = status
        return summary

    @contextmanager
    def span(self, name: str, span_type: str = "tool", parent_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing blocks of code."""
        span_obj = TelemetrySpan(name=name, span_type=span_type, parent_id=parent_id, attributes=attributes)
        self.spans.append(span_obj)
        try:
            yield span_obj
            span_obj.finish(status="SUCCESS")
        except Exception as ex:
            span_obj.finish(status="ERROR", error=str(ex))
            raise

    def record_tool(self, name: str, duration_ms: float, status: str = "SUCCESS", error: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        """Directly records a tool execution."""
        span_obj = TelemetrySpan(name=name, span_type="tool", attributes=attributes)
        span_obj.duration_ms = duration_ms
        span_obj.status = status
        span_obj.error = error
        self.spans.append(span_obj)

    def get_summary(self) -> Dict[str, Any]:
        total_duration_ms = round((time.time() - self.start_time) * 1000, 2) if self.start_time else 0.0
        tool_spans = [s for s in self.spans if s.span_type == "tool"]
        error_spans = [s for s in self.spans if s.status == "ERROR"]
        
        slow_tools = [
            {"name": s.name, "duration_ms": s.duration_ms}
            for s in sorted(tool_spans, key=lambda x: x.duration_ms, reverse=True)
            if s.duration_ms > 2000
        ]

        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "total_duration_ms": total_duration_ms,
            "total_spans": len(self.spans),
            "tool_calls_count": len(tool_spans),
            "error_count": len(error_spans),
            "slow_tools_count": len(slow_tools),
            "slowest_tools": slow_tools[:5],
            "metadata": self.metadata
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "summary": self.get_summary(),
            "spans": [s.to_dict() for s in self.spans]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# Global tracer instance
global_tracer = TelemetryTracer()


def trace_tool(tool_name: Optional[str] = None, span_type: str = "tool"):
    """Decorator to automatically profile and trace tool execution latencies and outcomes."""
    def decorator(func: Callable):
        name = tool_name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = "SUCCESS"
            error_msg = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "ERROR"
                error_msg = str(e)
                raise
            finally:
                duration_ms = round((time.time() - start) * 1000, 2)
                attrs = {}
                if kwargs.get("model_name"):
                    attrs["model_name"] = kwargs["model_name"]
                if kwargs.get("project_id"):
                    attrs["project_id"] = kwargs["project_id"]
                global_tracer.record_tool(name=name, duration_ms=duration_ms, status=status, error=error_msg, attributes=attrs)
        return wrapper
    return decorator
