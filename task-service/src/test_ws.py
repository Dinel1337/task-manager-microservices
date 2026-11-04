import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/api/v1/ws/tasks?user_id=testuser"
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri) as ws:
        print("✅ Connected! Waiting for messages...")
        
        # Ждем сообщения (например, 10 секунд)
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=10.0)
            print(f"📩 Received: {message}")
        except asyncio.TimeoutError:
            print("⏰ Timeout: No message received in 10s")

if __name__ == "__main__":
    asyncio.run(test_ws())