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
import string


Toc = Dict[str, Union["Toc", str]]


def foo(input_directory: Path, src: Union[str, Toc], extensions: Dict[str, fnl.e.Entity]):
    if isinstance(src, str):
        path = input_directory / Path(src)
        source = path.read_text("utf-8", "space_it")
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


def generate_head_extras(extra_js: List[str], extra_css: List[str]):
    rv = ""
    for extra in extra_js:
        rv += f'<script src="{extra}"></script>\n'
    for extra in extra_css:
        rv += f'<link rel="stylesheet" href="{extra}"/>\n'
    return rv


def build(config_path: str):
    with open(config_path, encoding="utf-8") as config_file:
        config = json.load(config_file)

    if "template_directory" in config:
        template_directory = Path(config["template_directory"])
    else:
        template_directory = Path(__file__).parent/"template"
    input_directory = Path(config["input_directory"])
    output_directory = Path(config["output_directory"])
    shutil.copytree(template_directory, output_directory, dirs_exist_ok=True)


    index_path = template_directory / "index.html"
    extra_css: List[str] = config.get("extra_css", [])
    extra_js: List[str] = config.get("extra_js", [])
    for extra in extra_css + extra_js:
        shutil.copy(input_directory / extra, output_directory / extra)

    final_index_page = string.Template(index_path.read_text("utf-8", "space_it")).substitute({
        "title": config.get("title", "Documentation"),
        "head_extras": generate_head_extras(extra_js, extra_css)
    })
    (output_directory / "index.html").write_text(final_index_page, "utf-8", "space_it")

    config.get("title", "")

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
        onPageSwitch: [], // (newPageTitle: string) => void
    }};
    """)
    (output_directory / Path("data.js")).write_text(js_code, "utf-8", "space_it")


if sys.argv[1:2] == ["serve"] and len(sys.argv) == 3:
    config_path = sys.argv[2]

    with open(config_path, encoding="utf-8") as config_file:
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

    @routes.get("/")
    async def on_root_redirect_to_index(req: web.Request) -> web.StreamResponse:
        raise web.HTTPFound(location="index.html")

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
