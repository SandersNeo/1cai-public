/**
 * Конфигурация безопасности для Code Execution Environment
 * 
 * Определяет:
 * - Разрешённые permissions (whitelist)
 * - Resource limits
 * - Monitoring settings
 */

export interface SecurityConfig {
  allowedPermissions: {
    net: string[];
    read: string[];
    write: string[];
    env: string[];
    run: boolean;
  };
  limits: {
    maxMemoryMB: number;
    maxCPUPercent: number;
    maxExecutionTimeMs: number;
    maxFileSizeMB: number;
    maxWorkspaceFiles: number;
  };
  monitoring: {
    logAll: boolean;
    alertOnFailure: boolean;
    metricsEndpoint: string;
  };
}

export const SECURITY_CONFIG: SecurityConfig = {
  // Разрешённые permissions (whitelist only)
  allowedPermissions: {
    // Network: только MCP server
    net: [
      'localhost:6001',  // MCP Server
      'localhost:8000',  // Python Backend
      '127.0.0.1:6001',
      '127.0.0.1:8000',
    ],
    
    // Read: только workspace, servers, skills
    read: [
      './workspace',
      './servers', 
      './skills',
      './temp',
    ],
    
    // Write: только workspace и temp
    write: [
      './workspace',
      './temp',
    ],
    
    // Environment variables (whitelist)
    env: [
      'ONEC_API_URL',
      'NEO4J_URL',
      'QDRANT_URL',
      'POSTGRES_URL',
      'ELASTICSEARCH_URL',
      'MCP_SERVER_URL',
    ],
    
    // NO subprocess execution
    run: false,
  },
  
  // Resource limits
  limits: {
    maxMemoryMB: 512,           // 512MB RAM limit
    maxCPUPercent: 50,          // 50% CPU max
    maxExecutionTimeMs: 30000,  // 30 seconds timeout
    maxFileSizeMB: 10,          // 10MB per file
    maxWorkspaceFiles: 100,     // Max 100 files in workspace
  },
  
  // Monitoring
  monitoring: {
    logAll: true,
    alertOnFailure: true,
    metricsEndpoint: 'http://localhost:9090/metrics',
  },
};

// Development mode (более мягкие ограничения)
export const DEV_SECURITY_CONFIG: SecurityConfig = {
  ...SECURITY_CONFIG,
  limits: {
    ...SECURITY_CONFIG.limits,
    maxMemoryMB: 1024,
    maxExecutionTimeMs: 60000,  // 1 минута для dev
  },
};

// Production mode (строже)
export const PROD_SECURITY_CONFIG: SecurityConfig = {
  ...SECURITY_CONFIG,
  limits: {
    ...SECURITY_CONFIG.limits,
    maxMemoryMB: 256,
    maxExecutionTimeMs: 15000,  // 15 секунд
  },
};

// Выбор конфигурации по NODE_ENV
export function getSecurityConfig(): SecurityConfig {
  const env = Deno.env.get('NODE_ENV') || 'development';
  
  switch (env) {
    case 'production':
      return PROD_SECURITY_CONFIG;
    case 'development':
      return DEV_SECURITY_CONFIG;
    default:
      return SECURITY_CONFIG;
  }
}


