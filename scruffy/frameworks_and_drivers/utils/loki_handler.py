"""Loki logging handler for shipping logs directly to Grafana Loki."""

import json
import logging
import sys
import time
from datetime import UTC, datetime
from typing import Any

import httpx


class JsonFormatter(logging.Formatter):
    """Format log records as JSON strings for structured logging."""

    # Standard LogRecord attributes to exclude from extra fields
    RESERVED_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        # Build the base log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add location info for errors and above
        if record.levelno >= logging.ERROR:
            log_entry["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add stack info if present
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info

        # Add any extra fields that were passed to the logger
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class LokiHandler(logging.Handler):
    """
    A logging handler that sends logs to Grafana Loki via HTTP push API.

    Logs are formatted as JSON and sent to Loki's /loki/api/v1/push endpoint.
    Connection failures are handled gracefully - errors are printed to stderr
    but don't crash the application.
    """

    # Loggers to ignore to prevent infinite recursion
    # (httpx/httpcore log HTTP requests, which would trigger more logs)
    IGNORED_LOGGERS = frozenset({"httpx", "httpcore", "urllib3", "requests"})

    def __init__(
        self,
        url: str,
        labels: dict[str, str] | None = None,
        timeout: float = 10.0,
        level: int = logging.NOTSET,
    ):
        """
        Initialize the Loki handler.

        Args:
            url: Loki push API URL (e.g., "http://loki:3100/loki/api/v1/push")
            labels: Static labels to attach to all log streams
            timeout: HTTP request timeout in seconds
            level: Minimum log level to handle
        """
        super().__init__(level)
        self.url = url
        self.labels = labels or {"app": "scruffy"}
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self.setFormatter(JsonFormatter())
        self._emitting = False  # Guard against re-entrancy

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to Loki.

        Args:
            record: The log record to send
        """
        # Prevent infinite recursion: skip logs from HTTP client libraries
        # and guard against re-entrancy during emit
        logger_root = record.name.split(".")[0]
        if logger_root in self.IGNORED_LOGGERS or self._emitting:
            return

        self._emitting = True
        try:
            # Format the log message as JSON
            msg = self.format(record)

            # Build Loki payload
            # Loki expects timestamps in nanoseconds
            timestamp_ns = str(int(time.time() * 1_000_000_000))

            # Add level to labels for easier filtering in Grafana
            stream_labels = {**self.labels, "level": record.levelname.lower()}

            payload = {
                "streams": [
                    {
                        "stream": stream_labels,
                        "values": [[timestamp_ns, msg]],
                    }
                ]
            }

            # Send to Loki
            response = self._client.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            # Log to stderr but don't crash
            print(
                f"Loki handler HTTP error: {e.response.status_code} - {e.response.text}",
                file=sys.stderr,
            )
        except httpx.RequestError as e:
            # Connection errors, timeouts, etc.
            print(f"Loki handler connection error: {e}", file=sys.stderr)
        except Exception as e:
            # Catch-all for unexpected errors
            print(f"Loki handler unexpected error: {e}", file=sys.stderr)
        finally:
            self._emitting = False

    def close(self) -> None:
        """Close the HTTP client when the handler is closed."""
        self._client.close()
        super().close()


class AsyncLokiHandler(logging.Handler):
    """
    An async-compatible Loki handler that uses httpx.AsyncClient.

    Note: This handler queues logs and sends them synchronously in emit()
    since Python's logging doesn't support async emit. For true async,
    consider using a background task or queue.
    """

    # Loggers to ignore to prevent infinite recursion
    IGNORED_LOGGERS = frozenset({"httpx", "httpcore", "urllib3", "requests"})

    def __init__(
        self,
        url: str,
        labels: dict[str, str] | None = None,
        timeout: float = 10.0,
        level: int = logging.NOTSET,
    ):
        """
        Initialize the async Loki handler.

        Args:
            url: Loki push API URL
            labels: Static labels to attach to all log streams
            timeout: HTTP request timeout in seconds
            level: Minimum log level to handle
        """
        super().__init__(level)
        self.url = url
        self.labels = labels or {"app": "scruffy"}
        self.timeout = timeout
        self.setFormatter(JsonFormatter())
        self._emitting = False  # Guard against re-entrancy

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to Loki using a sync client.

        For simplicity, this uses a synchronous request. In high-throughput
        scenarios, consider batching logs or using a background queue.
        """
        # Prevent infinite recursion: skip logs from HTTP client libraries
        logger_root = record.name.split(".")[0]
        if logger_root in self.IGNORED_LOGGERS or self._emitting:
            return

        self._emitting = True
        try:
            msg = self.format(record)
            timestamp_ns = str(int(time.time() * 1_000_000_000))
            stream_labels = {**self.labels, "level": record.levelname.lower()}

            payload = {
                "streams": [
                    {
                        "stream": stream_labels,
                        "values": [[timestamp_ns, msg]],
                    }
                ]
            }

            # Use a fresh client for each request to avoid async context issues
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            print(
                f"Loki handler HTTP error: {e.response.status_code} - {e.response.text}",
                file=sys.stderr,
            )
        except httpx.RequestError as e:
            print(f"Loki handler connection error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Loki handler unexpected error: {e}", file=sys.stderr)
        finally:
            self._emitting = False
