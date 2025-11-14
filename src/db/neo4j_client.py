"""
Neo4j Client for 1C Metadata Graph
Manages graph database operations
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from neo4j import GraphDatabase, Driver, Session
    NEO4J_AVAILABLE = True
except ImportError:
    import sys
    import types

    NEO4J_AVAILABLE = False

    class _StubDriver:
        def verify_connectivity(self):
            raise ImportError("neo4j driver not installed")

        def session(self):
            raise ImportError("neo4j driver not installed")

        def close(self):
            pass

    class _StubGraphDatabase:
        @staticmethod
        def driver(*args, **kwargs):
            raise ImportError("neo4j driver not installed")

    GraphDatabase = _StubGraphDatabase  # type: ignore[assignment]
    Driver = Any  # type: ignore[assignment]
    Session = Any  # type: ignore[assignment]

    neo4j_stub = types.ModuleType("neo4j")
    neo4j_stub.GraphDatabase = _StubGraphDatabase
    sys.modules.setdefault("neo4j", neo4j_stub)

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Логируем предупреждение о недоступности neo4j после настройки logger
if not NEO4J_AVAILABLE:
    logger.warning("neo4j driver not installed. Run: pip install neo4j")


class Neo4jClient:
    """Neo4j client for 1C metadata graph"""
    
    def __init__(self, 
                 uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = None):
        """Initialize Neo4j connection с input validation"""
        
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available; running in stub mode")
        
        # Input validation
        if not isinstance(uri, str) or not uri:
            logger.warning(
                "Invalid uri in Neo4jClient.__init__",
                extra={"uri": uri, "uri_type": type(uri).__name__}
            )
            uri = "bolt://localhost:7687"
        
        if not isinstance(user, str) or not user:
            logger.warning(
                "Invalid user in Neo4jClient.__init__",
                extra={"user": user, "user_type": type(user).__name__}
            )
            user = "neo4j"
        
        # Get password from env if not provided
        if not password:
            password = os.getenv("NEO4J_PASSWORD", "password")
        
        if not password or not isinstance(password, str):
            logger.warning(
                "Invalid password in Neo4jClient.__init__",
                extra={"has_password": bool(password)}
            )
            password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None
        
        logger.debug(
            "Neo4jClient initialized",
            extra={"uri": uri, "user": user}
        )
    
    def connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        Establish connection to Neo4j with retry logic с input validation
        
        Best practices:
        - Retry для transient errors
        - Exponential backoff
        - Structured logging
        """
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available; cannot connect")
            return False
        
        # Input validation
        if not isinstance(max_retries, int) or max_retries < 1:
            logger.warning(
                "Invalid max_retries in Neo4jClient.connect",
                extra={"max_retries": max_retries, "max_retries_type": type(max_retries).__name__}
            )
            max_retries = 3
        
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            logger.warning(
                "Invalid retry_delay in Neo4jClient.connect",
                extra={"retry_delay": retry_delay, "retry_delay_type": type(retry_delay).__name__}
            )
            retry_delay = 1.0
        
        import time
        
        for attempt in range(max_retries):
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )
                # Test connection
                self.driver.verify_connectivity()
                logger.info(
                    f"Connected to Neo4j at {self.uri}",
                    extra={
                        "uri": self.uri,
                        "attempt": attempt + 1
                    }
                )
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Failed to connect to Neo4j (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...",
                        extra={
                            "uri": self.uri,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "error": str(e)
                        }
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to connect to Neo4j after {max_retries} attempts: {e}",
                        exc_info=True,
                        extra={
                            "uri": self.uri,
                            "max_retries": max_retries
                        }
                    )
                    return False
        
        return False
    
    def disconnect(self):
        """Close connection"""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    def create_constraints(self):
        """Create uniqueness constraints and indexes"""
        with self.driver.session() as session:
            constraints = [
                # Configuration
                "CREATE CONSTRAINT config_name IF NOT EXISTS FOR (c:Configuration) REQUIRE c.name IS UNIQUE",
                
                # Object
                "CREATE CONSTRAINT object_unique IF NOT EXISTS FOR (o:Object) REQUIRE (o.configuration, o.type, o.name) IS UNIQUE",
                
                # Module
                "CREATE CONSTRAINT module_name IF NOT EXISTS FOR (m:Module) REQUIRE m.full_name IS UNIQUE",
                
                # Function
                "CREATE CONSTRAINT function_signature IF NOT EXISTS FOR (f:Function) REQUIRE (f.module_name, f.name) IS UNIQUE",
            ]
            
            indexes = [
                "CREATE INDEX obj_type IF NOT EXISTS FOR (o:Object) ON (o.type)",
                "CREATE INDEX mod_type IF NOT EXISTS FOR (m:Module) ON (m.module_type)",
                "CREATE INDEX func_name IF NOT EXISTS FOR (f:Function) ON (f.name)",
                "CREATE INDEX func_exported IF NOT EXISTS FOR (f:Function) ON (f.is_exported)",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(
                        "Created constraint",
                        extra={"constraint_preview": constraint[:50] if constraint else None}
                    )
                except Exception as e:
                    logger.warning(
                        "Constraint already exists or error",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "constraint_preview": constraint[:50] if constraint else None
                        }
                    )
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(
                        "Created index",
                        extra={"index_preview": index[:50] if index else None}
                    )
                except Exception as e:
                    logger.warning(
                        "Index already exists or error",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "index_preview": index[:50] if index else None
                        }
                    )
    
    def create_configuration(self, config_data: Dict[str, Any]) -> bool:
        """Create Configuration node"""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (c:Configuration {name: $name})
                ON CREATE SET 
                    c.full_name = $full_name,
                    c.version = $version,
                    c.created_at = datetime(),
                    c.metadata = $metadata
                ON MATCH SET
                    c.full_name = $full_name,
                    c.version = $version,
                    c.updated_at = datetime(),
                    c.metadata = $metadata
                RETURN c
            """, 
                name=config_data['name'],
                full_name=config_data.get('full_name', ''),
                version=config_data.get('version', ''),
                metadata=config_data.get('metadata', {})
            )
            return result.single() is not None
    
    def create_object(self, config_name: str, object_data: Dict[str, Any]) -> bool:
        """Create Object node and link to Configuration"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Configuration {name: $config_name})
                MERGE (o:Object {
                    configuration: $config_name,
                    type: $type,
                    name: $name
                })
                ON CREATE SET
                    o.synonym = $synonym,
                    o.description = $description,
                    o.created_at = datetime()
                ON MATCH SET
                    o.synonym = $synonym,
                    o.description = $description,
                    o.updated_at = datetime()
                MERGE (c)-[:HAS_OBJECT]->(o)
                RETURN o
            """,
                config_name=config_name,
                type=object_data['type'],
                name=object_data['name'],
                synonym=object_data.get('synonym', ''),
                description=object_data.get('description', '')
            )
            return result.single() is not None
    
    def create_module(self, config_name: str, module_data: Dict[str, Any]) -> bool:
        """Create Module node and relationships"""
        with self.driver.session() as session:
            # Create module
            result = session.run("""
                MATCH (c:Configuration {name: $config_name})
                MERGE (m:Module {full_name: $full_name})
                ON CREATE SET
                    m.name = $name,
                    m.module_type = $module_type,
                    m.line_count = $line_count,
                    m.code_hash = $code_hash,
                    m.description = $description,
                    m.created_at = datetime()
                ON MATCH SET
                    m.updated_at = datetime()
                MERGE (c)-[:HAS_MODULE]->(m)
                RETURN m
            """,
                config_name=config_name,
                full_name=module_data['full_name'],
                name=module_data['name'],
                module_type=module_data.get('module_type', ''),
                line_count=module_data.get('line_count', 0),
                code_hash=module_data.get('code_hash', ''),
                description=module_data.get('description', '')
            )
            
            if not result.single():
                return False
            
            # Link to object if exists
            object_name = module_data.get('object_name')
            object_type = module_data.get('object_type')
            
            if object_name and object_type:
                session.run("""
                    MATCH (m:Module {full_name: $full_name})
                    MATCH (o:Object {
                        configuration: $config_name,
                        type: $object_type,
                        name: $object_name
                    })
                    MERGE (o)-[:HAS_MODULE]->(m)
                """,
                    full_name=module_data['full_name'],
                    config_name=config_name,
                    object_type=object_type,
                    object_name=object_name
                )
            
            return True
    
    def create_function(self, module_full_name: str, func_data: Dict[str, Any]) -> bool:
        """Create Function node and link to Module"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Module {full_name: $module_name})
                MERGE (f:Function {
                    module_name: $module_name,
                    name: $name
                })
                ON CREATE SET
                    f.type = $type,
                    f.is_exported = $is_exported,
                    f.parameters = $parameters,
                    f.return_type = $return_type,
                    f.region = $region,
                    f.description = $description,
                    f.complexity = $complexity,
                    f.created_at = datetime()
                ON MATCH SET
                    f.updated_at = datetime()
                MERGE (m)-[:DEFINES]->(f)
                RETURN f
            """,
                module_name=module_full_name,
                name=func_data['name'],
                type=func_data.get('type', 'Function'),
                is_exported=func_data.get('is_exported', False),
                parameters=func_data.get('parameters', []),
                return_type=func_data.get('return_type', ''),
                region=func_data.get('region', ''),
                description=func_data.get('description', ''),
                complexity=func_data.get('complexity', 1)
            )
            return result.single() is not None
    
    def create_function_call(self, caller_module: str, caller_func: str, 
                           callee_module: str, callee_func: str) -> bool:
        """Create CALLS relationship between functions"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (caller:Function {module_name: $caller_module, name: $caller_func})
                MATCH (callee:Function {module_name: $callee_module, name: $callee_func})
                MERGE (caller)-[r:CALLS]->(callee)
                ON CREATE SET r.created_at = datetime()
                RETURN r
            """,
                caller_module=caller_module,
                caller_func=caller_func,
                callee_module=callee_module,
                callee_func=callee_func
            )
            return result.single() is not None
    
    def get_function_dependencies(self, module_name: str, function_name: str) -> List[Dict]:
        """Get all functions called by this function"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (caller:Function {module_name: $module_name, name: $function_name})
                MATCH (caller)-[:CALLS]->(callee:Function)
                RETURN callee.module_name as module, callee.name as function
            """,
                module_name=module_name,
                function_name=function_name
            )
            return [{"module": record["module"], "function": record["function"]} 
                    for record in result]
    
    def get_function_callers(self, module_name: str, function_name: str) -> List[Dict]:
        """Get all functions that call this function"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (callee:Function {module_name: $module_name, name: $function_name})
                MATCH (caller:Function)-[:CALLS]->(callee)
                RETURN caller.module_name as module, caller.name as function
            """,
                module_name=module_name,
                function_name=function_name
            )
            return [{"module": record["module"], "function": record["function"]} 
                    for record in result]
    
    def search_objects_by_type(self, object_type: str, config_name: Optional[str] = None) -> List[Dict]:
        """Search objects by type"""
        with self.driver.session() as session:
            if config_name:
                result = session.run("""
                    MATCH (c:Configuration {name: $config_name})-[:HAS_OBJECT]->(o:Object {type: $type})
                    RETURN o.name as name, o.description as description
                """,
                    config_name=config_name,
                    type=object_type
                )
            else:
                result = session.run("""
                    MATCH (o:Object {type: $type})
                    RETURN o.configuration as config, o.name as name, o.description as description
                """,
                    type=object_type
                )
            
            return [dict(record) for record in result]
    
    def get_object_modules(self, config_name: str, object_type: str, object_name: str) -> List[Dict]:
        """Get all modules of an object"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (o:Object {
                    configuration: $config_name,
                    type: $object_type,
                    name: $object_name
                })-[:HAS_MODULE]->(m:Module)
                RETURN m.name as name, m.module_type as type, m.line_count as lines
            """,
                config_name=config_name,
                object_type=object_type,
                object_name=object_name
            )
            return [dict(record) for record in result]
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.driver.session() as session:
            result = session.run("""
                RETURN 
                    count{(:Configuration)} as configurations,
                    count{(:Object)} as objects,
                    count{(:Module)} as modules,
                    count{(:Function)} as functions,
                    count{()-[:CALLS]->()} as function_calls
            """)
            record = result.single()
            return {
                'configurations': record['configurations'],
                'objects': record['objects'],
                'modules': record['modules'],
                'functions': record['functions'],
                'function_calls': record['function_calls']
            }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()







