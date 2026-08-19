"""
Telemetry & Observability Engine for Looker & BigQuery Optimization Multi-Agent System.
Provides structured execution tracing, tool latency profiling, sub-agent handoff tracking,
and integration with Firestore / JSON persistence.
"""

import os
import time
import uuid
import json
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager

try:
    from google.adk.plugins import BasePlugin
except ImportError:
    class BasePlugin:
        def __init__(self, name: str = ""):
            self.name = name

logger = logging.getLogger("looker_healthcheck_telemetry")

# Initialize Google Cloud Logging client & handlers
cloud_logging_client = None
gcp_logger = None

try:
    import google.cloud.logging
    from google.cloud.logging.handlers import CloudLoggingHandler, StructuredLogHandler
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or "sampitcher-playground"
    cloud_logging_client = google.cloud.logging.Client(project=gcp_project)
    
    # Direct structured Cloud Logging channel
    gcp_logger = cloud_logging_client.logger("looker_healthcheck_telemetry")
    
    # Attach CloudLoggingHandler to root logger so all logs across the app reach GCP
    cloud_handler = CloudLoggingHandler(cloud_logging_client, name="looker_healthcheck_app")
    cloud_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(cloud_handler)
    
    # Attach StructuredLogHandler for local/container standard formatting
    structured_handler = StructuredLogHandler(project_id=gcp_project)
    logging.getLogger().addHandler(structured_handler)
    
    logger.info("Google Cloud Logging successfully initialized and attached to root logger.")
except Exception as _e:
    logger.warning("Cloud Logging initialization fallback: %s", _e)


def log_cloud_event(event_name: str, payload: Dict[str, Any], level: str = "INFO"):
    """Emits a structured telemetry log event directly to Google Cloud Logging."""
    record = {
        "event": event_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload
    }
    # Direct Cloud Logging API delivery
    if gcp_logger:
        try:
            severity = "ERROR" if level == "ERROR" else ("WARNING" if level == "WARNING" else "INFO")
            gcp_logger.log_struct(record, severity=severity)
        except Exception as e:
            logger.debug("Direct Cloud Logging log_struct error: %s", e)
    
    # Python logger delivery
    if level == "ERROR":
        logger.error(json.dumps(record, default=str))
    elif level == "WARNING":
        logger.warning(json.dumps(record, default=str))
    else:
        logger.info(json.dumps(record, default=str))


def _extract_session_id(ctx) -> str:
    if not ctx:
        return "unknown"
    session = getattr(ctx, "session", None)
    if session and hasattr(session, "id"):
        return str(session.id)
    return getattr(ctx, "session_id", "unknown")


class CloudLoggingPlugin(BasePlugin):
    """
    ADK Lifecycle Plugin that automatically intercepts and streams ALL conversation events,
    user prompts, agent reasoning, model responses, and tool executions to Google Cloud Logging.
    """
    def __init__(self, name: str = "cloud_logging_plugin", project_id: Optional[str] = None):
        super().__init__(name=name)
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "sampitcher-playground")
        self._init_client()

    def _init_client(self):
        global cloud_logging_client, gcp_logger
        if not gcp_logger and cloud_logging_client:
            try:
                gcp_logger = cloud_logging_client.logger("looker_healthcheck_telemetry")
            except Exception:
                pass

    async def on_user_message_callback(self, *, invocation_context, user_message):
        """Streams incoming user messages to Google Cloud Logging."""
        try:
            text_content = []
            if hasattr(user_message, "parts"):
                for p in user_message.parts:
                    if hasattr(p, "text") and p.text:
                        text_content.append(p.text)
            message_text = " ".join(text_content) if text_content else str(user_message)
            
            session_id = _extract_session_id(invocation_context)
            user_id = getattr(invocation_context, "user_id", "unknown")
            invocation_id = getattr(invocation_context, "invocation_id", "unknown")

            log_cloud_event("user_message", {
                "session_id": session_id,
                "user_id": user_id,
                "invocation_id": invocation_id,
                "prompt": message_text,
                "role": "user"
            })
        except Exception as e:
            logger.error("Failed to log user message to Cloud Logging: %s", e)
        return None

    async def before_agent_callback(self, *, agent, callback_context):
        """Logs agent invocation start / subagent dispatch."""
        try:
            agent_name = getattr(agent, "name", str(agent))
            session_id = _extract_session_id(callback_context)
            log_cloud_event("agent_start", {
                "agent_name": agent_name,
                "session_id": session_id
            })
        except Exception as e:
            logger.debug("Error in before_agent_callback logging: %s", e)
        return None

    async def after_agent_callback(self, *, agent, callback_context):
        """Logs agent completion / transition."""
        try:
            agent_name = getattr(agent, "name", str(agent))
            session_id = _extract_session_id(callback_context)
            log_cloud_event("agent_completed", {
                "agent_name": agent_name,
                "session_id": session_id
            })
        except Exception as e:
            logger.debug("Error in after_agent_callback logging: %s", e)
        return None

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        """Logs tool execution start."""
        try:
            tool_name = getattr(tool, "name", str(tool))
            clean_args = {}
            if tool_args and isinstance(tool_args, dict):
                for k, v in tool_args.items():
                    clean_args[k] = v[:200] if isinstance(v, str) and len(v) > 200 else v
            log_cloud_event("tool_start", {
                "tool_name": tool_name,
                "tool_args": clean_args
            })
        except Exception as e:
            logger.debug("Error in before_tool_callback logging: %s", e)
        return None

    async def after_tool_callback(self, *, tool, tool_args, tool_context, result):
        """Logs tool execution completion and result."""
        try:
            tool_name = getattr(tool, "name", str(tool))
            result_str = str(result)
            preview = result_str[:500] if len(result_str) > 500 else result_str
            log_cloud_event("tool_completed", {
                "tool_name": tool_name,
                "result_preview": preview,
                "result_length": len(result_str)
            })
        except Exception as e:
            logger.debug("Error in after_tool_callback logging: %s", e)
        return None

    async def on_tool_error_callback(self, *, tool, tool_args, tool_context, error):
        """Logs tool failure to Cloud Logging."""
        try:
            tool_name = getattr(tool, "name", str(tool))
            log_cloud_event("tool_error", {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "error": str(error)
            }, level="ERROR")
        except Exception as e:
            logger.debug("Error in on_tool_error_callback logging: %s", e)
        return None

    async def on_event_callback(self, *, invocation_context, event):
        """Logs all ADK events (agent responses, tool responses, thoughts)."""
        try:
            author = getattr(event, "author", "unknown")
            event_id = getattr(event, "id", "")
            session_id = getattr(invocation_context, "session_id", "")
            
            content_text = []
            func_calls = []
            func_responses = []
            
            if hasattr(event, "content") and event.content:
                parts = getattr(event.content, "parts", []) or []
                for p in parts:
                    if hasattr(p, "text") and p.text:
                        content_text.append(p.text)
                    if hasattr(p, "function_call") and p.function_call:
                        func_calls.append(getattr(p.function_call, "name", str(p.function_call)))
                    if hasattr(p, "function_response") and p.function_response:
                        func_responses.append(getattr(p.function_response, "name", str(p.function_response)))

            if author != "user":
                payload = {
                    "event_id": event_id,
                    "session_id": session_id,
                    "author": author,
                    "text_preview": ("\n".join(content_text))[:500] if content_text else None,
                    "function_calls": func_calls if func_calls else None,
                    "function_responses": func_responses if func_responses else None
                }
                log_cloud_event(f"event_{author.lower()}", payload)
        except Exception as e:
            logger.debug("Error in on_event_callback logging: %s", e)
        return None


# Global plugin instance for agent app
gcp_logging_plugin = CloudLoggingPlugin()


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
        
        # Stream span directly to Cloud Logging
        log_cloud_event(
            f"span_{self.span_type}_{self.name}",
            self.to_dict(),
            level="ERROR" if status == "ERROR" else "INFO"
        )

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
        log_cloud_event(
            f"tool_execution_{name}",
            span_obj.to_dict(),
            level="ERROR" if status == "ERROR" else "INFO"
        )

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
