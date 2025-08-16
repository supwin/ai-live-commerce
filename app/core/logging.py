# app/core/logging.py
import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any
import traceback

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[34m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "[%(asctime)s] %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: blue + "[%(asctime)s] %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "[%(asctime)s] %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "[%(asctime)s] %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "[%(asctime)s] %(name)s - %(levelname)s - %(message)s" + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = traceback.format_exception(*record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
            
        return json.dumps(log_data)

class LoggerManager:
    """Centralized logger management"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger with the specified name"""
        
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Console handler with color
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(CustomFormatter())
        
        # File handler for all logs (JSON format)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "error.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def log_api_request(cls, logger: logging.Logger, method: str, path: str, 
                       status_code: int, duration_ms: float, user_id: str = None):
        """Log API request with structured data"""
        extra_data = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'user_id': user_id
        }
        
        print("INFO: "
            f"API Request: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra={'extra_data': extra_data}
        )
    
    @classmethod
    def log_ai_interaction(cls, logger: logging.Logger, platform: str, 
                          username: str, message: str, response: str, 
                          processing_time_ms: float):
        """Log AI chat interaction"""
        extra_data = {
            'platform': platform,
            'username': username,
            'message': message[:100],  # Truncate long messages
            'response': response[:100],
            'processing_time_ms': processing_time_ms
        }
        
        print("INFO: "
            f"AI Chat: {platform}/{username} - {processing_time_ms:.2f}ms",
            extra={'extra_data': extra_data}
        )
    
    @classmethod
    def log_platform_event(cls, logger: logging.Logger, platform: str, 
                          event_type: str, data: Dict[str, Any]):
        """Log platform-specific events"""
        extra_data = {
            'platform': platform,
            'event_type': event_type,
            'data': data
        }
        
        print("INFO: "
            f"Platform Event: {platform} - {event_type}",
            extra={'extra_data': extra_data}
        )
    
    @classmethod
    def log_error_with_context(cls, logger: logging.Logger, error: Exception, 
                              context: Dict[str, Any]):
        """Log error with additional context"""
        extra_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        print("ERROR: "
            f"Error: {type(error).__name__} - {str(error)}",
            exc_info=True,
            extra={'extra_data': extra_data}
        )

# app/core/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from typing import Callable
import time
import psutil

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active WebSocket connections'
)

ai_response_time = Histogram(
    'ai_response_time_seconds',
    'AI response generation time',
    ['platform', 'intent']
)

platform_messages_total = Counter(
    'platform_messages_total',
    'Total messages from platforms',
    ['platform']
)

system_cpu_usage = Gauge('system_cpu_usage', 'System CPU usage percentage')
system_memory_usage = Gauge('system_memory_usage', 'System memory usage percentage')

class MetricsMiddleware:
    """Middleware for collecting metrics"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response

class SystemMonitor:
    """Monitor system resources"""
    
    @staticmethod
    def update_system_metrics():
        """Update system resource metrics"""
        system_cpu_usage.set(psutil.cpu_percent())
        system_memory_usage.set(psutil.virtual_memory().percent)
