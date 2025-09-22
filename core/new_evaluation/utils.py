def normalize_stage_key(name: str) -> str:
    """Normalize stage identifier by stripping a trailing '_stage' once.

    Examples:
        'setup_stage' -> 'setup'
        'backswing' -> 'backswing'
    """
    if not isinstance(name, str):
        return name
    if name.endswith('_stage'):
        return name[:-6]
    return name

__all__ = ['normalize_stage_key']
