import re
import fnl

__extension__ = {}


def _perform_interpolation(source: str):
    last_pos = -1
    for match in re.finditer(r"@\(((?:[^)]|\)[^@])+)\)@", source):
        start = match.start()
        if start > last_pos + 1:
            yield fnl.e.String(source[last_pos + 1:start])
        yield fnl.parse("(" + match[1] + ")")
        last_pos = start + len(match[0]) - 1
    yield fnl.e.String(source[last_pos + 1:])


@fnl.definitions.fn(__extension__, "$$")
def interpolate():
    def _interpolate(string: fnl.e.String):
        return fnl.e.InlineConcat(tuple(_perform_interpolation(string.value)))
    yield ("(λ str . inline)", _interpolate)

@fnl.definitions.fn(__extension__, "$p")
def interpolate_para():
    def _interpolate_para(string: fnl.e.String):
        return fnl.e.BlockTag("p", "", tuple(_perform_interpolation(string.value)))
    yield ("(λ str . block)", _interpolate_para)
