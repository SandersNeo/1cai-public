/**
 * Получить метаданные конфигурации 1С
 * 
 * Auto-generated from MCP tool definition
 */

import { callMCPTool } from '../../client.ts';

export interface GetConfigurationInput {
  /** Имя конфигурации (УТ, Б УХ, ERP и т.д.) */
  name: string;
  /** Включить полные метаданные */
  includeMetadata?: boolean;
}

export interface GetConfigurationResult {
  [key: string]: any;
}


/**
 * Получить метаданные конфигурации 1С
 */
export async function getConfiguration(
  input: GetConfigurationInput
): Promise<GetConfigurationResult> {
  return await callMCPTool<GetConfigurationResult>(
    '1c__get_configuration',
    input
  );
}

