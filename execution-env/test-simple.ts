/**
 * Простой тест Code Execution Environment
 * 
 * Запуск:
 *   deno run --allow-all test-simple.ts
 */

import { CodeExecutionHarness } from './execution-harness.ts';

async function testSimpleExecution() {
  console.log('🧪 Test 1: Simple console.log');
  
  const harness = new CodeExecutionHarness();
  
  const code1 = `
console.log("Hello from AI Agent!");
const x = 1 + 1;
console.log(\`1 + 1 = \${x}\`);
  `;
  
  const result1 = await harness.execute(code1);
  
  console.log('✅ Result:', result1);
  console.log('  Success:', result1.success);
  console.log('  Output:', result1.output);
  console.log('  Time:', result1.executionTimeMs, 'ms');
  console.log('');
}

async function testMCPToolCall() {
  console.log('🧪 Test 2: MCP Tool Call Simulation');
  
  const harness = new CodeExecutionHarness();
  
  const code2 = `
// Simulate MCP tool call
async function callTool(name: string, args: any) {
  console.log(\`Calling tool: \${name}\`);
  console.log(\`Arguments:\`, JSON.stringify(args, null, 2));
  
  // Simulate result
  return {
    success: true,
    data: { result: "Mock data from " + name }
  };
}

const result = await callTool('1c__get_configuration', { name: 'УТ' });
console.log('Tool result:', JSON.stringify(result, null, 2));
  `;
  
  const result2 = await harness.execute(code2);
  
  console.log('✅ Result:', result2);
  console.log('  Success:', result2.success);
  console.log('  Output:', result2.output);
  console.log('');
}

async function testWorkspace() {
  console.log('🧪 Test 3: Workspace Write');
  
  const harness = new CodeExecutionHarness();
  
  const code3 = `
// Write to workspace
const data = {
  timestamp: new Date().toISOString(),
  message: "Hello from agent",
  calculations: [1, 2, 3].map(x => x * 2)
};

await Deno.writeTextFile(
  './workspace/test-output.json',
  JSON.stringify(data, null, 2)
);

console.log('✅ Written to workspace/test-output.json');
console.log(JSON.stringify(data, null, 2));
  `;
  
  const result3 = await harness.execute(code3);
  
  console.log('✅ Result:', result3);
  console.log('  Success:', result3.success);
  console.log('  Output:', result3.output);
  
  // Verify file created
  try {
    const content = await Deno.readTextFile('./workspace/test-output.json');
    console.log('  📁 File created successfully!');
    console.log('  Content:', content);
  } catch {
    console.log('  ❌ File not created');
  }
  
  console.log('');
}

async function testSecurityRestriction() {
  console.log('🧪 Test 4: Security Restriction (should fail)');
  
  const harness = new CodeExecutionHarness();
  
  const maliciousCode = `
// Try to read outside allowed directory
await Deno.readTextFile('/etc/passwd');
  `;
  
  const result4 = await harness.execute(maliciousCode);
  
  console.log('✅ Security test result:');
  console.log('  Success:', result4.success);
  console.log('  Should be false!');
  console.log('  Errors:', result4.errors);
  console.log('');
}

// Run all tests
async function runAllTests() {
  console.log('🚀 Running Code Execution Environment Tests\n');
  console.log('='.repeat(60));
  console.log('');
  
  await testSimpleExecution();
  await testMCPToolCall();
  await testWorkspace();
  await testSecurityRestriction();
  
  console.log('='.repeat(60));
  console.log('\n✅ All tests completed!');
}

if (import.meta.main) {
  await runAllTests();
}


