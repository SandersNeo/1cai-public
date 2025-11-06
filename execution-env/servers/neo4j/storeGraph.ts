/**
 * Сохранить граф в Neo4j
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface StoreGraphInput {
  /** Graph nodes */
  nodes: any[];
  /** Graph relationships */
  relationships: any[];
}

export interface StoreGraphResult {
  [key: string]: any;
}


/**
 * Сохранить граф в Neo4j
 */
export async function storeGraph(
  input: StoreGraphInput
): Promise<StoreGraphResult> {
  return await callMCPTool<StoreGraphResult>(
    'neo4j__store_graph',
    input
  );
}

