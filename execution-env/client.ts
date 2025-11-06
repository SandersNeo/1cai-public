/**
 * MCP Client для Execution Environment
 * 
 * Связь между TypeScript execution environment и Python MCP Server
 */

// Simple HTTP-based MCP client (без использования SDK для простоты)
interface MCPToolCallRequest {
  toolName: string;
  arguments: any;
}

interface MCPToolCallResponse {
  success: boolean;
  result?: any;
  error?: string;
}

class SimpleMCPClient {
  private serverUrl: string;
  
  constructor(serverUrl: string = 'http://localhost:8000/mcp') {
    this.serverUrl = serverUrl;
  }
  
  async callTool<T>(toolName: string, args: any): Promise<T> {
    const request: MCPToolCallRequest = {
      toolName,
      arguments: args,
    };
    
    try {
      const response = await fetch(`${this.serverUrl}/call-tool`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data: MCPToolCallResponse = await response.json();
      
      if (!data.success) {
        throw new Error(`MCP tool error: ${data.error}`);
      }
      
      return data.result as T;
      
    } catch (error) {
      console.error(`Error calling MCP tool '${toolName}':`, error);
      throw error;
    }
  }
}

// Singleton instance
let mcpClient: SimpleMCPClient | null = null;

/**
 * Вызвать MCP tool
 * 
 * Usage:
 *   const result = await callMCPTool<MyResultType>('server__tool_name', { arg1: 'value' });
 */
export async function callMCPTool<T>(
  toolName: string,
  args: any
): Promise<T> {
  if (!mcpClient) {
    // Получить URL из environment variable или use default
    const serverUrl = Deno.env.get('MCP_SERVER_URL') || 'http://localhost:8000/mcp';
    mcpClient = new SimpleMCPClient(serverUrl);
  }
  
  return await mcpClient.callTool<T>(toolName, args);
}

/**
 * Search tools (semantic search)
 */
export interface SearchToolsInput {
  query: string;
  server?: string;
  detailLevel?: 'name_only' | 'name_and_description' | 'full';
  limit?: number;
}

export interface SearchToolsResult {
  name: string;
  server: string;
  description?: string;
  score: number;
  fullDefinition?: any;
}

export async function searchTools(
  input: SearchToolsInput
): Promise<SearchToolsResult[]> {
  return await callMCPTool<SearchToolsResult[]>('search_tools', input);
}


