"""
ACC Response Handler
Ensures agents properly respond to ACC messages
"""

import asyncio
from typing import List, Optional
from .message_bus import AgentMessage, MessageType, message_bus


class ACCResponseHandler:
    """Handles ACC message responses for agents"""
    
    @staticmethod
    async def setup_acc_response_handling(agent):
        """Setup ACC response handling for an agent"""
        agent.log("🔧 Setting up ACC response handling")
        
        # Store original process messages method
        original_process = agent._process_messages
        
        async def process_with_acc_response(messages: List[AgentMessage]):
            """Enhanced message processing with ACC responses"""
            for message in messages:
                try:
                    # Check if this is an ACC user chat request
                    if (message.message_type == MessageType.TASK_REQUEST and
                        message.content.get("type") == "user_chat" and
                        message.requires_response and
                        message.correlation_id):
                        
                        user_msg = message.content.get("message", "")
                        agent.log(f"💬 ACC Chat Request: '{user_msg}' (from: {message.from_agent}, id: {message.correlation_id})")
                        
                        # Handle the chat
                        response_text = None
                        if hasattr(agent, 'handle_user_chat'):
                            try:
                                response_text = await agent.handle_user_chat(user_msg)
                            except Exception as e:
                                agent.log(f"❌ Error in handle_user_chat: {e}", level="error")
                                response_text = f"I apologize, but I encountered an error: {str(e)}"
                        else:
                            response_text = f"Hello! I'm {agent.config.name}. I received your message but don't have a chat handler yet."
                        
                        # Send response back to ACC
                        response_msg = AgentMessage(
                            from_agent=agent.config.name,
                            to_agent="acc_system",
                            message_type=MessageType.TASK_RESPONSE,
                            content={
                                "response": response_text,
                                "original_message": user_msg
                            },
                            correlation_id=message.correlation_id,
                            requires_response=False
                        )
                        
                        agent.log(f"📤 Sending response to ACC: '{response_text[:50]}...'")
                        success = await message_bus.send_message(response_msg)
                        
                        if success:
                            agent.log(f"✅ Response sent to ACC (correlation_id: {message.correlation_id})")
                        else:
                            agent.log("❌ Failed to send response to ACC", level="error")
                    
                    else:
                        # Process other messages normally
                        await original_process([message])
                        
                except Exception as e:
                    agent.log(f"❌ Error processing ACC message: {e}", level="error")
                    import traceback
                    traceback.print_exc()
        
        # Replace the process messages method
        agent._process_messages = process_with_acc_response
        agent.log("✅ ACC response handling enabled")
        
        return True


def enable_acc_responses(agent_class):
    """Decorator to enable ACC responses on an agent class"""
    
    original_init = agent_class.__init__
    
    def new_init(self, *args, **kwargs):
        # Call original init
        original_init(self, *args, **kwargs)
        
        # Schedule ACC setup after agent is initialized
        async def setup():
            await asyncio.sleep(0.1)  # Let agent fully initialize
            await ACCResponseHandler.setup_acc_response_handling(self)
        
        asyncio.create_task(setup())
    
    agent_class.__init__ = new_init
    return agent_class