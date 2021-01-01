import asyncio
import importlib
from textwrap import dedent
from traceback import print_exc
from typing import Dict, List, Tuple, Union
import fnl
from pathlib import Path
import json
import sys
import watchgod
import shutil
from aiohttp import web
from functools import reduce


Toc = Dict[str, Union["Toc", str]]


def foo(input_directory: Path, src: Union[str, Toc], extensions: Dict[str, fnl.e.Entity]):
    if isinstance(src, str):
        path = input_directory / Path(src)
        source = path.read_text()
        html = fnl.html(source, extensions)
        return html
    else:
        return {
            name: foo(input_directory, subtoc, extensions)
            for name, subtoc in src.items()
        }


Node = Dict[str, Union[str, "Node"]]


def render_toc(input_directory: Path, src: Toc, extensions: Dict[str, fnl.e.Entity]) -> Node:
    return foo(input_directory, src, extensions)  # type: ignore


def get_extension(path: str, name: str) -> Dict[str, fnl.e.Entity]:
    module = importlib.import_module(path)
    entities = getattr(module, name)
    if not isinstance(entities, dict):
        raise TypeError(f"{path}.{name} is not a dictionary, it's: {entities!r}")
    for k, v in entities.items():
        if not isinstance(k, str):
            raise TypeError(f"{path}.{name}'s key {k!r} is not a string")
        if not isinstance(entities, dict):
            raise TypeError(f"{path}.{name}[{k!r}] is not a dictionary, it's: {v!r}")
    return entities


def build(config_path: str):
    with open(config_path) as config_file:
        config = json.load(config_file)

    if "template_directory" in config:
        template_directory = Path(config["template_directory"])
    else:
        template_directory = Path(__file__).parent/"template"
    input_directory = Path(config["input_directory"])
    output_directory = Path(config["output_directory"])
    shutil.copytree(template_directory, output_directory, dirs_exist_ok=True)

    extensions = reduce(
        lambda acc, ext: {**acc, **get_extension(ext[0], ext[1])},
        config.get("extensions", []),
        {}
    )

    compiled_html = render_toc(input_directory, config["toc"], extensions)
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
    if "template_directory" in config:
        template_directory = Path(config["template_directory"])
    else:
        template_directory = Path(__file__).parent/"template"

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
        asyncio.create_task(watch(template_directory))

    routes = web.RouteTableDef()

    routes.static('/', config["output_directory"])

    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(watcher)

    web.run_app(app)
elif sys.argv[1:2] == ["build"] and len(sys.argv) == 3:
    config_path = sys.argv[2]
    build(config_path)
else:
    print("Unknown invocation mode. Valid modes:")
    print("python -m fnldoc build <config_file>")
    print("python -m fnldoc serve <config_file>")
    sys.exit(1)
