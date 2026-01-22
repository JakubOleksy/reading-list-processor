import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
import os
from typing import Optional


def fetch_webpage_content(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch and extract text content from a webpage.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Extracted text content or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def summarize_with_claude(
    content: str,
    custom_instructions: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Summarize content using Claude API.

    Args:
        content: Text content to summarize
        custom_instructions: Optional custom instructions for summarization
        api_key: Anthropic API key (falls back to env var)

    Returns:
        Summary text
    """
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        raise ValueError("Anthropic API key not provided")

    client = Anthropic(api_key=api_key)

    default_instructions = (
        "Please provide a concise summary of the following content. "
        "Focus on the main points, key takeaways, and any important insights."
    )

    instructions = custom_instructions if custom_instructions else default_instructions

    # Truncate content if too long (approx 100k tokens max)
    max_chars = 400000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[Content truncated due to length...]"

    prompt = f"{instructions}\n\nContent:\n\n{content}"

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text
