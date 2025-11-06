/**
 * Получить метаданные объекта 1С
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface GetMetadataInput {
  /** Тип объекта (Catalog, Document, Report и т.д.) */
  objectType: string;
  /** Имя объекта */
  objectName: string;
}

export interface GetMetadataResult {
  [key: string]: any;
}


/**
 * Получить метаданные объекта 1С
 */
export async function getMetadata(
  input: GetMetadataInput
): Promise<GetMetadataResult> {
  return await callMCPTool<GetMetadataResult>(
    '1c__get_metadata',
    input
  );
}

