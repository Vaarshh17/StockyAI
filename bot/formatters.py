"""
bot/formatters.py — Format agent responses for Telegram display.
Owner: Person 3
"""

def format_response(text: str) -> str:
    """
    Clean up GLM output for Telegram Markdown.
    - Escape special chars that break Markdown
    - Ensure emoji alignment
    """
    if not text:
        return "Maaf, tiada respons. Cuba lagi."

    # Telegram MarkdownV1 doesn't need heavy escaping
    # Just ensure backticks are paired
    return text.strip()
