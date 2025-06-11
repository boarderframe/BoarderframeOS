# Claude CLI for BoarderframeOS

This directory contains the integration of Anthropic's Claude Code CLI with BoarderframeOS.

## Setup

1. Navigate to this directory:

   ```bash
   cd /path/to/BoarderframeOS/tools/claude
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Make the scripts executable:

   ```bash
   chmod +x claudectl start-claude claude-launcher
   ```

## Usage

You can use the Claude CLI in several ways:

### 1. Interactive Terminal Interface

```bash
./start-claude
```

This launches Claude in interactive mode with a nice terminal interface.

### 2. From anywhere in the BoarderframeOS project

```bash
tools/ctl/claude
```

### 3. Directly via npx

```bash
npx @anthropic-ai/claude-code [command]
```

### 4. Using the API wrapper script

```bash
./claudectl [command]
```

## Common Commands

- Generate code:

  ```bash
  ./start-claude code "create a function that calculates the Fibonacci sequence"
  ```

- Get help:

  ```bash
  ./start-claude --help
  ```

## Integration with BoarderframeOS

This module can be used by BoarderframeOS agents to leverage Claude's code generation capabilities directly from the terminal.

For more information on Claude Code CLI, visit the [official documentation](https://docs.anthropic.com/claude/docs/claude-code-cli).

## Common Commands

- Generate code: `claudectl code "create a function that calculates the Fibonacci sequence"`
- Get help: `claudectl --help`

## Integration with BoarderframeOS

This module can be used by BoarderframeOS agents to leverage Claude's code generation capabilities directly from the terminal.

For more information on Claude Code CLI, visit the [official documentation](https://docs.anthropic.com/claude/docs/claude-code-cli).
