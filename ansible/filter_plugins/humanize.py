def human_readable_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

class FilterModule(object):
    def filters(self):
        return {
            'human_readable': human_readable_bytes
        }
