"""
ToolRunnerMixin - Tool execution framework
Manages agent tool capabilities and execution
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime
import inspect
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definition of an agent tool"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    requires_approval: bool = False
    cost_estimate: float = 0.0
    timeout_seconds: int = 30


@dataclass
class ToolExecutionResult:
    """Result of tool execution"""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cost_incurred: float = 0.0


class ToolRunnerMixin:
    """Tool execution capabilities"""
    
    def __init__(self):
        """Initialize tool runner"""
        self.available_tools: Dict[str, ToolDefinition] = {}
        self.tool_execution_history: List[Dict[str, Any]] = []
        self.max_history_size = 500
        self.tool_usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Tool execution policies
        self.max_parallel_tools = 5
        self.global_timeout = 300  # 5 minutes
        self.require_approval_for_high_cost = True
        self.cost_threshold = 0.01  # $0.01
        
    def register_tool(self, tool_def: ToolDefinition) -> None:
        """Register a tool for the agent"""
        self.available_tools[tool_def.name] = tool_def
        self.tool_usage_stats[tool_def.name] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_cost": 0.0,
            "average_execution_time": 0.0
        }
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Registered tool: {tool_def.name}")
            
    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool"""
        if tool_name in self.available_tools:
            del self.available_tools[tool_name]
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"Unregistered tool: {tool_name}")
                
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a single tool"""
        if tool_name not in self.available_tools:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Tool '{tool_name}' not found"
            )
            
        tool_def = self.available_tools[tool_name]
        
        # Check if approval required
        if await self._requires_approval(tool_def, parameters):
            approved = await self._request_approval(tool_def, parameters)
            if not approved:
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=False,
                    output=None,
                    error="Execution not approved"
                )
                
        # Execute with timeout
        start_time = time.time()
        try:
            if inspect.iscoroutinefunction(tool_def.function):
                result = await asyncio.wait_for(
                    tool_def.function(**parameters),
                    timeout=tool_def.timeout_seconds
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: tool_def.function(**parameters)),
                    timeout=tool_def.timeout_seconds
                )
                
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # Update statistics
            self._update_tool_stats(tool_name, True, execution_time, tool_def.cost_estimate)
            
            # Record execution
            self._record_execution(tool_name, parameters, result, execution_time, True)
            
            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                output=result,
                execution_time_ms=execution_time,
                cost_incurred=tool_def.cost_estimate
            )
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Tool execution timed out after {tool_def.timeout_seconds}s"
            
            self._update_tool_stats(tool_name, False, execution_time, 0)
            self._record_execution(tool_name, parameters, None, execution_time, False, error_msg)
            
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=error_msg,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Tool execution failed: {str(e)}"
            
            self._update_tool_stats(tool_name, False, execution_time, 0)
            self._record_execution(tool_name, parameters, None, execution_time, False, error_msg)
            
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
                
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=error_msg,
                execution_time_ms=execution_time
            )
            
    async def execute_tools_parallel(self, tool_requests: List[Tuple[str, Dict[str, Any]]]) -> List[ToolExecutionResult]:
        """Execute multiple tools in parallel"""
        # Limit parallelism
        if len(tool_requests) > self.max_parallel_tools:
            # Execute in batches
            results = []
            for i in range(0, len(tool_requests), self.max_parallel_tools):
                batch = tool_requests[i:i + self.max_parallel_tools]
                batch_tasks = [self.execute_tool(name, params) for name, params in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend(batch_results)
            return results
        else:
            # Execute all in parallel
            tasks = [self.execute_tool(name, params) for name, params in tool_requests]
            return await asyncio.gather(*tasks)
            
    async def execute_tool_chain(self, tool_chain: List[Tuple[str, Callable[[Any], Dict[str, Any]]]]) -> List[ToolExecutionResult]:
        """Execute tools in sequence, passing output to next tool"""
        results = []
        previous_output = None
        
        for tool_name, param_transformer in tool_chain:
            # Transform parameters based on previous output
            if previous_output is not None:
                parameters = param_transformer(previous_output)
            else:
                parameters = param_transformer({})
                
            # Execute tool
            result = await self.execute_tool(tool_name, parameters)
            results.append(result)
            
            # Check if we should continue
            if not result.success:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.warning(f"Tool chain broken at {tool_name}: {result.error}")
                break
                
            previous_output = result.output
            
        return results
        
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with metadata"""
        return [
            {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": tool_def.parameters,
                "requires_approval": tool_def.requires_approval,
                "cost_estimate": tool_def.cost_estimate,
                "usage_stats": self.tool_usage_stats.get(tool_def.name, {})
            }
            for tool_def in self.available_tools.values()
        ]
        
    def get_tool_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive tool usage report"""
        total_executions = sum(stats["total_calls"] for stats in self.tool_usage_stats.values())
        total_cost = sum(stats["total_cost"] for stats in self.tool_usage_stats.values())
        
        return {
            "total_executions": total_executions,
            "total_cost": total_cost,
            "tool_statistics": self.tool_usage_stats,
            "most_used_tool": max(self.tool_usage_stats.items(), key=lambda x: x[1]["total_calls"])[0] if self.tool_usage_stats else None,
            "highest_cost_tool": max(self.tool_usage_stats.items(), key=lambda x: x[1]["total_cost"])[0] if self.tool_usage_stats else None
        }
        
    async def _requires_approval(self, tool_def: ToolDefinition, parameters: Dict[str, Any]) -> bool:
        """Check if tool execution requires approval"""
        if tool_def.requires_approval:
            return True
            
        if self.require_approval_for_high_cost and tool_def.cost_estimate > self.cost_threshold:
            return True
            
        # Check for risky operations
        risky_keywords = ["delete", "remove", "drop", "truncate", "production"]
        param_str = str(parameters).lower()
        if any(keyword in param_str for keyword in risky_keywords):
            return True
            
        return False
        
    async def _request_approval(self, tool_def: ToolDefinition, parameters: Dict[str, Any]) -> bool:
        """Request approval for tool execution"""
        # In production, this would integrate with governance system
        # For now, log and auto-approve
        if hasattr(self, 'logger') and self.logger:
            self.logger.warning(
                f"Tool {tool_def.name} requires approval. "
                f"Cost: ${tool_def.cost_estimate}, Parameters: {parameters}"
            )
        return True
        
    def _update_tool_stats(self, tool_name: str, success: bool, execution_time: float, cost: float) -> None:
        """Update tool usage statistics"""
        if tool_name not in self.tool_usage_stats:
            return
            
        stats = self.tool_usage_stats[tool_name]
        stats["total_calls"] += 1
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
            
        stats["total_cost"] += cost
        
        # Update average execution time
        current_avg = stats["average_execution_time"]
        total_calls = stats["total_calls"]
        stats["average_execution_time"] = ((current_avg * (total_calls - 1)) + execution_time) / total_calls
        
    def _record_execution(self, tool_name: str, parameters: Dict[str, Any], 
                         result: Any, execution_time: float, success: bool, 
                         error: Optional[str] = None) -> None:
        """Record tool execution in history"""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "parameters": parameters,
            "success": success,
            "execution_time_ms": execution_time,
            "error": error
        }
        
        # Don't store large results in history
        if result is not None and len(str(result)) < 1000:
            execution_record["result"] = result
            
        self.tool_execution_history.append(execution_record)
        
        # Maintain history size limit
        if len(self.tool_execution_history) > self.max_history_size:
            self.tool_execution_history.pop(0)
            
    def get_tool_by_capability(self, capability: str) -> Optional[ToolDefinition]:
        """Find a tool by capability description"""
        capability_lower = capability.lower()
        
        for tool_def in self.available_tools.values():
            if (capability_lower in tool_def.name.lower() or 
                capability_lower in tool_def.description.lower()):
                return tool_def
                
        return None