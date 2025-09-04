# MCP Server Manager Project - Claude Instructions

## Project Overview
This is a centralized system to manage multiple MCP servers for an AI agent company, integrated with Open WebUI for chip-based tool access in chat UI. The project prioritizes usability, security, efficient tool management, and LLM-focused design.

## Technology Stack Preferences
- **Backend**: Python with FastAPI (NOT Node.js)
- **Database**: PostgreSQL (NOT Redis for primary data)
- **Frontend**: React or Svelte with Vite for hot reload
- **API**: Python FastAPI with async support
- **Testing**: Python pytest framework
- **Container**: Python 3.11+ based Docker images


### Background Processing Rules:
- **Always run development servers in background** using `run_in_background: true`
- **Use BashOutput tool** to monitor background processes
- **Run parallel bash commands** in single messages for efficiency
- **Kill background processes** with KillBash when done

## Project Structure & Tools

### Core Technologies:
- **Docker**: Containerization with Node.js 18 base image
- **Git**: Version control with Conventional Commits
- **Vite**: Real-time development with hot reload
- **Open WebUI**: Chat interface integration
- **MCP Inspector**: Testing and validation
- **LM Studio**: Local inference with gpt-oss model

### Directory Structure:
```
mcp-server-manager/
├── src/                 # Main application code
├── config/              # MCP server configurations
├── docker/              # Docker files and compose
├── docs/                # Documentation (human & LLM)
├── tests/               # MCP Inspector tests
├── frontend/            # Vite-based management UI
└── CLAUDE.md           # This file
```

### Key Files:
- `config/mcp.json`: Dynamic MCP server configuration with security restrictions
- `docker/Dockerfile`: Lightweight Node.js container
- `docker/docker-compose.yml`: Multi-service orchestration
- `src/index.js`: Main API server with LLM-focused endpoints
- `frontend/`: Vite-based real-time management interface

## Development Workflow

### Git Branching Strategy:
- `main`: Production-ready code
- `mcp-initial`: Initial setup branch
- `mcp-<server-name>`: Feature branches for each MCP server
- Use Conventional Commits: `<type>(<scope>): <summary>` (max 50 chars)

### Commit Automation Rules:
1. **Always run tests** with MCP Inspector before commits
2. **Use code-reviewer agent** for all significant code changes
3. **Test Docker builds** before pushing
4. **Validate Open WebUI integration** after changes
5. **Check security restrictions** in config/mcp.json

### Required Commands for Testing:
```bash
# Test MCP servers
npx @modelcontextprotocol/inspector

# Build and test Docker
docker-compose up --build

# Run Vite dev server in background
npm run dev
```

## Security & Configuration Requirements

### MCP Configuration (`config/mcp.json`):
```json
{
  "servers": {},
  "security": {
    "blocked_paths": ["/etc", "/var", "/.env"],
    "blocked_commands": ["rm", "sudo", "chmod"],
    "max_token_budget": 10000,
    "rate_limits": {
      "requests_per_minute": 60,
      "max_concurrent": 5
    }
  },
  "logging": {
    "level": "info",
    "audit_trail": true
  }
}
```

### Docker Security:
- **No privileged mode**
- **Restricted mounts** (only /config volume)
- **Non-root user** execution
- **Minimal attack surface** with alpine or slim images

## LLM-Focused Design Principles

### Error Handling:
- **Clear error messages** that help agent decision-making
- **Configuration issues** over permission denials
- **Context-aware responses** to prevent token waste
- **Structured responses** for easy parsing

### Token Management:
- **Efficient API responses** to avoid context window degradation
- **Summarized logs** instead of full dumps
- **Pagination** for large datasets
- **Caching** for repeated requests

### Agent-Friendly Features:
- **Tool descriptions** with clear suitability guidelines
- **Endpoint documentation** optimized for LLM consumption
- **Failure mode documentation** with recovery strategies
- **Usage examples** for common scenarios

## Open WebUI Integration

### Setup Requirements:
1. **Add container API URL** (http://localhost:8080) to MCP Connector settings
2. **Configure chip-based access** for seamless tool calling
3. **Use MCPO proxy** for tool routing
4. **Test latency and security** with simulated LLM calls

### Real-time Development:
- **Vite dev server** for instant UI updates
- **Hot reload** for configuration changes
- **Live testing** with Open WebUI integration
- **Background monitoring** of MCP server health

## Automation Instructions for Claude

### When Adding New MCP Servers:
1. **Create feature branch**: `git checkout -b mcp-<server-name>`
2. **Use security-auditor agent** to review configurations
3. **Test with MCP Inspector** before committing
4. **Use backend-architect agent** for API design
5. **Commit with conventional format**: `feat(mcp): add <server> with restrictions`

### When Modifying Code:
1. **Use code-reviewer agent** after significant changes
2. **Run parallel testing** with multiple agents
3. **Validate Docker builds** in background
4. **Check Open WebUI integration** automatically

### When Troubleshooting:
1. **Use devops-troubleshooter agent** for deployment issues
2. **Use error-detective agent** for log analysis
3. **Use performance-engineer agent** for optimization
4. **Document solutions** for future reference

## Remember: ALWAYS USE AGENTS IN PARALLEL - This is not optional!



## Parallel Agent Configuration

# Claude Code Parallel Agent Execution Guide

## 🚀 Core Parallel Agent Capabilities

### Task Tool (Subagents)
Claude Code can spawn lightweight subagents using the Task tool. Each subagent:
- Has its own context window (independent memory)
- Can access the same tools as the main agent (except spawning more tasks)
- Runs concurrently with other subagents
- Reports results back to the main agent

### How to Invoke Parallel Agents:
**Use multiple Task tool calls in a SINGLE message for parallel execution:**

**CRITICAL: All three parameters are REQUIRED for each Task call:**

```xml
<function_calls>
<invoke name="Task">
<parameter name="subagent_type">python-pro</parameter>
<parameter name="description">Create FastAPI backend</parameter>
<parameter name="prompt">Implement Python FastAPI backend with PostgreSQL integration and async endpoints</parameter>
</invoke>
<invoke name="Task">
<parameter name="subagent_type">frontend-developer</parameter>
<parameter name="description">Setup React frontend</parameter>
<parameter name="prompt">Create React/Svelte frontend with Vite hot reload for MCP server management UI</parameter>
</invoke>
<invoke name="Task">
<parameter name="subagent_type">security-auditor</parameter>
<parameter name="description">Review security config</parameter>
<parameter name="prompt">Audit the security configuration for vulnerabilities and compliance with best practices</parameter>
</invoke>
</function_calls>
```

**Required Parameters for Task Tool:**
- `subagent_type`: The specialized agent type (e.g., python-pro, frontend-developer, security-auditor)
- `description`: Short 3-5 word description of the task 
- `prompt`: Detailed instructions for what the agent should accomplish

## 📋 Parallel Execution Patterns

### 1. Basic Parallel Task Invocation
```
Execute these tasks using 4 parallel agents:
- Agent 1: Analyze authentication logic
- Agent 2: Review database schemas  
- Agent 3: Document API endpoints
- Agent 4: Check test coverage
```

### 2. The 7-Parallel-Task Method (Recommended for Features)
When implementing new features, immediately launch 7 parallel tasks:
```
IMMEDIATE EXECUTION: Launch parallel Tasks for [feature name]:
1. **Component**: Create main component file
2. **Styles**: Create component styles/CSS
3. **Types**: Define TypeScript interfaces/types
4. **Tests**: Write unit tests
5. **Integration**: Handle API/service connections
6. **Documentation**: Update docs/README
7. **Review**: Coordinate integration and validation
```

### 3. Large Codebase Exploration Pattern
```
Explore the codebase using 4 parallel tasks. Each agent should:
- Focus on different directories
- Have specific exploration goals
- Document findings in a RESULTS.md file
- Not overlap with other agents' areas
```

## 🎯 When to Use Parallel Agents

### ✅ ALWAYS use parallel agents for:
- **Feature implementation** (break into component tasks)
- **Large refactoring** (divide by modules/directories)
- **Codebase exploration** (split by area of focus)
- **Multi-file migrations** (batch files to agents)
- **Test generation** (separate test types)
- **Documentation updates** (split by doc type)

### ❌ AVOID parallel agents for:
- Simple single-file changes
- Sequential dependencies
- Database migrations (risk of conflicts)
- Critical path operations
- Small bug fixes

## 💻 Git Worktree Integration

### Setup Multiple Workspaces
```bash
# Create parallel worktrees for feature development
git worktree add ../trees/feature-1 -b feature-1
git worktree add ../trees/feature-2 -b feature-2
git worktree add ../trees/feature-3 -b feature-3

# Launch Claude in each worktree
cd ../trees/feature-1 && claude
cd ../trees/feature-2 && claude
cd ../trees/feature-3 && claude
```

### Project Structure for Parallel Development
```
project/
├── .claude/
│   └── CLAUDE.md          # This file
├── main/                  # Main branch
└── trees/                 # Parallel workspaces
    ├── feature-1/
    ├── feature-2/
    └── feature-3/
```

## 📝 Explicit Parallel Instructions Template

```markdown
## Parallel Implementation Request

**Task**: [Describe the feature/task]
**Parallel Agents**: 5

**Agent Distribution**:
1. **Frontend Agent**: Handle all UI components in src/components/*
2. **Backend Agent**: Implement API endpoints in src/api/*  
3. **Database Agent**: Create schemas and migrations in src/db/*
4. **Test Agent**: Write all tests in tests/*
5. **Integration Agent**: Connect components and verify integration

**Critical Rules**:
- Each agent MUST update status.json with progress
- Agents MUST NOT modify files outside their scope
- All agents should complete within reasonable time
- Use RESULTS.md to document completion

**Execution**: Start all agents immediately in parallel
```

## 🔧 Advanced Patterns

### Supervisor-Worker Pattern
```
Act as a supervisor and spawn 4 worker tasks:
- Define the overall plan first
- Delegate specific portions to each worker
- Workers report back with results
- Supervisor integrates and validates all work
```

### Exploration with Different Personas
```
Spawn 4 sub-tasks with different expert perspectives:
1. Security expert: Review for vulnerabilities
2. Performance expert: Identify bottlenecks
3. UX expert: Evaluate user experience
4. Architecture expert: Assess design patterns
```

### Parallel Review and Implementation
```
Use 2 parallel agents:
- Agent A: Write the implementation
- Agent B: Write tests for the implementation
Then spawn Agent C to review both outputs
```

## ⚡ Performance Optimization

### Context Window Management
- Each subagent gets fresh context (doesn't inherit conversation)
- Use this to avoid context pollution
- Ideal for large codebases that exceed single context

### Delegation Guidelines
```
DELEGATE to subagents:
- File reads and searches
- Independent analysis tasks  
- Parallel file modifications
- Research and exploration

KEEP in main agent:
- Critical decision making
- Coordination logic
- Final integration
- User interaction
```

## 🎮 Preference Settings

### When Claude Should Default to Parallel
- Any request mentioning "multiple files" or "entire codebase"
- Feature implementations (auto-split into components)
- Requests with "analyze", "explore", or "review" keywords
- Migrations or refactoring tasks
- When time efficiency is mentioned

### Sequential Override Keywords
- "one at a time"
- "step by step"  
- "carefully"
- "dependent on"
- "after completing"

## 📊 Status Tracking Pattern

Create a `status.json` for parallel agents:
```json
{
  "agents": {
    "agent_1": {"status": "in_progress", "files": ["src/auth.js"]},
    "agent_2": {"status": "completed", "files": ["src/db.js"]},
    "agent_3": {"status": "pending", "files": ["src/api.js"]}
  }
}
```

## 🚨 Safety Rules

1. **File Ownership**: Each agent owns specific files/directories
2. **No Overlaps**: Agents must not modify same files
3. **Atomic Commits**: Each agent commits independently
4. **Failure Isolation**: One agent failure doesn't affect others
5. **Clear Boundaries**: Explicitly define agent scopes

## 💡 Quick Reference

### Trigger Phrases for Parallel Execution
- "use parallel agents"
- "split this across multiple tasks"
- "fan out"
- "distribute the work"
- "work on this simultaneously"
- "multiple agents in parallel"

### Magic Numbers
- **4 agents**: Default for exploration tasks
- **7 agents**: Optimal for feature implementation
- **10+ agents**: Maximum practical limit for complex projects

Remember: Parallel agents multiply your productivity but require clear boundaries and coordination. When in doubt, be explicit about parallel execution preferences!