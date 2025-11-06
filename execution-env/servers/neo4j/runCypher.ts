/**
 * Выполнить Cypher запрос в Neo4j
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface RunCypherInput {
  /** Cypher query */
  query: string;
  /** Query parameters */
  parameters?: Record<string, any>;
}

export interface RunCypherResult {
  [key: string]: any;
}


/**
 * Выполнить Cypher запрос в Neo4j
 */
export async function runCypher(
  input: RunCypherInput
): Promise<RunCypherResult> {
  return await callMCPTool<RunCypherResult>(
    'neo4j__run_cypher',
    input
  );
}

