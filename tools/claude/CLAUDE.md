# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude CLI integration module for BoarderframeOS that provides multiple access points to Anthropic's Claude Code CLI. It serves as a wrapper and launcher system within the BoarderframeOS AI operating system.

## Development Commands

- **Install dependencies**: `npm install`
- **Start main service**: `npm start`
- **Make scripts executable**: `chmod +x claudectl start-claude claude-launcher`
- **Interactive Claude session**: `./start-claude`
- **Command execution**: `./claudectl [command]`

## Architecture

**Core Components:**
- `index.js`: Main Node.js module exposing `runClaudeCommand()` function using `child_process.execSync`
- `package.json`: Minimal configuration with single dependency on `@anthropic-ai/claude-code`

**Executable Scripts:**
- `start-claude`: Interactive terminal launcher with model selection
- `claudectl`: Node.js CLI wrapper for programmatic execution
- `claude-launcher`: Terminal launcher that navigates to project root
- `claude-terminal`: Direct wrapper preserving terminal interface

## Setup Requirements

- Scripts require `chmod +x` permissions to be executable
- Claude settings configured in `.claude/settings.local.json` with `Bash(find:*)` permissions
- Designed to operate from `tools/claude/` directory within BoarderframeOS

## Usage Patterns

1. **Interactive mode**: Use `./start-claude` for terminal sessions
2. **Programmatic**: Use `claudectl [command]` for script integration
3. **Global access**: Available via `tools/ctl/claude` from anywhere in BoarderframeOS
4. **Direct CLI**: `npx @anthropic-ai/claude-code [command]`

The system is lightweight and focused on providing convenient access to Claude CLI while maintaining terminal interface quality.