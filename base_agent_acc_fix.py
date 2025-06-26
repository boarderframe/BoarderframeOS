#!/usr/bin/env python3
"""
BaseAgent ACC Integration Fix
Ensures agents properly respond to messages from ACC
"""

import asyncio
from typing import List
from core.message_bus import AgentMessage, MessageType, message_bus
from core.base_agent import BaseAgent


async def enhance_agent_message_processing(agent: BaseAgent):
    """Enhance an agent to properly handle ACC messages"""
    
    # Store original _process_messages method
    original_process_messages = agent._process_messages
    
    async def enhanced_process_messages(messages: List[AgentMessage]):
        """Enhanced message processing that handles ACC responses"""
        for message in messages:
            try:
                agent.log(f"📥 Processing message: type={message.message_type}, from={message.from_agent}, correlation_id={message.correlation_id}")
                
                # Check if this is a user chat message from ACC
                if (message.message_type == MessageType.TASK_REQUEST and 
                    message.content.get("type") == "user_chat" and 
                    message.requires_response):
                    
                    user_message = message.content.get("message", "")
                    agent.log(f"💬 Received user chat: '{user_message}'")
                    
                    # Call the agent's chat handler
                    if hasattr(agent, 'handle_user_chat'):
                        response_text = await agent.handle_user_chat(user_message)
                        agent.log(f"💭 Generated response: '{response_text[:100]}...'")
                        
                        # Send response back via message bus
                        response_msg = AgentMessage(
                            from_agent=agent.config.name,
                            to_agent="acc_system",  # Send to ACC
                            message_type=MessageType.TASK_RESPONSE,
                            content={"response": response_text},
                            correlation_id=message.correlation_id,
                            requires_response=False
                        )
                        
                        success = await message_bus.send_message(response_msg)
                        if success:
                            agent.log(f"✅ Sent response to ACC (correlation_id: {message.correlation_id})")
                        else:
                            agent.log(f"❌ Failed to send response to ACC", level="error")
                    else:
                        agent.log(f"⚠️ Agent does not have handle_user_chat method", level="warning")
                        
                        # Send a default response
                        response_msg = AgentMessage(
                            from_agent=agent.config.name,
                            to_agent="acc_system",
                            message_type=MessageType.TASK_RESPONSE,
                            content={"response": f"Hello! I am {agent.config.name}. I received your message but don't have a chat handler implemented yet."},
                            correlation_id=message.correlation_id,
                            requires_response=False
                        )
                        await message_bus.send_message(response_msg)
                
                # Also run original processing for other message types
                else:
                    await original_process_messages([message])
                    
            except Exception as e:
                agent.log(f"❌ Error processing message: {e}", level="error")
                import traceback
                traceback.print_exc()
    
    # Replace the method
    agent._process_messages = enhanced_process_messages
    
    # Also ensure agent subscribes to ACC messages
    await message_bus.subscribe_to_topic(agent.config.name, "acc_messages")
    
    agent.log("✅ Enhanced ACC message processing enabled")


def create_acc_enhanced_agent(agent_class):
    """Factory to create an ACC-enhanced agent class"""
    
    class ACCEnhancedAgent(agent_class):
        """Agent with enhanced ACC message handling"""
        
        async def _register_with_message_bus(self):
            """Override to add ACC enhancements after registration"""
            # Call parent registration
            await super()._register_with_message_bus()
            
            # Apply ACC enhancements
            await enhance_agent_message_processing(self)
            
        async def handle_user_chat(self, message: str) -> str:
            """Default chat handler if not implemented by subclass"""
            if hasattr(super(), 'handle_user_chat'):
                return await super().handle_user_chat(message)
            else:
                # Basic response using agent's LLM
                context = {
                    "role": self.config.role,
                    "name": self.config.name,
                    "user_message": message
                }
                
                prompt = f"""You are {self.config.name}, with the role: {self.config.role}.
                
User message: {message}

Please provide a helpful response based on your role and capabilities."""
                
                try:
                    response = await self.llm.complete(prompt)
                    return response.strip()
                except Exception as e:
                    self.log(f"Error generating response: {e}", level="error")
                    return f"I apologize, but I encountered an error processing your message. I am {self.config.name}, and I'm currently experiencing technical difficulties."
    
    return ACCEnhancedAgent


if __name__ == "__main__":
    print("This module provides ACC integration fixes for BaseAgent")
    print("Use enhance_agent_message_processing() or create_acc_enhanced_agent()")