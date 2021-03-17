from formatter import formatter


@formatter(bool, str, None)
def to_string(input: bool):
    if input:
        return 'on'
    return 'off'

