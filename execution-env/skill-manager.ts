/**
 * Skill Manager
 * 
 * Управление переиспользуемыми agent skills
 * Агенты могут сохранять и загружать полезные функции
 */

import { ensureDir } from 'https://deno.land/std@0.208.0/fs/mod.ts';
import { exists } from 'https://deno.land/std@0.208.0/fs/exists.ts';

export interface Skill {
  id: string;
  name: string;
  description: string;
  code: string;
  metadata: SkillMetadata;
}

export interface SkillMetadata {
  author: string;
  created: string;
  updated: string;
  tags: string[];
  usageCount: number;
  successRate: number;
  averageExecutionTimeMs: number;
}

export class SkillManager {
  private skillsDir = './skills';
  
  /**
   * Сохранить новый skill
   */
  async saveSkill(skill: Omit<Skill, 'id' | 'metadata'>): Promise<string> {
    const skillId = this.generateSkillId(skill.name);
    const skillDir = `${this.skillsDir}/${skillId}`;
    
    await ensureDir(skillDir);
    
    // Сохранить код
    await Deno.writeTextFile(
      `${skillDir}/skill.ts`,
      skill.code
    );
    
    // Создать SKILL.md
    const skillMd = this.generateSkillMarkdown(skill);
    await Deno.writeTextFile(
      `${skillDir}/SKILL.md`,
      skillMd
    );
    
    // Создать metadata
    const metadata: SkillMetadata = {
      author: 'ai-agent',
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      tags: this.extractTags(skill.description),
      usageCount: 0,
      successRate: 1.0,
      averageExecutionTimeMs: 0,
    };
    
    await Deno.writeTextFile(
      `${skillDir}/metadata.json`,
      JSON.stringify(metadata, null, 2)
    );
    
    console.log(`✅ Saved skill '${skill.name}' with ID: ${skillId}`);
    
    return skillId;
  }
  
  /**
   * Загрузить skill по ID
   */
  async loadSkill(skillId: string): Promise<Skill | null> {
    const skillDir = `${this.skillsDir}/${skillId}`;
    
    // Check if exists
    if (!await exists(skillDir)) {
      return null;
    }
    
    try {
      // Load all files
      const code = await Deno.readTextFile(`${skillDir}/skill.ts`);
      const skillMd = await Deno.readTextFile(`${skillDir}/SKILL.md`);
      const metadataText = await Deno.readTextFile(`${skillDir}/metadata.json`);
      const metadata: SkillMetadata = JSON.parse(metadataText);
      
      // Parse SKILL.md для name и description
      const { name, description } = this.parseSkillMarkdown(skillMd);
      
      return {
        id: skillId,
        name,
        description,
        code,
        metadata,
      };
    } catch (error) {
      console.error(`Error loading skill ${skillId}:`, error);
      return null;
    }
  }
  
  /**
   * Найти skills по query
   */
  async searchSkills(query: string): Promise<Skill[]> {
    const skills: Skill[] = [];
    
    try {
      // Scan skills directory
      for await (const entry of Deno.readDir(this.skillsDir)) {
        if (entry.isDirectory) {
          const skill = await this.loadSkill(entry.name);
          
          if (skill && this.matchesQuery(skill, query)) {
            skills.push(skill);
          }
        }
      }
    } catch (error) {
      console.error('Error searching skills:', error);
    }
    
    // Sort by usage count и success rate
    skills.sort((a, b) => {
      const scoreA = a.metadata.usageCount * a.metadata.successRate;
      const scoreB = b.metadata.usageCount * b.metadata.successRate;
      return scoreB - scoreA;
    });
    
    return skills;
  }
  
  /**
   * Получить все skills
   */
  async getAllSkills(): Promise<Skill[]> {
    const skills: Skill[] = [];
    
    try {
      for await (const entry of Deno.readDir(this.skillsDir)) {
        if (entry.isDirectory) {
          const skill = await this.loadSkill(entry.name);
          if (skill) {
            skills.push(skill);
          }
        }
      }
    } catch (error) {
      console.error('Error loading all skills:', error);
    }
    
    return skills;
  }
  
  /**
   * Обновить метрики skill после использования
   */
  async updateMetrics(
    skillId: string,
    success: boolean,
    executionTimeMs: number
  ): Promise<void> {
    const skillDir = `${this.skillsDir}/${skillId}`;
    const metadataPath = `${skillDir}/metadata.json`;
    
    try {
      const metadataText = await Deno.readTextFile(metadataPath);
      const metadata: SkillMetadata = JSON.parse(metadataText);
      
      // Update usage count
      metadata.usageCount += 1;
      
      // Update success rate (running average)
      const previousTotal = metadata.usageCount - 1;
      metadata.successRate = (
        (metadata.successRate * previousTotal) + (success ? 1 : 0)
      ) / metadata.usageCount;
      
      // Update average execution time
      metadata.averageExecutionTimeMs = (
        (metadata.averageExecutionTimeMs * previousTotal) + executionTimeMs
      ) / metadata.usageCount;
      
      // Update timestamp
      metadata.updated = new Date().toISOString();
      
      // Save
      await Deno.writeTextFile(
        metadataPath,
        JSON.stringify(metadata, null, 2)
      );
      
      console.log(`✅ Updated metrics for skill ${skillId}`);
    } catch (error) {
      console.error(`Error updating metrics for skill ${skillId}:`, error);
    }
  }
  
  /**
   * Удалить skill
   */
  async deleteSkill(skillId: string): Promise<boolean> {
    const skillDir = `${this.skillsDir}/${skillId}`;
    
    try {
      await Deno.remove(skillDir, { recursive: true });
      console.log(`✅ Deleted skill ${skillId}`);
      return true;
    } catch (error) {
      console.error(`Error deleting skill ${skillId}:`, error);
      return false;
    }
  }
  
  /**
   * Генерировать SKILL.md
   */
  private generateSkillMarkdown(skill: {
    name: string;
    description: string;
  }): string {
    const functionName = this.toCamelCase(skill.name);
    
    return `# ${skill.name}

${skill.description}

## Usage

\`\`\`typescript
import { ${functionName} } from './skill.ts';

// Example usage
const result = await ${functionName}({
  // parameters
});

console.log(result);
\`\`\`

## Parameters

See skill.ts for full parameter documentation.

## Returns

Description of return value.

## Examples

### Example 1

\`\`\`typescript
// Example code here
\`\`\`

## Tags

Auto-generated from description.
`;
  }
  
  /**
   * Parse SKILL.md для извлечения name и description
   */
  private parseSkillMarkdown(markdown: string): {
    name: string;
    description: string;
  } {
    // Extract title (first line with #)
    const titleMatch = markdown.match(/^#\s+(.+)$/m);
    const name = titleMatch ? titleMatch[1].trim() : 'Unknown Skill';
    
    // Extract description (text between title and ## Usage)
    const descMatch = markdown.match(/^#\s+.+\n\n(.+?)(?=\n##)/s);
    const description = descMatch ? descMatch[1].trim() : '';
    
    return { name, description };
  }
  
  /**
   * Генерировать skill ID из имени
   */
  private generateSkillId(name: string): string {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }
  
  /**
   * Извлечь tags из description
   */
  private extractTags(description: string): string[] {
    const keywords = [
      '1c', 'metadata', 'configuration',
      'neo4j', 'graph', 'cypher',
      'qdrant', 'search', 'vector',
      'postgres', 'sql', 'database',
      'elasticsearch', 'logs', 'query',
      'analysis', 'report', 'export',
    ];
    
    const descLower = description.toLowerCase();
    
    return keywords.filter(keyword => descLower.includes(keyword));
  }
  
  /**
   * Проверить, соответствует ли skill query
   */
  private matchesQuery(skill: Skill, query: string): boolean {
    const queryLower = query.toLowerCase();
    
    return (
      skill.name.toLowerCase().includes(queryLower) ||
      skill.description.toLowerCase().includes(queryLower) ||
      skill.metadata.tags.some(tag => tag.includes(queryLower))
    );
  }
  
  /**
   * Convert to camelCase
   */
  private toCamelCase(str: string): string {
    return str
      .replace(/[^a-zA-Z0-9]+(.)/g, (_, char) => char.toUpperCase())
      .replace(/^[A-Z]/, char => char.toLowerCase());
  }
}

// Example usage
if (import.meta.main) {
  const manager = new SkillManager();
  
  // Example: Save a skill
  const skillId = await manager.saveSkill({
    name: 'Extract 1C Dependencies',
    description: 'Анализирует код модуля 1С и извлекает зависимости',
    code: `
export async function extract1CDependencies(moduleId: string) {
  import { getModuleCode } from './servers/1c/getModuleCode.ts';
  
  const code = await getModuleCode({ moduleId });
  
  // Parse imports/dependencies
  const dependencies = [];
  const importPattern = /import\\s+.*?from\\s+['"](.+?)['"]/g;
  
  let match;
  while ((match = importPattern.exec(code)) !== null) {
    dependencies.push(match[1]);
  }
  
  return {
    moduleId,
    dependencies,
    count: dependencies.length
  };
}
`,
  });
  
  console.log(`\n✅ Saved skill with ID: ${skillId}`);
  
  // Load it back
  const loaded = await manager.loadSkill(skillId);
  console.log('\n📖 Loaded skill:');
  console.log(`  Name: ${loaded?.name}`);
  console.log(`  Description: ${loaded?.description}`);
  console.log(`  Tags: ${loaded?.metadata.tags.join(', ')}`);
  
  // Search
  const found = await manager.searchSkills('1c dependencies');
  console.log(`\n🔍 Found ${found.length} skills matching '1c dependencies'`);
}


