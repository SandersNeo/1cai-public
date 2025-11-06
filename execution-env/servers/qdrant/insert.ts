/**
 * Вставить vectors в Qdrant
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface InsertInput {
  /** Collection name */
  collection: string;
  /** Points to insert */
  points: any[];
}

export interface InsertResult {
  [key: string]: any;
}


/**
 * Вставить vectors в Qdrant
 */
export async function insert(
  input: InsertInput
): Promise<InsertResult> {
  return await callMCPTool<InsertResult>(
    'qdrant__insert',
    input
  );
}

