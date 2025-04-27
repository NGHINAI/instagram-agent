# Instagram Bot

This is a Python implementation of an Instagram automation bot that can interact with posts by liking and commenting using AI-generated content. The bot leverages Google's Gemini AI to generate context-aware comments and provides robust automation capabilities for Instagram engagement.

## Key Benefits
- Automated engagement with target audiences
- AI-powered comment generation for authentic interactions
- Session persistence with cookie management
- Multi-account support with API key rotation
- Comprehensive logging and error handling

## Features

- Automated login to Instagram (with support for 2FA)
- Cookie management for persistent sessions
- Automated interaction with Instagram posts
  - Liking posts
  - Commenting on posts with AI-generated content
- Random user-agent rotation
- Error handling and logging

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- Instagram account credentials
- Gemini API key(s) for AI comment generation

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables in the `.env` file:

```
IG_USERNAME=your_instagram_username
IG_PASSWORD=your_instagram_password
GEMINI_API_KEY_1=your_gemini_api_key
# Add more API keys if needed
# GEMINI_API_KEY_2=your_second_gemini_api_key
```

## Usage

Run the bot using the following command:

```bash
python main.py
```

The bot will:
1. Log in to Instagram (using cookies if available, or credentials if not)
2. Navigate to the Instagram homepage
3. Interact with posts by liking and commenting
4. Close the browser when finished

## Project Structure

```
instagram_bot/
├── agent/              # AI agent implementation
│   ├── __init__.py    # Main agent functionality
│   └── schema/        # Schema definitions for AI responses
├── client/            # Social media client implementations
│   └── instagram.py   # Instagram automation implementation
├── config/            # Configuration files
│   └── logger.py      # Logging configuration
├── cookies/           # Directory for storing cookies
├── data/              # Directory for storing data
├── utils/             # Utility functions
│   └── __init__.py    # Cookie management and other utilities
├── .env               # Environment variables
├── main.py            # Main entry point
├── requirements.txt   # Python dependencies
├── secret.py          # Credentials and API keys
└── README.md          # This file
```

## Customization

You can customize the bot's behavior by modifying the following parameters in `client/instagram.py`:

- `max_posts`: Maximum number of posts to interact with (default: 50)
- Chrome options: Uncomment the headless mode option for running without UI
- User agents: Add or modify the list of user agents

## Notes

- The bot includes random delays between actions to avoid detection
- Cookies are saved after successful login for future sessions
- The bot handles 2FA authentication if enabled on your account
- Error handling is implemented to gracefully handle exceptions

## Future Enhancements

- Support for other social media platforms (Twitter, GitHub, etc.)
- More sophisticated interaction patterns
- Advanced AI-generated content