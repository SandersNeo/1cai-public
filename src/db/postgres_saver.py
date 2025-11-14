"""
PostgreSQL Saver for 1C Configurations
Версия: 2.0.0

Улучшения:
- Улучшенная обработка ошибок с retry logic
- Connection pooling support
- Structured logging
- Graceful degradation при ошибках подключения
"""

import os
import hashlib
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import execute_values, Json
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from psycopg2 import pool, OperationalError, DatabaseError
except ImportError:
    raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class PostgreSQLSaver:
    """Saves parsed 1C configurations to PostgreSQL"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "knowledge_base",
                 user: str = "admin",
                 password: str = None):
        """Initialize PostgreSQL connection с input validation"""
        
        # Input validation
        if not isinstance(host, str) or not host:
            logger.warning(
                "Invalid host in PostgreSQLSaver.__init__",
                extra={"host": host, "host_type": type(host).__name__}
            )
            host = "localhost"
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.warning(
                "Invalid port in PostgreSQLSaver.__init__",
                extra={"port": port, "port_type": type(port).__name__}
            )
            port = 5432
        
        if not isinstance(database, str) or not database:
            logger.warning(
                "Invalid database in PostgreSQLSaver.__init__",
                extra={"database": database, "database_type": type(database).__name__}
            )
            database = "knowledge_base"
        
        if not isinstance(user, str) or not user:
            logger.warning(
                "Invalid user in PostgreSQLSaver.__init__",
                extra={"user": user, "user_type": type(user).__name__}
            )
            user = "admin"
        
        # Get password from env if not provided
        if not password:
            password = os.getenv("POSTGRES_PASSWORD")
        
        if not password or not isinstance(password, str):
            logger.error(
                "PostgreSQL password not provided",
                extra={"has_password": bool(password)}
            )
            raise ValueError("PostgreSQL password not provided")
        
        self.conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        
        self.conn = None
        self.cur = None
        
        logger.debug(
            "PostgreSQLSaver initialized",
            extra={"host": host, "port": port, "database": database, "user": user}
        )
        
    def connect(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Establish database connection with retry logic с input validation
        
        Best practices:
        - Retry для transient errors
        - Exponential backoff
        - Structured logging
        """
        # Input validation
        if not isinstance(max_retries, int) or max_retries < 1:
            logger.warning(
                "Invalid max_retries in PostgreSQLSaver.connect",
                extra={"max_retries": max_retries, "max_retries_type": type(max_retries).__name__}
            )
            max_retries = 3
        
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            logger.warning(
                "Invalid retry_delay in PostgreSQLSaver.connect",
                extra={"retry_delay": retry_delay, "retry_delay_type": type(retry_delay).__name__}
            )
            retry_delay = 1.0
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(**self.conn_params)
                self.cur = self.conn.cursor()
                logger.info(
                    f"Connected to PostgreSQL at {self.conn_params['host']}",
                    extra={
                        "host": self.conn_params['host'],
                        "database": self.conn_params['database'],
                        "attempt": attempt + 1
                    }
                )
                return True
            except OperationalError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Failed to connect to PostgreSQL (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "error": str(e)
                        }
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to connect to PostgreSQL after {max_retries} attempts: {e}",
                        exc_info=True,
                        extra={
                            "host": self.conn_params['host'],
                            "database": self.conn_params['database'],
                            "max_retries": max_retries
                        }
                    )
            except Exception as e:
                logger.error(
                    f"Unexpected error connecting to PostgreSQL: {e}",
                    exc_info=True,
                    extra={
                        "host": self.conn_params['host'],
                        "database": self.conn_params['database'],
                        "error_type": type(e).__name__
                    }
                )
                return False
        
        return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Disconnected from PostgreSQL")
    
    def save_configuration(self, config_data: Dict[str, Any]) -> Optional[str]:
        """
        Save configuration to database
        Returns configuration ID
        """
        try:
            # Check if configuration exists
            self.cur.execute(
                "SELECT id FROM configurations WHERE name = %s",
                (config_data['name'],)
            )
            result = self.cur.fetchone()
            
            if result:
                config_id = result[0]
                # Update existing
                self.cur.execute("""
                    UPDATE configurations 
                    SET full_name = %s,
                        version = %s,
                        source_path = %s,
                        metadata = %s,
                        parsed_at = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                """, (
                    config_data.get('full_name'),
                    config_data.get('version'),
                    config_data.get('source_path'),
                    Json(config_data.get('metadata', {})),
                    datetime.now(),
                    config_id
                ))
                logger.info(
                    "Updated configuration",
                    extra={"config_name": config_data['name']}
                )
            else:
                # Insert new
                self.cur.execute("""
                    INSERT INTO configurations (name, full_name, version, source_path, metadata, parsed_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    config_data['name'],
                    config_data.get('full_name'),
                    config_data.get('version'),
                    config_data.get('source_path'),
                    Json(config_data.get('metadata', {})),
                    datetime.now()
                ))
                config_id = self.cur.fetchone()[0]
                logger.info(
                    "Created configuration",
                    extra={"config_name": config_data['name']}
                )
            
            self.conn.commit()
            return config_id
            
        except Exception as e:
            logger.error(
                "Error saving configuration",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "config_name": config_data.get('name') if 'config_data' in locals() else None
                },
                exc_info=True
            )
            self.conn.rollback()
            return None
    
    def save_object(self, config_id: str, object_data: Dict[str, Any]) -> Optional[str]:
        """Save 1C object (Document, Catalog, etc.)"""
        try:
            self.cur.execute("""
                INSERT INTO objects (
                    configuration_id, object_type, name, synonym, description, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (configuration_id, object_type, name) 
                DO UPDATE SET 
                    synonym = EXCLUDED.synonym,
                    description = EXCLUDED.description,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING id
            """, (
                config_id,
                object_data['type'],
                object_data['name'],
                object_data.get('synonym'),
                object_data.get('description'),
                Json(object_data.get('metadata', {}))
            ))
            
            object_id = self.cur.fetchone()[0]
            self.conn.commit()
            return object_id
            
        except Exception as e:
            logger.error(
                "Error saving object",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "object_name": object_data.get('name') if 'object_data' in locals() else None
                },
                exc_info=True
            )
            self.conn.rollback()
            return None
    
    def save_module(self, config_id: str, module_data: Dict[str, Any], 
                   object_id: Optional[str] = None) -> Optional[str]:
        """Save BSL module"""
        try:
            # Calculate code hash
            code = module_data.get('code', '')
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            # Count lines
            line_count = len(code.split('\n')) if code else 0
            
            self.cur.execute("""
                INSERT INTO modules (
                    configuration_id, object_id, name, module_type, 
                    code, code_hash, description, source_file, line_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                config_id,
                object_id,
                module_data['name'],
                module_data.get('module_type'),
                code,
                code_hash,
                module_data.get('description'),
                module_data.get('source_file'),
                line_count
            ))
            
            module_id = self.cur.fetchone()[0]
            self.conn.commit()
            
            # Save functions
            for func in module_data.get('functions', []):
                self.save_function(module_id, func)
            
            # Save procedures
            for proc in module_data.get('procedures', []):
                self.save_function(module_id, proc)
            
            # Save API usage
            for api in module_data.get('api_usage', []):
                self.save_api_usage(module_id, api)
            
            # Save regions
            for region in module_data.get('regions', []):
                self.save_region(module_id, region)
            
            return module_id
            
        except Exception as e:
            logger.error(
                "Error saving module",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "module_name": module_data.get('name') if 'module_data' in locals() else None
                },
                exc_info=True
            )
            self.conn.rollback()
            return None
    
    def save_function(self, module_id: str, func_data: Dict[str, Any]) -> Optional[str]:
        """Save function or procedure"""
        try:
            # Determine type
            func_type = func_data.get('type', 'Function')
            
            # Calculate complexity (simple estimate based on code)
            code = func_data.get('code', '')
            complexity_score = self._calculate_complexity(code)
            
            self.cur.execute("""
                INSERT INTO functions (
                    module_id, name, function_type, is_exported,
                    parameters, return_type, region, description, code,
                    start_line, end_line, complexity_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                module_id,
                func_data['name'],
                func_type,
                func_data.get('exported', False),
                Json(func_data.get('params', [])),
                func_data.get('return_type'),
                func_data.get('region'),
                func_data.get('comments', ''),
                code,
                func_data.get('start_line'),
                func_data.get('end_line'),
                complexity_score
            ))
            
            func_id = self.cur.fetchone()[0]
            self.conn.commit()
            return func_id
            
        except Exception as e:
            logger.error(
                "Error saving function",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "function_name": func_data.get('name') if 'func_data' in locals() else None
                },
                exc_info=True
            )
            self.conn.rollback()
            return None
    
    def save_api_usage(self, module_id: str, api_name: str) -> bool:
        """Save API usage"""
        try:
            self.cur.execute("""
                INSERT INTO api_usage (module_id, api_name, usage_count)
                VALUES (%s, %s, 1)
                ON CONFLICT (module_id, api_name)
                DO UPDATE SET usage_count = api_usage.usage_count + 1
            """, (module_id, api_name))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(
                "Error saving API usage",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "api_name": api_name
                },
                exc_info=True
            )
            self.conn.rollback()
            return False
    
    def save_region(self, module_id: str, region_data: Dict[str, Any]) -> Optional[str]:
        """Save code region"""
        try:
            self.cur.execute("""
                INSERT INTO regions (
                    module_id, name, start_line, end_line, level
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                module_id,
                region_data['name'],
                region_data.get('start_line'),
                region_data.get('end_line'),
                region_data.get('level', 0)
            ))
            
            region_id = self.cur.fetchone()[0]
            self.conn.commit()
            return region_id
            
        except Exception as e:
            logger.error(
                "Error saving region",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "region_name": region_data.get('name') if 'region_data' in locals() else None
                },
                exc_info=True
            )
            self.conn.rollback()
            return None
    
    def _calculate_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity (simple approximation)"""
        if not code:
            return 0
        
        # Count decision points
        keywords = ['Если', 'If', 'Иначе', 'Else', 'ИначеЕсли', 'ElseIf',
                   'Пока', 'While', 'Для', 'For', 'Попытка', 'Try',
                   'Исключение', 'Except', 'И', 'And', 'Или', 'Or']
        
        complexity = 1  # Base complexity
        code_lower = code.lower()
        
        for keyword in keywords:
            complexity += code_lower.count(keyword.lower())
        
        return complexity
    
    def clear_configuration(self, config_name: str) -> bool:
        """Clear all data for a configuration before re-parsing"""
        try:
            # Get configuration ID
            self.cur.execute(
                "SELECT id FROM configurations WHERE name = %s",
                (config_name,)
            )
            result = self.cur.fetchone()
            
            if not result:
                return True  # Nothing to clear
            
            config_id = result[0]
            
            # Delete in correct order (respecting foreign keys)
            tables = [
                'api_usage',
                'regions',
                'functions',
                'modules',
                'objects'
            ]
            
            # Whitelist of allowed tables for security
            allowed_tables = {'api_usage', 'regions', 'functions', 'modules', 'objects'}
            
            for table in tables:
                # Security check: ensure table name is in whitelist
                if table not in allowed_tables:
                    logger.warning(
                        "Attempted to delete from non-whitelisted table",
                        extra={"table": table}
                    )
                    continue
                
                if table == 'modules':
                    self.cur.execute("DELETE FROM modules WHERE configuration_id = %s", (config_id,))
                elif table == 'objects':
                    self.cur.execute("DELETE FROM objects WHERE configuration_id = %s", (config_id,))
                elif table == 'api_usage':
                    self.cur.execute("""
                        DELETE FROM api_usage 
                        WHERE module_id IN (
                            SELECT id FROM modules WHERE configuration_id = %s
                        )
                    """, (config_id,))
                elif table == 'regions':
                    self.cur.execute("""
                        DELETE FROM regions 
                        WHERE module_id IN (
                            SELECT id FROM modules WHERE configuration_id = %s
                        )
                    """, (config_id,))
                elif table == 'functions':
                    self.cur.execute("""
                        DELETE FROM functions 
                        WHERE module_id IN (
                            SELECT id FROM modules WHERE configuration_id = %s
                        )
                    """, (config_id,))
            
            self.conn.commit()
            logger.info(
                "Cleared data for configuration",
                extra={"config_name": config_name}
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error clearing configuration",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "config_name": config_name if 'config_name' in locals() else None
                },
                exc_info=True
            )
            self.conn.rollback()
            return False
    
    def get_statistics(self, config_name: Optional[str] = None) -> Dict[str, int]:
        """Get parsing statistics"""
        try:
            where_clause = ""
            params = []
            
            if config_name:
                where_clause = "WHERE c.name = %s"
                params = [config_name]
            
            # Build query safely without f-string interpolation
            base_query = """
                SELECT 
                    COUNT(DISTINCT c.id) as configs,
                    COUNT(DISTINCT o.id) as objects,
                    COUNT(DISTINCT m.id) as modules,
                    COUNT(DISTINCT f.id) as functions,
                    SUM(m.line_count) as total_lines
                FROM configurations c
                LEFT JOIN objects o ON o.configuration_id = c.id
                LEFT JOIN modules m ON m.configuration_id = c.id
                LEFT JOIN functions f ON f.module_id = m.id
            """
            
            if where_clause:
                full_query = base_query + " " + where_clause
            else:
                full_query = base_query
            
            self.cur.execute(full_query, params)
            
            result = self.cur.fetchone()
            
            return {
                'configurations': result[0] or 0,
                'objects': result[1] or 0,
                'modules': result[2] or 0,
                'functions': result[3] or 0,
                'total_lines': result[4] or 0
            }
            
        except Exception as e:
            logger.error(
                "Error getting statistics",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {}
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()







