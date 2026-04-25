---
name: langsmith-fetch
description: Debug LangChain and LangGraph agents by fetching execution traces from LangSmith Studio. Use when debugging agent behavior, investigating errors, analyzing tool calls, checking memory operations, or examining agent performance. Automatically fetches recent traces and analyzes execution patterns. Requires langsmith-fetch CLI installed.
---

# LangSmith Fetch - Agent Debugging Skill

Debug LangChain and LangGraph agents by fetching execution traces directly from LangSmith Studio in your terminal.

## When to Use This Skill

Automatically activate when user mentions:
- "Debug my agent" or "What went wrong?"
- "Show me recent traces" or "What happened?"
- "Check for errors" or "Why did it fail?"
- "Analyze memory operations" or "Check LTM"
- "Review agent performance" or "Check token usage"
- "What tools were called?" or "Show execution flow"

## Prerequisites

### 1. Install langsmith-fetch
```bash
pip install langsmith-fetch
```

### 2. Set Environment Variables
```bash
export LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_PROJECT="your_project_name"
```

## Core Workflows

### Workflow 1: Quick Debug Recent Activity

**When user asks:** "What just happened?" or "Debug my agent"

**Execute:**
```bash
langsmith-fetch traces --last-n-minutes 5 --limit 5 --format pretty
```

**Analyze and report:**
1. Number of traces found
2. Any errors or failures
3. Tools that were called
4. Execution times
5. Token usage

### Workflow 2: Deep Dive Specific Trace

**When user provides:** Trace ID or says "investigate that error"

**Execute:**
```bash
langsmith-fetch trace <trace-id> --format json
```

**Analyze and report:**
1. What the agent was trying to do
2. Which tools were called (in order)
3. Tool results (success/failure)
4. Error messages (if any)
5. Root cause analysis
6. Suggested fix

### Workflow 3: Export Debug Session

**When user says:** "Save this session" or "Export traces"

**Execute:**
```bash
# Create session folder with timestamp
SESSION_DIR="langsmith-debug/session-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SESSION_DIR"

# Export traces
langsmith-fetch traces "$SESSION_DIR/traces" --last-n-minutes 30 --limit 50 --include-metadata

# Export threads (conversations)
langsmith-fetch threads "$SESSION_DIR/threads" --limit 20
```

### Workflow 4: Error Detection

**When user asks:** "Show me errors" or "What's failing?"

**Execute:**
```bash
langsmith-fetch traces --last-n-minutes 30 --limit 50 --format raw | grep -i "error\|failed\|exception"
```

**Analyze and report:**
1. Total errors found
2. Error types and frequency
3. When errors occurred
4. Which agents/tools failed
5. Common patterns

## Common Use Cases

### Use Case 1: Agent Not Responding

1. Check if traces exist:
   ```bash
   langsmith-fetch traces --last-n-minutes 5 --limit 5
   ```
2. If no traces found:
   - Check if tracing is disabled
   - Check if environment variables are set
   - Verify the agent actually ran

### Use Case 2: Wrong Tool Called

1. Get the specific trace
2. Review available tools at execution time
3. Check the agent's reasoning for tool selection
4. Examine tool descriptions/instructions
5. Suggest prompt or tool config improvements

### Use Case 3: Memory Not Working

1. Search for memory operations:
   ```bash
   langsmith-fetch traces --last-n-minutes 10 --limit 20 --format raw | grep -i "memory\|recall\|store"
   ```
2. Check:
   - Were memory tools called?
   - Did recall return results?
   - Were memories actually stored?
   - Are retrieved memories being used?

### Use Case 4: Performance Issues

1. Export with metadata:
   ```bash
   langsmith-fetch traces ./perf-analysis --last-n-minutes 30 --limit 50 --include-metadata
   ```
2. Analyze:
   - Execution time per trace
   - Tool call latencies
   - Token usage
   - Number of iterations
   - Slowest operations

## Troubleshooting

### No traces found matching criteria

Possible causes:
1. No agent activity in the timeframe
2. Tracing is disabled
3. Wrong project name
4. API key issues

### Project not found

Solution:
```bash
langsmith-fetch config show
langsmith-fetch config set project "your-project-name"
```

## Best Practices

1. Always check if `langsmith-fetch` is installed before running commands
2. Verify environment variables are set
3. Use `--format pretty` for human-readable output
4. Use `--format json` when you need detailed analysis
5. When exporting sessions, create organized folder structures
6. Always provide clear analysis and actionable insights

## Resources

- LangSmith Fetch CLI: https://github.com/langchain-ai/langsmith-fetch
- LangSmith Studio: https://smith.langchain.com/
- LangChain Docs: https://docs.langchain.com/
- This Skill Repo: https://github.com/OthmanAdi/langsmith-fetch-skill
