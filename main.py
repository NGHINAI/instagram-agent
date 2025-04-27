import asyncio
import os
from config.logger import logger
from client.instagram import run_instagram
from utils import setup_handle_error

# Ensure the cookies directory exists
os.makedirs('./cookies', exist_ok=True)

async def run_agents():
    """
    Main function to run all social media agents
    Currently only Instagram is implemented
    """
    try:
        logger.info("Starting Instagram agent...")
        await run_instagram()
        logger.info("Instagram agent finished.")
        
        # Future implementations for other social media platforms
        # logger.info("Starting Twitter agent...")
        # await run_twitter()
        # logger.info("Twitter agent finished.")
        
        # logger.info("Starting GitHub agent...")
        # await run_github()
        # logger.info("GitHub agent finished.")
        
    except Exception as error:
        setup_handle_error(error, "Error running agents")

if __name__ == "__main__":
    asyncio.run(run_agents())