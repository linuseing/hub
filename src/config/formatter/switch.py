from formatter import formatter


@formatter(bool, str, None)
def to_string(input: bool, on="on", off="off"):
    if input:
        return on
    return off
