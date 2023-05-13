import asyncio


class MyHttpDefault:

    simulate: bool
    simulate_code: int
    simulate_response: str
    simulate_content_type: str
    sem: asyncio.Semaphore
