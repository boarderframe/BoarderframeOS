"""
MemoryMixin - Agent memory and state management
Provides short-term and long-term memory capabilities
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
import hashlib


class MemoryMixin:
    """Agent memory capabilities"""
    
    def __init__(self):
        """Initialize memory systems"""
        # Short-term memory (working memory)
        self.short_term_memory = deque(maxlen=100)
        
        # Long-term memory (episodic)
        self.long_term_memory: List[Dict[str, Any]] = []
        self.max_long_term_memories = 10000
        
        # Semantic memory (facts and knowledge)
        self.semantic_memory: Dict[str, Any] = {}
        
        # Procedural memory (learned patterns)
        self.procedural_memory: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Memory indices for fast retrieval
        self.memory_index: Dict[str, Set[int]] = defaultdict(set)
        self.memory_embeddings: Dict[str, List[float]] = {}  # For similarity search
        
        # Memory management
        self.memory_consolidation_interval = 300  # 5 minutes
        self.last_consolidation = datetime.now()
        
    async def remember(self, memory_type: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a memory with metadata"""
        memory_id = self._generate_memory_id(content)
        
        memory_entry = {
            "id": memory_id,
            "type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "access_count": 0,
            "importance": self._calculate_importance(content, metadata)
        }
        
        # Store in appropriate memory system
        if memory_type == "working":
            self.short_term_memory.append(memory_entry)
        elif memory_type == "episodic":
            await self._store_episodic_memory(memory_entry)
        elif memory_type == "semantic":
            await self._store_semantic_memory(memory_entry)
        elif memory_type == "procedural":
            await self._store_procedural_memory(memory_entry)
            
        # Update indices
        await self._index_memory(memory_entry)
        
        # Check if consolidation needed
        await self._check_memory_consolidation()
        
        return memory_id
        
    async def recall(self, query: str, memory_types: Optional[List[str]] = None, 
                    limit: int = 10) -> List[Dict[str, Any]]:
        """Recall memories based on query"""
        if memory_types is None:
            memory_types = ["working", "episodic", "semantic", "procedural"]
            
        results = []
        
        # Search each memory type
        for mem_type in memory_types:
            if mem_type == "working":
                results.extend(self._search_working_memory(query, limit))
            elif mem_type == "episodic":
                results.extend(await self._search_episodic_memory(query, limit))
            elif mem_type == "semantic":
                results.extend(self._search_semantic_memory(query, limit))
            elif mem_type == "procedural":
                results.extend(self._search_procedural_memory(query, limit))
                
        # Sort by relevance and recency
        results.sort(key=lambda x: (x.get("relevance", 0), x.get("timestamp", "")), reverse=True)
        
        # Update access counts
        for memory in results[:limit]:
            memory["access_count"] += 1
            
        return results[:limit]
        
    async def recall_by_similarity(self, reference_content: Any, limit: int = 5) -> List[Dict[str, Any]]:
        """Recall memories similar to reference content"""
        # In production, this would use embeddings and vector similarity
        # For now, use simple string matching
        results = []
        reference_str = str(reference_content).lower()
        
        # Search all memories
        all_memories = list(self.short_term_memory) + self.long_term_memory
        
        for memory in all_memories:
            content_str = str(memory.get("content", "")).lower()
            similarity = self._calculate_similarity(reference_str, content_str)
            
            if similarity > 0.3:  # Threshold
                memory_copy = memory.copy()
                memory_copy["similarity"] = similarity
                results.append(memory_copy)
                
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:limit]
        
    async def forget(self, memory_id: str) -> bool:
        """Forget a specific memory"""
        # Remove from short-term memory
        self.short_term_memory = deque(
            [m for m in self.short_term_memory if m.get("id") != memory_id],
            maxlen=100
        )
        
        # Remove from long-term memory
        self.long_term_memory = [m for m in self.long_term_memory if m.get("id") != memory_id]
        
        # Remove from semantic memory
        keys_to_remove = [k for k, v in self.semantic_memory.items() 
                         if isinstance(v, dict) and v.get("id") == memory_id]
        for key in keys_to_remove:
            del self.semantic_memory[key]
            
        # Remove from indices
        for index_set in self.memory_index.values():
            index_set.discard(memory_id)
            
        return True
        
    def get_working_memory(self) -> List[Dict[str, Any]]:
        """Get current working memory contents"""
        return list(self.short_term_memory)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            "working_memory_size": len(self.short_term_memory),
            "long_term_memory_size": len(self.long_term_memory),
            "semantic_memory_size": len(self.semantic_memory),
            "procedural_patterns": sum(len(patterns) for patterns in self.procedural_memory.values()),
            "total_memories": (
                len(self.short_term_memory) + 
                len(self.long_term_memory) + 
                len(self.semantic_memory)
            ),
            "last_consolidation": self.last_consolidation.isoformat()
        }
        
    async def _store_episodic_memory(self, memory_entry: Dict[str, Any]) -> None:
        """Store episodic memory with management"""
        self.long_term_memory.append(memory_entry)
        
        # Manage memory size
        if len(self.long_term_memory) > self.max_long_term_memories:
            # Remove least important/accessed memories
            self.long_term_memory.sort(
                key=lambda x: (x.get("importance", 0) * x.get("access_count", 1)),
                reverse=True
            )
            self.long_term_memory = self.long_term_memory[:self.max_long_term_memories]
            
    async def _store_semantic_memory(self, memory_entry: Dict[str, Any]) -> None:
        """Store semantic fact or knowledge"""
        content = memory_entry["content"]
        
        if isinstance(content, dict):
            # Store structured knowledge
            for key, value in content.items():
                self.semantic_memory[key] = {
                    "value": value,
                    "id": memory_entry["id"],
                    "timestamp": memory_entry["timestamp"],
                    "confidence": memory_entry.get("metadata", {}).get("confidence", 1.0)
                }
        else:
            # Store as single fact
            key = memory_entry.get("metadata", {}).get("key", memory_entry["id"])
            self.semantic_memory[key] = {
                "value": content,
                "id": memory_entry["id"],
                "timestamp": memory_entry["timestamp"]
            }
            
    async def _store_procedural_memory(self, memory_entry: Dict[str, Any]) -> None:
        """Store procedural pattern or skill"""
        pattern_type = memory_entry.get("metadata", {}).get("pattern_type", "general")
        
        pattern = {
            "id": memory_entry["id"],
            "pattern": memory_entry["content"],
            "success_rate": memory_entry.get("metadata", {}).get("success_rate", 0.0),
            "usage_count": 0,
            "timestamp": memory_entry["timestamp"]
        }
        
        self.procedural_memory[pattern_type].append(pattern)
        
        # Keep only top patterns per type
        if len(self.procedural_memory[pattern_type]) > 50:
            self.procedural_memory[pattern_type].sort(
                key=lambda x: x["success_rate"] * x["usage_count"],
                reverse=True
            )
            self.procedural_memory[pattern_type] = self.procedural_memory[pattern_type][:50]
            
    async def _index_memory(self, memory_entry: Dict[str, Any]) -> None:
        """Index memory for fast retrieval"""
        memory_id = memory_entry["id"]
        content_str = str(memory_entry["content"]).lower()
        
        # Extract keywords for indexing
        keywords = self._extract_keywords(content_str)
        
        for keyword in keywords:
            self.memory_index[keyword].add(memory_id)
            
    def _search_working_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search working memory"""
        query_lower = query.lower()
        results = []
        
        for memory in self.short_term_memory:
            content_str = str(memory.get("content", "")).lower()
            if query_lower in content_str:
                memory_copy = memory.copy()
                memory_copy["relevance"] = self._calculate_relevance(query_lower, content_str)
                results.append(memory_copy)
                
        return results
        
    async def _search_episodic_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search episodic memory"""
        query_lower = query.lower()
        results = []
        
        # Use index for faster search
        keywords = self._extract_keywords(query_lower)
        candidate_ids = set()
        
        for keyword in keywords:
            if keyword in self.memory_index:
                candidate_ids.update(self.memory_index[keyword])
                
        # Search candidates
        for memory in self.long_term_memory:
            if memory["id"] in candidate_ids:
                memory_copy = memory.copy()
                content_str = str(memory.get("content", "")).lower()
                memory_copy["relevance"] = self._calculate_relevance(query_lower, content_str)
                results.append(memory_copy)
                
        return results
        
    def _search_semantic_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search semantic memory"""
        query_lower = query.lower()
        results = []
        
        for key, value_info in self.semantic_memory.items():
            if query_lower in key.lower() or query_lower in str(value_info.get("value", "")).lower():
                result = {
                    "id": value_info.get("id", key),
                    "type": "semantic",
                    "content": {key: value_info["value"]},
                    "timestamp": value_info.get("timestamp", ""),
                    "relevance": self._calculate_relevance(query_lower, f"{key} {value_info['value']}")
                }
                results.append(result)
                
        return results
        
    def _search_procedural_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search procedural memory"""
        query_lower = query.lower()
        results = []
        
        for pattern_type, patterns in self.procedural_memory.items():
            for pattern in patterns:
                pattern_str = str(pattern.get("pattern", "")).lower()
                if query_lower in pattern_str or query_lower in pattern_type.lower():
                    result = {
                        "id": pattern["id"],
                        "type": "procedural",
                        "content": pattern["pattern"],
                        "metadata": {
                            "pattern_type": pattern_type,
                            "success_rate": pattern["success_rate"],
                            "usage_count": pattern["usage_count"]
                        },
                        "timestamp": pattern.get("timestamp", ""),
                        "relevance": self._calculate_relevance(query_lower, pattern_str)
                    }
                    results.append(result)
                    
        return results
        
    async def _check_memory_consolidation(self) -> None:
        """Consolidate memories from short-term to long-term"""
        if (datetime.now() - self.last_consolidation).seconds < self.memory_consolidation_interval:
            return
            
        # Move important working memories to long-term
        consolidated = []
        for memory in list(self.short_term_memory):
            if memory.get("importance", 0) > 0.7 or memory.get("access_count", 0) > 3:
                await self._store_episodic_memory(memory)
                consolidated.append(memory["id"])
                
        # Remove consolidated memories from working memory
        self.short_term_memory = deque(
            [m for m in self.short_term_memory if m["id"] not in consolidated],
            maxlen=100
        )
        
        self.last_consolidation = datetime.now()
        
        if consolidated and hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Consolidated {len(consolidated)} memories to long-term storage")
            
    def _generate_memory_id(self, content: Any) -> str:
        """Generate unique memory ID"""
        content_str = f"{datetime.now().isoformat()}_{str(content)}"
        return hashlib.md5(content_str.encode()).hexdigest()[:16]
        
    def _calculate_importance(self, content: Any, metadata: Optional[Dict[str, Any]]) -> float:
        """Calculate memory importance score"""
        importance = 0.5  # Base importance
        
        # Adjust based on metadata
        if metadata:
            if metadata.get("priority") == "high":
                importance += 0.3
            if metadata.get("source") == "user":
                importance += 0.2
            if metadata.get("emotion_intensity", 0) > 0.7:
                importance += 0.1
                
        # Adjust based on content characteristics
        content_str = str(content)
        if len(content_str) > 200:  # Detailed information
            importance += 0.1
            
        return min(importance, 1.0)
        
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        # Simple relevance based on keyword overlap
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
            
        overlap = len(query_words.intersection(content_words))
        return overlap / len(query_words)
        
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
        
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text for indexing"""
        # Simple keyword extraction - in production use NLP
        stopwords = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "but", "in", "to", "for"}
        words = text.lower().split()
        keywords = {word for word in words if len(word) > 3 and word not in stopwords}
        return keywords