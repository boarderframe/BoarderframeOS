/**
 * BoarderframeOS Claude CLI integration
 * 
 * This module provides integration with Anthropic's Claude Code CLI.
 */

const { execSync } = require('child_process');

function runClaudeCommand(command, options = {}) {
  try {
    const result = execSync(`npx @anthropic-ai/claude-code ${command}`, {
      encoding: 'utf8',
      ...options
    });
    return { success: true, output: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

module.exports = {
  runClaudeCommand
};
