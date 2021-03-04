from formatter import formatter


@formatter
def to_string(input):
    if input:
        return 'on'
    return 'off'

