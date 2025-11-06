/**
 * Выполнить SQL запрос в базе 1С
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface ExecuteQueryInput {
  /** SQL запрос */
  query: string;
  /** Лимит результатов */
  limit?: number;
}

export interface ExecuteQueryResult {
  [key: string]: any;
}


/**
 * Выполнить SQL запрос в базе 1С
 */
export async function executeQuery(
  input: ExecuteQueryInput
): Promise<ExecuteQueryResult> {
  return await callMCPTool<ExecuteQueryResult>(
    '1c__execute_query',
    input
  );
}

