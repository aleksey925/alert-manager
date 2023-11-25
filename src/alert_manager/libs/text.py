def truncate(text: str, max_length: int) -> str:
    if len(text) > max_length:
        return text[: max_length - 3] + '...'
    return text
