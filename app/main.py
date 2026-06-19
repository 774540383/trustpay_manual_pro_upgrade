import asyncio, uvicorn
from .db import init_db
from .bots import run_bots
from .admin import app

async def run_web():
    config=uvicorn.Config(app, host='0.0.0.0', port=8000, log_level='info')
    server=uvicorn.Server(config)
    await server.serve()

async def main():
    init_db()
    await asyncio.gather(run_web(), run_bots())

if __name__=='__main__':
    asyncio.run(main())
