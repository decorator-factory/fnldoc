import asyncio
from textwrap import dedent
from traceback import print_exc
from typing import Callable, Dict, TypeVar, Union
import fnl
from pathlib import Path
import json
import sys
import watchgod
import shutil
from aiohttp import web


Toc = Dict[str, Union["Toc", str]]


def foo(input_directory: Path, src: Union[str, Toc]):
    if isinstance(src, str):
        path = input_directory / Path(src)
        source = path.read_text()
        html = fnl.html(source)
        return html
    else:
        result = {}
        for name, subtoc in src.items():
            result[name] = foo(input_directory, subtoc)
        return result


Node = Dict[str, Union[str, "Node"]]


def render_toc(input_directory: Path, src: Toc) -> Node:
    return foo(input_directory, src)  # type: ignore


def build(config_path: str):
    with open(config_path) as config_file:
        config = json.load(config_file)

    template_directory = Path(config["template_directory"])
    input_directory = Path(config["input_directory"])
    output_directory = Path(config["output_directory"])
    shutil.copytree(template_directory, output_directory, dirs_exist_ok=True)

    compiled_html = render_toc(input_directory, config["toc"])
    js_code = dedent(f"""
    window.fnl = {{
        start: {json.dumps(config["start"])},
        source: {json.dumps(config["toc"])},
        compiledHtml: {json.dumps(compiled_html)},
    }};
    """)
    (output_directory / Path("data.js")).write_text(js_code)


if sys.argv[1:2] == ["serve"] and len(sys.argv) == 3:
    config_path = sys.argv[2]

    with open(config_path) as config_file:
        config = json.load(config_file)

    build(config_path)

    async def watch(path):
        async for updates in watchgod.awatch(path):
            print("Updates:", updates)
            try:
                build(config_path)
            except BaseException as e:
                print_exc(limit=4)

    async def watcher(app: web.Application):
        asyncio.create_task(watch("fnldoc.json"))
        asyncio.create_task(watch(config["input_directory"]))
        asyncio.create_task(watch(config["template_directory"]))

    routes = web.RouteTableDef()

    routes.static('/', config["output_directory"])

    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(watcher)

    web.run_app(app)
elif sys.argv[1:2] == ["serve"] and len(sys.argv) == 3:
    config_path = sys.argv[2]
    build(config_path)
else:
    print("Unknown invocation mode. Valid modes:")
    print("python -m fnldoc build <config_file>")
    print("python -m fnldoc serve <config_file>")
    sys.exit(1)
