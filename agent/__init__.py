import google.generativeai as genai
import json
import time
from config.logger import logger
from secret import gemini_api_keys

def handle_error(error, current_api_key_index):
    """Handle API errors and determine whether to retry or switch API keys
    
    Args:
        error: The error that occurred
        current_api_key_index: The index of the current API key
        
    Returns:
        int: The next index to try, or -1 if the error is not recoverable by switching keys,
             or -2 for unknown errors.
    """
    if isinstance(error, Exception):
        if "429 Too Many Requests" in str(error):
            logger.error(f"---GEMINI_API_KEY_{current_api_key_index + 1} limit exhausted, switching to the next API key...")
            # Return the next index to try
            return (current_api_key_index + 1) % len(gemini_api_keys)
        elif "503 Service Unavailable" in str(error):
            logger.error("Service is temporarily unavailable. Retrying after delay...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            # Return the current index to retry with the same key after delay
            return current_api_key_index
        else:
            logger.error(f"Unhandled error during API call: {str(error)}")
            # Indicate an error occurred that isn't related to key limits or temporary unavailability
            return -1
    else:
        logger.error(f"An unknown error occurred: {error}")
        # Indicate an unknown error
        return -2

async def run_agent(schema, prompt):
    """Run the AI agent to generate content based on the provided schema and prompt
    
    Args:
        schema: The schema defining the structure of the response
        prompt: The prompt to send to the AI model
        
    Returns:
        The generated content or an error message
    """
    current_api_key_index = 0
    max_retries = len(gemini_api_keys)  # Try each key once

    for attempt in range(max_retries):
        gemini_api_key = gemini_api_keys[current_api_key_index]

        if not gemini_api_key or gemini_api_key.startswith("API_KEY_"):  # Check for placeholder keys
            logger.warning(f"Skipping invalid or placeholder API key at index {current_api_key_index}")
            current_api_key_index = (current_api_key_index + 1) % len(gemini_api_keys)
            continue  # Try the next key

        logger.info(f"Attempting API call with key index {current_api_key_index}")
        
        # Configure the generative AI
        genai.configure(api_key=gemini_api_key)
        
        # Set up the model
        generation_config = {
            "response_mime_type": "application/json",
            "response_schema": schema,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )

        try:
            # Generate content
            response = await model.generate_content_async(prompt)

            if not response or not response.text:
                logger.warning(f"No response or empty response received from API with key index {current_api_key_index}.")
                # Try the next key if available, similar to 503
                next_index = handle_error(Exception("503 Service Unavailable"), current_api_key_index)
                if next_index == current_api_key_index:  # 503 retry indication
                    logger.info("Retrying with the same key after delay due to potential service issue.")
                    # The delay is handled within handle_error
                    continue  # Retry the loop with the same index
                elif next_index >= 0:
                    current_api_key_index = next_index
                    continue  # Try next key
                else:
                    logger.error("Failed to get a valid response and error handling did not provide a retry index.")
                    return "Service unavailable or failed after retries."

            # Parse the response
            response_text = response.text
            data = json.loads(response_text)
            logger.info(f"API call successful with key index {current_api_key_index}")
            return data  # Success

        except Exception as error:
            next_index = handle_error(error, current_api_key_index)

            if next_index >= 0 and next_index != current_api_key_index:
                # Rate limit (429) or other error indicating key switch
                current_api_key_index = next_index
                logger.info(f"Switching to API key index {current_api_key_index}")
            elif next_index == current_api_key_index:
                # Service unavailable (503), retry with the same key after delay
                logger.info(f"Retrying with API key index {current_api_key_index} after delay.")
                # Delay is handled in handle_error, continue loop to retry
            elif next_index == -1:
                # Unhandled error, stop retrying
                logger.error("Unhandled error occurred, stopping retries.")
                return f"An error occurred: {str(error)}"
            elif next_index == -2:
                # Unknown error, stop retrying
                logger.error("An unknown error occurred, stopping retries.")
                return "An unknown error occurred."

    logger.error("All API keys exhausted or failed.")
    return "Failed to generate response after trying all API keys."