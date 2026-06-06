# Copyright 2026 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import asyncio
import datetime
import logging
import os
import tempfile
import sys

from fastmcp import FastMCP
from fastmcp.utilities import logging as fastmcp_logger

from colab_mcp.session import ColabSessionProxy


mcp = FastMCP(name="ColabMCP")


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def init_logger(logdir):
    log_filename = datetime.datetime.now().strftime(
        f"{logdir}/colab-mcp.%Y-%m-%d_%H-%M-%S.log"
    )
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        filename=log_filename,
        level=logging.INFO,  # Set the minimum logging level to capture
    )
    fastmcp_logger.get_logger("colab-mcp").info("logging to %s" % log_filename)


def parse_args(v):
    parser = argparse.ArgumentParser(
        description="ColabMCP is an MCP server that lets you interact with Colab."
    )
    parser.add_argument(
        "-l",
        "--log",
        help="if set, use this directory as a location for logfiles (if unset, will log to %s/colab-mcp-logs/)"
        % tempfile.gettempdir(),
        action="store",
        default=tempfile.mkdtemp(prefix="colab-mcp-logs-"),
    )
    parser.add_argument(
        "-p",
        "--enable-proxy",
        help="if set, enable the runtime proxy (enabled by default).",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--browser-command",
        help=(
            "browser executable or command used for controlled Colab launch. "
            "Overrides COLAB_MCP_BROWSER_COMMAND."
        ),
        default=None,
    )
    parser.add_argument(
        "--browser-profile",
        help=(
            "Chrome/Chromium profile directory name, for example 'Default'. "
            "Overrides COLAB_MCP_BROWSER_PROFILE."
        ),
        default=None,
    )
    parser.add_argument(
        "--browser-user-data-dir",
        help=(
            "browser user data directory, for example ~/.config/google-chrome. "
            "Overrides COLAB_MCP_BROWSER_USER_DATA_DIR."
        ),
        default=None,
    )
    parser.add_argument(
        "--connection-timeout",
        help=(
            "seconds to wait for the Colab frontend MCP connection. "
            "Overrides COLAB_MCP_CONNECTION_TIMEOUT."
        ),
        type=positive_float,
        default=None,
    )
    parser.add_argument(
        "--print-connection-url",
        help="write the generated Colab connection URL to stderr when launching the browser.",
        action="store_true",
        default=False,
    )
    return parser.parse_args(v)


def apply_browser_args(args):
    env_updates = {
        "COLAB_MCP_BROWSER_COMMAND": args.browser_command,
        "COLAB_MCP_BROWSER_PROFILE": args.browser_profile,
        "COLAB_MCP_BROWSER_USER_DATA_DIR": args.browser_user_data_dir,
        "COLAB_MCP_CONNECTION_TIMEOUT": (
            str(args.connection_timeout) if args.connection_timeout is not None else None
        ),
        "COLAB_MCP_PRINT_CONNECTION_URL": "1"
        if args.print_connection_url
        else None,
    }
    for name, value in env_updates.items():
        if value is not None:
            os.environ[name] = value


async def main_async():
    args = parse_args(sys.argv[1:])
    apply_browser_args(args)
    init_logger(args.log)

    if args.enable_proxy:
        logging.info("enabling session proxy tools")
        session_mcp = ColabSessionProxy()
        await session_mcp.start_proxy_server()
        mcp.mount(session_mcp.proxy_server)
        for middleware in session_mcp.middleware:
            mcp.add_middleware(middleware)

    try:
        await mcp.run_async()

    finally:
        if args.enable_proxy:
            await session_mcp.cleanup()


def main() -> None:
    asyncio.run(main_async())
