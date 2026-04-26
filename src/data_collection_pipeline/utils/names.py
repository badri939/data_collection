def split_full_name(full_name: str) -> tuple[str, str]:
    """Splits a full name into first name and last name.
    
    Args:
        full_name (str): The full name to split.

    Returns:
        tuple[str, str]: A tuple containing the first name and last name.
    """
    if not full_name or not full_name.strip():
        return "", ""
    parts = full_name.split()
    
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])