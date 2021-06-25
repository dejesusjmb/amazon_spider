import re
import types
from collections import Iterator


def compress(clean):
    """
    Trims leading and trailing whitespace
    Also compresses multiple spaces within a string
    """
    if clean is None:
        return None
    clean = re.sub(r'[\r\n\t\xa0]', ' ', clean)
    clean = re.sub(r'&nbsp;?', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def recursive_compress(data, empty_string_as_none=False,
                       remove_empty_keys=True):
    '''
    Recursive compress function
    Accepts an object an tries to compress every sub-data if it is a string
    empty_string_as_none is a flag to replace empty string with None value
    '''
    kwargs = {
        'empty_string_as_none': empty_string_as_none,
        'remove_empty_keys': remove_empty_keys
    }
    if isinstance(data, dict):
        if remove_empty_keys:
            return {compress(k): recursive_compress(v, **kwargs)
                    for k, v in data.items() if k}
        else:
            return {compress(k) if k else k: recursive_compress(v, **kwargs)
                    for k, v in data.items()}
    elif isinstance(data, list):
        return [recursive_compress(x, **kwargs) for x in data]
    elif isinstance(data, types.GeneratorType) or isinstance(data, Iterator):
        return (recursive_compress(x, **kwargs) for x in data)
    elif isinstance(data, str):
        compressed_data = compress(data)
        if empty_string_as_none and not compressed_data:
            compressed_data = None
        return compressed_data
    else:
        return data
