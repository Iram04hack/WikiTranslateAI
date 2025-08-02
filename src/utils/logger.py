# -*- coding: utf-8 -*-
"""
Logger system for WikiTranslateAI
"""

import logging
import logging.handlers
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import time
import os


class WikiTranslateLogger:
    """Specialized logger for WikiTranslateAI"""
    
    def __init__(self, name: str = "wikitranslate", log_dir: str = "logs", log_level: str = "INFO"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread-local context
        self._local = threading.local()
        
        # Metrics
        self.metrics = {
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': time.time()
        }
        self._metrics_lock = threading.Lock()
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        # File handler
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def set_context(self, **kwargs):
        """Set context for current thread"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        self._local.context.update(kwargs)
    
    def get_context(self) -> Dict[str, Any]:
        """Get context for current thread"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        return self._local.context.copy()
    
    def _log_with_context(self, level: int, message: str, extra: Optional[Dict] = None):
        """Log with context and metrics"""
        context = self.get_context()
        
        # Update metrics
        with self._metrics_lock:
            self.metrics['total_logs'] += 1
            if level >= logging.ERROR:
                self.metrics['errors'] += 1
            elif level >= logging.WARNING:
                self.metrics['warnings'] += 1
        
        # Add context to message if present
        if context or extra:
            context_info = {**context}
            if extra:
                context_info.update(extra)
            context_str = json.dumps(context_info)
            message = f"{message} | Context: {context_str}"
        
        self.logger.log(level, message)
    
    def info(self, message: str, **kwargs):
        """Log INFO level"""
        self._log_with_context(logging.INFO, message, kwargs or None)
    
    def debug(self, message: str, **kwargs):
        """Log DEBUG level"""
        self._log_with_context(logging.DEBUG, message, kwargs or None)
    
    def warning(self, message: str, **kwargs):
        """Log WARNING level"""
        self._log_with_context(logging.WARNING, message, kwargs or None)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log ERROR level with optional stack trace"""
        extra_data = kwargs or {}
        
        if exception:
            extra_data['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        self._log_with_context(logging.ERROR, message, extra_data)
    
    # Specialized methods for WikiTranslateAI
    
    def log_translation_start(self, article_title: str, source_lang: str, target_lang: str):
        """Log translation start"""
        self.set_context(
            operation='translation',
            article=article_title,
            source_lang=source_lang,
            target_lang=target_lang
        )
        self.info(f"Translation started: {article_title} ({source_lang} -> {target_lang})")
    
    def log_translation_complete(self, success: bool, duration_s: float):
        """Log translation completion"""
        context = self.get_context()
        article = context.get('article', 'Unknown')
        status = "COMPLETED" if success else "FAILED"
        self.info(f"Translation {status}: {article} ({duration_s:.2f}s)")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logger metrics"""
        with self._metrics_lock:
            uptime_s = time.time() - self.metrics['start_time']
            return {
                **self.metrics,
                'uptime_seconds': uptime_s,
                'error_rate': self.metrics['errors'] / max(self.metrics['total_logs'], 1)
            }


# Global instance
_default_logger: Optional[WikiTranslateLogger] = None

def get_logger(name: str = "wikitranslate") -> WikiTranslateLogger:
    """Get logger instance"""
    global _default_logger
    if _default_logger is None:
        _default_logger = WikiTranslateLogger(name)
    return _default_logger

Logger = WikiTranslateLogger
logger = get_logger()