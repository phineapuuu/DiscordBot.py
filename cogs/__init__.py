from glob import iglob
from os import path


def get_extensions(*, disabled=()):
    extensions_list = []
    for filepath in iglob(path.join(path.dirname(__file__), '*.py')):
        filename = path.basename(filepath)
        if not filename.startswith('_'):
            extension_name = filename[:-3]
            if extension_name not in disabled:
                extensions_list.append(extension_name)
    return sorted(extensions_list)
