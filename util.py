def validate_fraction(string):
    parts = string.split('/')
    if len(parts) != 2:
        raise ValueError('Invalid fraction format')

    try:
        amount = int(parts[0])
        limit = int(parts[1])
    except ValueError:
        raise ValueError('Invalid fraction format')

    if limit >= amount:
        raise ValueError('Limit should be smaller than amount')

    return amount, limit
