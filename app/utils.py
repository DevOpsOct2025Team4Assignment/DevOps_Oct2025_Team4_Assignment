def format_size(size_bytes: int) -> str:
    """Format file size in bytes to a human-readable string."""
    if size_bytes == 0:
        return "0 B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    size = float(size_bytes)

    while size >= 1000 and i < len(size_name) - 1:
        size /= 1000
        i += 1

    return f"{size:.2f} {size_name[i]}"
