import requests


def get_last_version():
    last_release: str = list(
        requests.get(
            url='https://pypi.org/pypi/async-icq/json'
        ).json().get(
            'releases'
        ).keys())[-1]

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
