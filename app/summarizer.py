import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
import os
from typing import Optional
from openai import OpenAI


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


def summarize_with_llm(
    content: str,
    custom_instructions: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Summarize content using an LLM (supports GitHub Models, Anthropic Claude, or OpenAI).

    Args:
        content: Text content to summarize
        custom_instructions: Optional custom instructions for summarization
        api_key: API key (falls back to env var)
        provider: LLM provider ('github', 'anthropic', 'openai')
        model: Model name to use

    Returns:
        Summary text
    """
    # Get provider and model from env if not specified
    if not provider:
        provider = os.getenv('LLM_PROVIDER', 'github')

    if not model:
        model = os.getenv('LLM_MODEL')

    default_instructions = (
        "Please provide a concise summary of the following content. "
        "Focus on the main points, key takeaways, and any important insights."
    )

    instructions = custom_instructions if custom_instructions else default_instructions

    # Truncate content if too long
    max_chars = 400000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[Content truncated due to length...]"

    prompt = f"{instructions}\n\nContent:\n\n{content}"

    if provider == 'github':
        # GitHub Models API (OpenAI-compatible)
        if not api_key:
            api_key = os.getenv('GITHUB_TOKEN')

        if not api_key:
            raise ValueError("GitHub token not provided")

        if not model:
            model = "gpt-4o"  # Default GitHub model

        client = OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=api_key
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes articles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.7
        )

        return response.choices[0].message.content

    elif provider == 'anthropic':
        # Anthropic Claude API
        if not api_key:
            api_key = os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            raise ValueError("Anthropic API key not provided")

        if not model:
            model = "claude-3-5-sonnet-20241022"

        client = Anthropic(api_key=api_key)

        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    elif provider == 'openai':
        # OpenAI API
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("OpenAI API key not provided")

        if not model:
            model = "gpt-4o"

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes articles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.7
        )

        return response.choices[0].message.content

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# Keep backwards compatibility
def summarize_with_claude(
    content: str,
    custom_instructions: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """Legacy function for backwards compatibility."""
    return summarize_with_llm(content, custom_instructions, api_key, provider='anthropic')
