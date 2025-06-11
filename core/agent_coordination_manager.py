"""
Agent Coordination Manager - Orchestrates complex multi-agent workflows and coordination patterns
Provides high-level coordination primitives for agent collaboration
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .enhanced_message_bus import (
    EnhancedAgentMessage,
    MessagePriority,
    MessageType,
    RoutingStrategy,
    WorkflowStep,
    enhanced_message_bus,
    send_capability_request,
)


class CoordinationPattern(Enum):
    SEQUENTIAL = "sequential"  # Execute agents one after another
    PARALLEL = "parallel"  # Execute agents simultaneously
    PIPELINE = "pipeline"  # Data flows through agents in sequence
    SCATTER_GATHER = "scatter_gather"  # Distribute work, then collect results
    CONSENSUS = "consensus"  # Agents reach agreement
    AUCTION = "auction"  # Agents bid for tasks
    ELECTION = "election"  # Elect a leader agent


class TaskState(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CoordinationTask:
    """Represents a coordination task"""

    task_id: str
    pattern: CoordinationPattern
    participants: List[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    timeout: Optional[int] = None
    progress: float = 0.0


@dataclass
class AgentBid:
    """Represents an agent's bid for a task"""

    agent_name: str
    task_id: str
    bid_amount: float
    capabilities: List[str]
    estimated_time: int
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsensusManager:
    """Manages consensus-based decision making among agents"""

    def __init__(self):
        self.active_proposals: Dict[str, Dict[str, Any]] = {}
        self.votes: Dict[str, Dict[str, Any]] = {}  # proposal_id -> {agent: vote}

    async def create_proposal(
        self,
        proposal_id: str,
        proposer: str,
        proposal_data: Dict[str, Any],
        participants: List[str],
        voting_timeout: int = 300,
    ) -> str:
        """Create a new proposal for consensus"""
        self.active_proposals[proposal_id] = {
            "id": proposal_id,
            "proposer": proposer,
            "data": proposal_data,
            "participants": participants,
            "created_at": datetime.now(),
            "timeout": voting_timeout,
            "status": "active",
        }

        self.votes[proposal_id] = {}

        # Send proposal to all participants
        for participant in participants:
            if participant != proposer:
                message = EnhancedAgentMessage(
                    from_agent="CoordinationManager",
                    to_agent=participant,
                    message_type=MessageType.COORDINATION,
                    content={
                        "action": "vote_request",
                        "proposal_id": proposal_id,
                        "proposal_data": proposal_data,
                        "timeout": voting_timeout,
                    },
                    routing_strategy=RoutingStrategy.DIRECT,
                )
                await enhanced_message_bus.send_enhanced_message(message)

        return proposal_id

    async def cast_vote(
        self, proposal_id: str, agent_name: str, vote: Dict[str, Any]
    ) -> bool:
        """Cast a vote for a proposal"""
        if proposal_id not in self.active_proposals:
            return False

        if agent_name not in self.active_proposals[proposal_id]["participants"]:
            return False

        self.votes[proposal_id][agent_name] = {
            "vote": vote,
            "timestamp": datetime.now(),
        }

        # Check if consensus is reached
        await self._check_consensus(proposal_id)
        return True

    async def _check_consensus(self, proposal_id: str):
        """Check if consensus has been reached"""
        proposal = self.active_proposals[proposal_id]
        votes = self.votes[proposal_id]

        total_participants = len(proposal["participants"])
        total_votes = len(votes)

        # Simple majority consensus (can be customized)
        if total_votes >= (total_participants * 0.6):  # 60% participation
            # Analyze votes for consensus
            approval_votes = sum(
                1
                for vote_data in votes.values()
                if vote_data["vote"].get("approve", False)
            )

            if approval_votes >= (total_votes * 0.6):  # 60% approval
                proposal["status"] = "approved"
                await self._notify_consensus_result(proposal_id, "approved")
            else:
                proposal["status"] = "rejected"
                await self._notify_consensus_result(proposal_id, "rejected")

    async def _notify_consensus_result(self, proposal_id: str, result: str):
        """Notify all participants of consensus result"""
        proposal = self.active_proposals[proposal_id]

        for participant in proposal["participants"]:
            message = EnhancedAgentMessage(
                from_agent="CoordinationManager",
                to_agent=participant,
                message_type=MessageType.COORDINATION,
                content={
                    "action": "consensus_result",
                    "proposal_id": proposal_id,
                    "result": result,
                    "votes": self.votes[proposal_id],
                },
                routing_strategy=RoutingStrategy.DIRECT,
            )
            await enhanced_message_bus.send_enhanced_message(message)

    async def request_consensus(
        self,
        proposal_id: str,
        participants: List[str],
        proposal: Dict[str, Any],
        voting_method: str = "majority",
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Request consensus decision from multiple agents"""
        await self.create_proposal(
            proposal_id, "CoordinationManager", proposal, participants, timeout_seconds
        )

        # Wait for consensus with timeout
        start_time = datetime.now()
        while True:
            if proposal_id in self.active_proposals:
                status = self.active_proposals[proposal_id]["status"]
                if status in ["approved", "rejected"]:
                    return {
                        "proposal_id": proposal_id,
                        "status": status,
                        "votes": self.votes.get(proposal_id, {}),
                        "participants": participants,
                    }

            # Check timeout
            if (datetime.now() - start_time).total_seconds() > timeout_seconds:
                return {
                    "proposal_id": proposal_id,
                    "status": "timeout",
                    "votes": self.votes.get(proposal_id, {}),
                    "participants": participants,
                }

            await asyncio.sleep(1)


class AuctionManager:
    """Manages auction-based task allocation"""

    def __init__(self):
        self.active_auctions: Dict[str, Dict[str, Any]] = {}
        self.bids: Dict[str, List[AgentBid]] = {}

    async def create_auction(
        self,
        auction_id: str,
        task_description: Dict[str, Any],
        required_capabilities: List[str],
        bidding_timeout: int = 120,
    ) -> str:
        """Create a new auction for task allocation"""
        self.active_auctions[auction_id] = {
            "id": auction_id,
            "task": task_description,
            "required_capabilities": required_capabilities,
            "created_at": datetime.now(),
            "timeout": bidding_timeout,
            "status": "active",
        }

        self.bids[auction_id] = []

        # Broadcast auction to capable agents
        message = EnhancedAgentMessage(
            from_agent="CoordinationManager",
            to_agent="",  # Will be resolved by capability routing
            message_type=MessageType.COORDINATION,
            content={
                "action": "auction_announcement",
                "auction_id": auction_id,
                "task": task_description,
                "timeout": bidding_timeout,
            },
            routing_strategy=RoutingStrategy.CAPABILITY_BASED,
            required_capabilities=required_capabilities,
        )
        await enhanced_message_bus.send_enhanced_message(message)

        # Schedule auction closure
        asyncio.create_task(
            self._close_auction_after_timeout(auction_id, bidding_timeout)
        )

        return auction_id

    async def start_auction(
        self,
        auction_id: str,
        task: Dict[str, Any],
        participants: List[str],
        duration_seconds: int = 120,
    ) -> Dict[str, Any]:
        """Start a new auction for task allocation"""
        try:
            # Create auction with required capabilities based on participants
            required_capabilities = []
            if "analysis" in str(task).lower():
                required_capabilities.append("analysis")
            if "research" in str(task).lower():
                required_capabilities.append("research")

            result_auction_id = await self.create_auction(
                auction_id, task, required_capabilities, duration_seconds
            )

            return {
                "status": "success",
                "auction_id": result_auction_id,
                "participants": participants,
                "duration": duration_seconds,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def submit_bid(self, auction_id: str, bid: AgentBid) -> bool:
        """Submit a bid for an auction"""
        if auction_id not in self.active_auctions:
            return False

        if self.active_auctions[auction_id]["status"] != "active":
            return False

        self.bids[auction_id].append(bid)
        return True

    async def _close_auction_after_timeout(self, auction_id: str, timeout: int):
        """Close auction after timeout and select winner"""
        await asyncio.sleep(timeout)

        if (
            auction_id in self.active_auctions
            and self.active_auctions[auction_id]["status"] == "active"
        ):
            await self._select_auction_winner(auction_id)

    async def _select_auction_winner(self, auction_id: str):
        """Select the winning bid and notify participants"""
        if not self.bids[auction_id]:
            self.active_auctions[auction_id]["status"] = "failed"
            return

        # Simple selection: lowest bid with highest confidence
        winning_bid = min(
            self.bids[auction_id],
            key=lambda bid: bid.bid_amount - (bid.confidence * 10),
        )

        self.active_auctions[auction_id]["status"] = "completed"
        self.active_auctions[auction_id]["winner"] = winning_bid.agent_name

        # Notify winner
        message = EnhancedAgentMessage(
            from_agent="CoordinationManager",
            to_agent=winning_bid.agent_name,
            message_type=MessageType.TASK_REQUEST,
            content={
                "action": "auction_won",
                "auction_id": auction_id,
                "task": self.active_auctions[auction_id]["task"],
                "winning_bid": winning_bid.bid_amount,
            },
            routing_strategy=RoutingStrategy.DIRECT,
        )
        await enhanced_message_bus.send_enhanced_message(message)

        # Notify other bidders
        for bid in self.bids[auction_id]:
            if bid.agent_name != winning_bid.agent_name:
                message = EnhancedAgentMessage(
                    from_agent="CoordinationManager",
                    to_agent=bid.agent_name,
                    message_type=MessageType.COORDINATION,
                    content={
                        "action": "auction_lost",
                        "auction_id": auction_id,
                        "winning_agent": winning_bid.agent_name,
                        "winning_bid": winning_bid.bid_amount,
                    },
                    routing_strategy=RoutingStrategy.DIRECT,
                )
                await enhanced_message_bus.send_enhanced_message(message)


class AgentCoordinationManager:
    """Main coordination manager for multi-agent workflows"""

    def __init__(self):
        self.active_tasks: Dict[str, CoordinationTask] = {}
        self.consensus_manager = ConsensusManager()
        self.auction_manager = AuctionManager()
        self.agent_pools: Dict[str, List[str]] = {}  # capability -> [agents]
        self.logger = logging.getLogger("AgentCoordinationManager")

        # Performance tracking
        self.coordination_metrics: Dict[str, Any] = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_completion_time": 0,
            "patterns_used": {},
        }

    async def start(self):
        """Start the coordination manager"""
        # Register with message bus to handle coordination messages
        await enhanced_message_bus.register_agent(
            "CoordinationManager",
            capabilities=["coordination", "workflow", "consensus", "auction"],
        )

        # Start background tasks
        asyncio.create_task(self._monitor_task_timeouts())
        asyncio.create_task(self._update_agent_pools())

        self.logger.info("Agent Coordination Manager started")

    async def stop(self):
        """Stop the coordination manager"""
        self.logger.info("Agent Coordination Manager stopped")

    async def create_workflow(
        self,
        workflow_id: str,
        pattern: CoordinationPattern,
        participants: List[str],
        coordinator: str,
        tasks: List[Dict],
    ) -> str:
        """Create a new workflow"""
        task = CoordinationTask(
            task_id=workflow_id,
            pattern=pattern,
            participants=participants,
            input_data={"tasks": tasks, "coordinator": coordinator},
        )

        self.active_tasks[workflow_id] = task
        self.logger.info(f"Created workflow {workflow_id} with pattern {pattern}")
        return workflow_id

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow"""
        if workflow_id not in self.active_tasks:
            return None

        task = self.active_tasks[workflow_id]
        return {
            "workflow_id": workflow_id,
            "pattern": task.pattern.value,
            "state": task.state.value,
            "participants": task.participants,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "timeout": task.timeout,
            "input_data": task.input_data,
            "output_data": task.output_data,
        }

    async def check_timeouts(self):
        """Check for timed out tasks"""
        current_time = datetime.now()
        for task_id, task in list(self.active_tasks.items()):
            if (
                task.timeout
                and task.created_at + timedelta(seconds=task.timeout) < current_time
            ):
                self.logger.warning(f"Task {task_id} timed out")
                task.state = TaskState.CANCELLED

    async def get_usage_statistics(self) -> Dict[str, Any]:
        """Get coordination usage statistics"""
        return self.coordination_metrics

    async def coordinate_agents(
        self,
        pattern: CoordinationPattern,
        participants: List[str],
        task_data: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> str:
        """Coordinate agents using specified pattern"""
        task_id = str(uuid.uuid4())

        task = CoordinationTask(
            task_id=task_id,
            pattern=pattern,
            participants=participants,
            input_data=task_data,
            timeout=timeout,
        )

        self.active_tasks[task_id] = task

        # Execute coordination pattern
        if pattern == CoordinationPattern.SEQUENTIAL:
            await self._execute_sequential(task)
        elif pattern == CoordinationPattern.PARALLEL:
            await self._execute_parallel(task)
        elif pattern == CoordinationPattern.PIPELINE:
            await self._execute_pipeline(task)
        elif pattern == CoordinationPattern.SCATTER_GATHER:
            await self._execute_scatter_gather(task)
        elif pattern == CoordinationPattern.CONSENSUS:
            await self._execute_consensus(task)
        elif pattern == CoordinationPattern.AUCTION:
            await self._execute_auction(task)
        else:
            task.state = TaskState.FAILED
            self.logger.error(f"Unknown coordination pattern: {pattern}")

        # Update metrics
        self.coordination_metrics["patterns_used"][pattern.value] = (
            self.coordination_metrics["patterns_used"].get(pattern.value, 0) + 1
        )

        return task_id

    async def _execute_sequential(self, task: CoordinationTask):
        """Execute agents sequentially"""
        task.state = TaskState.IN_PROGRESS
        current_data = task.input_data.copy()

        for i, agent in enumerate(task.participants):
            try:
                # Send task to agent
                message = EnhancedAgentMessage(
                    from_agent="CoordinationManager",
                    to_agent=agent,
                    message_type=MessageType.TASK_REQUEST,
                    content={
                        "task_id": task.task_id,
                        "step": i,
                        "input_data": current_data,
                        "coordination_pattern": "sequential",
                    },
                    routing_strategy=RoutingStrategy.DIRECT,
                    conversation_id=task.task_id,
                )

                await enhanced_message_bus.send_enhanced_message(message)

                # Wait for response (simplified - in practice would use proper response handling)
                await asyncio.sleep(1)  # Placeholder for actual response waiting

                # Update progress
                task.progress = (i + 1) / len(task.participants)

            except Exception as e:
                task.state = TaskState.FAILED
                self.logger.error(f"Sequential execution failed at step {i}: {e}")
                return

        task.state = TaskState.COMPLETED
        self.coordination_metrics["tasks_completed"] += 1

    async def _execute_parallel(self, task: CoordinationTask):
        """Execute agents in parallel"""
        task.state = TaskState.IN_PROGRESS

        # Send tasks to all agents simultaneously
        tasks = []
        for agent in task.participants:
            message = EnhancedAgentMessage(
                from_agent="CoordinationManager",
                to_agent=agent,
                message_type=MessageType.TASK_REQUEST,
                content={
                    "task_id": task.task_id,
                    "input_data": task.input_data,
                    "coordination_pattern": "parallel",
                },
                routing_strategy=RoutingStrategy.DIRECT,
                conversation_id=task.task_id,
            )

            tasks.append(enhanced_message_bus.send_enhanced_message(message))

        try:
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            task.state = TaskState.COMPLETED
            task.progress = 1.0
            self.coordination_metrics["tasks_completed"] += 1

        except Exception as e:
            task.state = TaskState.FAILED
            self.coordination_metrics["tasks_failed"] += 1
            self.logger.error(f"Parallel execution failed: {e}")

    async def _execute_pipeline(self, task: CoordinationTask):
        """Execute agents in pipeline pattern"""
        task.state = TaskState.IN_PROGRESS
        current_data = task.input_data.copy()

        for i, agent in enumerate(task.participants):
            try:
                # Send data to next agent in pipeline
                message = EnhancedAgentMessage(
                    from_agent="CoordinationManager",
                    to_agent=agent,
                    message_type=MessageType.TASK_REQUEST,
                    content={
                        "task_id": task.task_id,
                        "pipeline_stage": i,
                        "input_data": current_data,
                        "coordination_pattern": "pipeline",
                    },
                    routing_strategy=RoutingStrategy.DIRECT,
                    conversation_id=task.task_id,
                )

                await enhanced_message_bus.send_enhanced_message(message)

                # In practice, would wait for response and update current_data
                await asyncio.sleep(0.5)

                task.progress = (i + 1) / len(task.participants)

            except Exception as e:
                task.state = TaskState.FAILED
                self.logger.error(f"Pipeline execution failed at stage {i}: {e}")
                return

        task.state = TaskState.COMPLETED
        self.coordination_metrics["tasks_completed"] += 1

    async def _execute_scatter_gather(self, task: CoordinationTask):
        """Execute scatter-gather pattern"""
        task.state = TaskState.IN_PROGRESS

        # Scatter phase: distribute work to all agents
        scatter_tasks = []
        for i, agent in enumerate(task.participants):
            # Partition data for each agent
            agent_data = task.input_data.copy()
            agent_data["partition"] = i
            agent_data["total_partitions"] = len(task.participants)

            message = EnhancedAgentMessage(
                from_agent="CoordinationManager",
                to_agent=agent,
                message_type=MessageType.TASK_REQUEST,
                content={
                    "task_id": task.task_id,
                    "input_data": agent_data,
                    "coordination_pattern": "scatter_gather",
                    "phase": "scatter",
                },
                routing_strategy=RoutingStrategy.DIRECT,
                conversation_id=task.task_id,
            )

            scatter_tasks.append(enhanced_message_bus.send_enhanced_message(message))

        try:
            # Wait for scatter phase
            await asyncio.gather(*scatter_tasks)

            # Gather phase would collect results
            # (Implementation depends on specific use case)

            task.state = TaskState.COMPLETED
            task.progress = 1.0
            self.coordination_metrics["tasks_completed"] += 1

        except Exception as e:
            task.state = TaskState.FAILED
            self.coordination_metrics["tasks_failed"] += 1
            self.logger.error(f"Scatter-gather execution failed: {e}")

    async def _execute_consensus(self, task: CoordinationTask):
        """Execute consensus-based coordination"""
        proposal_id = f"consensus_{task.task_id}"

        await self.consensus_manager.create_proposal(
            proposal_id=proposal_id,
            proposer="CoordinationManager",
            proposal_data=task.input_data,
            participants=task.participants,
            voting_timeout=300,
        )

        task.state = TaskState.IN_PROGRESS

    async def _execute_auction(self, task: CoordinationTask):
        """Execute auction-based coordination"""
        auction_id = f"auction_{task.task_id}"

        required_capabilities = task.input_data.get("required_capabilities", [])

        await self.auction_manager.create_auction(
            auction_id=auction_id,
            task_description=task.input_data,
            required_capabilities=required_capabilities,
            bidding_timeout=120,
        )

        task.state = TaskState.IN_PROGRESS

    async def _monitor_task_timeouts(self):
        """Monitor and handle task timeouts"""
        while True:
            try:
                current_time = datetime.now()

                for task_id, task in list(self.active_tasks.items()):
                    if task.timeout and task.state == TaskState.IN_PROGRESS:
                        elapsed = (current_time - task.created_at).total_seconds()

                        if elapsed > task.timeout:
                            task.state = TaskState.FAILED
                            self.coordination_metrics["tasks_failed"] += 1
                            self.logger.warning(
                                f"Task {task_id} timed out after {elapsed}s"
                            )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Error monitoring task timeouts: {e}")

    async def _update_agent_pools(self):
        """Update agent capability pools"""
        while True:
            try:
                # Get current agent capabilities from message bus
                capabilities_map = enhanced_message_bus.agent_capabilities

                # Rebuild capability pools
                self.agent_pools.clear()
                for agent, capabilities in capabilities_map.items():
                    for capability in capabilities:
                        if capability not in self.agent_pools:
                            self.agent_pools[capability] = []
                        self.agent_pools[capability].append(agent)

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                self.logger.error(f"Error updating agent pools: {e}")

    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics"""
        return {
            "active_tasks": len(self.active_tasks),
            "metrics": self.coordination_metrics,
            "agent_pools": {
                cap: len(agents) for cap, agents in self.agent_pools.items()
            },
            "consensus_proposals": len(self.consensus_manager.active_proposals),
            "active_auctions": len(self.auction_manager.active_auctions),
        }


# Global coordination manager instance
coordination_manager = AgentCoordinationManager()


# Convenience functions
async def coordinate_sequential(
    participants: List[str], task_data: Dict[str, Any], timeout: Optional[int] = None
) -> str:
    """Coordinate agents sequentially"""
    return await coordination_manager.coordinate_agents(
        CoordinationPattern.SEQUENTIAL, participants, task_data, timeout
    )


async def coordinate_parallel(
    participants: List[str], task_data: Dict[str, Any], timeout: Optional[int] = None
) -> str:
    """Coordinate agents in parallel"""
    return await coordination_manager.coordinate_agents(
        CoordinationPattern.PARALLEL, participants, task_data, timeout
    )


async def create_consensus_proposal(
    proposal_data: Dict[str, Any], participants: List[str], voting_timeout: int = 300
) -> str:
    """Create a consensus proposal"""
    proposal_id = f"proposal_{uuid.uuid4()}"
    return await coordination_manager.consensus_manager.create_proposal(
        proposal_id, "CoordinationManager", proposal_data, participants, voting_timeout
    )


async def create_task_auction(
    task_description: Dict[str, Any],
    required_capabilities: List[str],
    bidding_timeout: int = 120,
) -> str:
    """Create a task auction"""
    auction_id = f"auction_{uuid.uuid4()}"
    return await coordination_manager.auction_manager.create_auction(
        auction_id, task_description, required_capabilities, bidding_timeout
    )
