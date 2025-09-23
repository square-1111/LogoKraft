import asyncio
import json
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

router = APIRouter(prefix="/api/v1", tags=["streaming"])

async def generate_test_events() -> AsyncGenerator[str, None]:
    """Generate test SSE events every 2 seconds"""
    counter = 0
    while True:
        counter += 1
        timestamp = datetime.now().isoformat()
        
        # Create SSE formatted message
        data = {
            "event": "test_message",
            "counter": counter,
            "timestamp": timestamp,
            "message": f"Hello from LogoKraft backend! Message #{counter}"
        }
        
        # SSE format: data: {json}\n\n
        yield f"data: {json.dumps(data)}\n\n"
        
        # Wait 2 seconds before next message
        await asyncio.sleep(2)

@router.get("/stream-test")
async def stream_test():
    """
    SSE Test endpoint for Milestone 1: The Smoke Test
    
    This endpoint proves our real-time communication works by sending
    timestamp messages every 2 seconds via Server-Sent Events.
    
    Test with:
    - Browser: Navigate to http://localhost:8000/api/v1/stream-test
    - JavaScript: EventSource API
    - curl: curl -N http://localhost:8000/api/v1/stream-test
    """
    return StreamingResponse(
        generate_test_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )