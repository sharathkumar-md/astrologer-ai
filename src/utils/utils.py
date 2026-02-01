def sanitize_role(role):
    if role in ['astrologer', 'astra', 'bot']:
        return 'assistant'
    return role if role in ['system', 'assistant', 'user', 'function', 'tool', 'developer'] else 'user'
