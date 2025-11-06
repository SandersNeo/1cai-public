/**
 * Code Execution Harness
 * 
 * Безопасное выполнение AI-generated TypeScript кода в sandboxed Deno runtime
 */

import { getSecurityConfig, SecurityConfig } from './execution-config.ts';

export interface ExecutionResult {
  success: boolean;
  output: string;
  errors: string;
  executionTimeMs: number;
  memoryUsedMB: number;
  exitCode: number;
}

export interface ExecutionOptions {
  timeout?: number;
  sessionId?: string;
  saveOutput?: boolean;
}

export class CodeExecutionHarness {
  private config: SecurityConfig;
  private workspaceDir = './workspace';
  private tempDir = './temp';
  
  constructor(config?: SecurityConfig) {
    this.config = config || getSecurityConfig();
  }
  
  /**
   * Выполнить TypeScript код в sandboxed environment
   */
  async execute(
    code: string,
    options: ExecutionOptions = {}
  ): Promise<ExecutionResult> {
    const startTime = Date.now();
    const sessionId = options.sessionId || this.generateSessionId();
    
    // Создать временный файл с кодом
    const tempFile = await this.createTempFile(code, sessionId);
    
    try {
      // Подготовить команду с security restrictions
      const cmd = this.buildSecureCommand(tempFile);
      
      // Выполнить с timeout
      const timeout = options.timeout || this.config.limits.maxExecutionTimeMs;
      const result = await this.executeWithTimeout(cmd, timeout);
      
      // Собрать метрики
      const executionTimeMs = Date.now() - startTime;
      const memoryUsedMB = result.memoryUsedMB;
      
      // Сохранить output в workspace (опционально)
      if (options.saveOutput && result.success) {
        await this.saveOutput(sessionId, result.output);
      }
      
      return {
        success: result.success,
        output: result.output,
        errors: result.errors,
        executionTimeMs,
        memoryUsedMB,
        exitCode: result.exitCode,
      };
      
    } catch (error) {
      return {
        success: false,
        output: '',
        errors: `Execution error: ${error.message}`,
        executionTimeMs: Date.now() - startTime,
        memoryUsedMB: 0,
        exitCode: 1,
      };
    } finally {
      // Cleanup temp file
      await this.cleanup(tempFile);
    }
  }
  
  /**
   * Построить команду с security restrictions
   */
  private buildSecureCommand(scriptPath: string): string[] {
    const perms = this.config.allowedPermissions;
    
    const cmd = ['deno', 'run'];
    
    // Network permissions
    if (perms.net.length > 0) {
      cmd.push(`--allow-net=${perms.net.join(',')}`);
    }
    
    // Read permissions
    if (perms.read.length > 0) {
      cmd.push(`--allow-read=${perms.read.join(',')}`);
    }
    
    // Write permissions
    if (perms.write.length > 0) {
      cmd.push(`--allow-write=${perms.write.join(',')}`);
    }
    
    // Environment variables
    if (perms.env.length > 0) {
      cmd.push(`--allow-env=${perms.env.join(',')}`);
    }
    
    // NO subprocess (--allow-run не добавляем!)
    
    // No prompts
    cmd.push('--no-prompt');
    
    // Script path
    cmd.push(scriptPath);
    
    return cmd;
  }
  
  /**
   * Выполнить с timeout
   */
  private async executeWithTimeout(
    cmd: string[],
    timeoutMs: number
  ): Promise<{
    success: boolean;
    output: string;
    errors: string;
    exitCode: number;
    memoryUsedMB: number;
  }> {
    const process = new Deno.Command(cmd[0], {
      args: cmd.slice(1),
      stdout: 'piped',
      stderr: 'piped',
    });
    
    const child = process.spawn();
    
    // Timeout timer
    const timeoutPromise = new Promise<void>((_, reject) => {
      setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`Execution timeout after ${timeoutMs}ms`));
      }, timeoutMs);
    });
    
    // Execution promise
    const executionPromise = (async () => {
      const status = await child.status;
      const output = new TextDecoder().decode(
        await new Response(child.stdout).arrayBuffer()
      );
      const errors = new TextDecoder().decode(
        await new Response(child.stderr).arrayBuffer()
      );
      
      return {
        success: status.success,
        output,
        errors,
        exitCode: status.code,
      };
    })();
    
    try {
      const result = await Promise.race([executionPromise, timeoutPromise]);
      
      // Получить memory usage (Linux only, для Windows вернём 0)
      const memoryUsedMB = await this.getMemoryUsage(child.pid);
      
      return {
        ...result as any,
        memoryUsedMB,
      };
    } catch (error) {
      throw error;
    }
  }
  
  /**
   * Создать временный файл с кодом
   */
  private async createTempFile(code: string, sessionId: string): Promise<string> {
    // Ensure temp directory exists
    try {
      await Deno.mkdir(this.tempDir, { recursive: true });
    } catch {
      // Directory exists
    }
    
    const tempFile = `${this.tempDir}/script-${sessionId}.ts`;
    await Deno.writeTextFile(tempFile, code);
    
    return tempFile;
  }
  
  /**
   * Получить memory usage (Linux only)
   */
  private async getMemoryUsage(pid: number): Promise<number> {
    try {
      // Linux: read /proc/{pid}/status
      const statusFile = `/proc/${pid}/status`;
      const status = await Deno.readTextFile(statusFile);
      const match = status.match(/VmRSS:\s+(\d+)\s+kB/);
      
      if (match) {
        return parseInt(match[1]) / 1024; // Convert KB to MB
      }
    } catch {
      // Windows или другая OS - вернуть 0
      return 0;
    }
    
    return 0;
  }
  
  /**
   * Сохранить output в workspace
   */
  private async saveOutput(sessionId: string, output: string): Promise<void> {
    const outputDir = `${this.workspaceDir}/${sessionId}`;
    
    try {
      await Deno.mkdir(outputDir, { recursive: true });
    } catch {
      // Directory exists
    }
    
    const outputFile = `${outputDir}/output.txt`;
    await Deno.writeTextFile(outputFile, output);
  }
  
  /**
   * Cleanup temporary files
   */
  private async cleanup(tempFile: string): Promise<void> {
    try {
      await Deno.remove(tempFile);
    } catch {
      // File already deleted or doesn't exist
    }
  }
  
  /**
   * Генерировать session ID
   */
  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  }
}

// HTTP Server для remote execution
export async function startExecutionServer(port: number = 8001) {
  const harness = new CodeExecutionHarness();
  
  const handler = async (req: Request): Promise<Response> => {
    // CORS headers
    const headers = {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers });
    }
    
    // Only POST allowed
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        { status: 405, headers }
      );
    }
    
    // Parse request
    try {
      const body = await req.json();
      const { code, timeout, sessionId, saveOutput } = body;
      
      if (!code) {
        return new Response(
          JSON.stringify({ error: 'Missing code parameter' }),
          { status: 400, headers }
        );
      }
      
      // Execute
      const result = await harness.execute(code, {
        timeout,
        sessionId,
        saveOutput,
      });
      
      return new Response(JSON.stringify(result), { headers });
      
    } catch (error) {
      return new Response(
        JSON.stringify({ error: error.message }),
        { status: 500, headers }
      );
    }
  };
  
  console.log(`🚀 Code Execution Server listening on http://localhost:${port}`);
  await Deno.serve({ port }, handler);
}

// CLI entry point
if (import.meta.main) {
  const port = parseInt(Deno.env.get('PORT') || '8001');
  await startExecutionServer(port);
}


