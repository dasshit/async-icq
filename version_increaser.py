import json
import urllib.request


def get_last_version():

    request = urllib.request.urlopen(
        "https://pypi.org/pypi/async-icq/json").read()

    last_release = list(
        json.loads(request).get('releases').keys())[-1]

    return [int(i) for i in last_release.split('.')]


def auto_version_increase():

    major, middle, minor = get_last_version()

    if minor < 10:
        return f'{major}.{middle}.{minor + 1}'
    else:
        minor = 0
        if middle < 10:
            return f'{major}.{middle + 1}.{minor}'
        else:
            middle = 0
            return f'{major + 1}.{middle}.{minor}'
