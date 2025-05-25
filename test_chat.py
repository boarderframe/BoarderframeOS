#!/usr/bin/env python3
"""
Test client for Solomon chat interface
"""
import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_chat")

async def test_chat():
    """Test the chat interface"""
    uri = "ws://localhost:8889"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to Solomon chat server")
            
            # Send a test message
            test_message = {
                "type": "user_message",
                "message": "Hello Solomon! Can you hear me?"
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("Sent test message to Solomon")
            
            # Listen for responses for 10 seconds
            try:
                async with asyncio.timeout(10):
                    async for message in websocket:
                        data = json.loads(message)
                        logger.info(f"Received: {data}")
                        
                        if data.get("type") == "solomon_response":
                            logger.info(f"Solomon responded: {data.get('message')}")
                            break
                            
            except asyncio.TimeoutError:
                logger.info("No response from Solomon within 10 seconds")
                
    except Exception as e:
        logger.error(f"Chat test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())