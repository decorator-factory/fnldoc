import fnl
import markdown

__extension__ = {}


@fnl.definitions.fn(__extension__, "md")
def md():
    def _md(string: fnl.e.String):
        html = markdown.markdown(string.value)
        if html == "":
            return fnl.e.BlockTag("p", "", ())
        else:
            return fnl.e.BlockRaw(html)
    yield ("(λ str . block)", _md)
