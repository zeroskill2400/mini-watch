import re


def find_urls(text):
    if not isinstance(text, str):
        return []
    return list(dict.fromkeys(value.rstrip('.,;:!?') for value in re.findall(r'https?://[^\s<>"\'()\[\]{}]+', text)))
