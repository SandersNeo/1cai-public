/**
 * Семантический поиск в Qdrant
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface SearchInput {
  /** Collection name */
  collection: string;
  /** Search query */
  query: string;
  /** Result limit */
  limit?: number;
}

export interface SearchResult {
  [key: string]: any;
}


/**
 * Семантический поиск в Qdrant
 */
export async function search(
  input: SearchInput
): Promise<SearchResult> {
  return await callMCPTool<SearchResult>(
    'qdrant__search',
    input
  );
}

