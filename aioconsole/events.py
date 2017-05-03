"""Provide an interactive event loop class."""

import asyncio
import functools

from . import code
from . import compat
from . import server

@asyncio.coroutine
def interactive_console(loop, locals=None, banner=None, serve=None, console_class=code.AsynchronousConsole):
    # Local console
    if serve is None:
        console = console_class(None, locals=locals, loop=loop)
        yield from console.interact(banner, stop=True, handle_sigint=True)
    # Serving console
    else:
        host, port = serve
        try:
            factory = lambda streams: console_class(streams, locals=locals, loop=loop)
            console_server = yield from server.start_interactive_server(
                factory, host=host, port=port, banner=banner, loop=loop)
            server.print_server(console_server)
        except:
            pass

class InteractiveEventLoopPolicy(asyncio.AbstractEventLoopPolicy):
    """Policy to use the interactive event loop by default."""

    def __init__(self, serve=None, oldpolicy=None):
        assert oldpolicy is not None
        self.serve = serve
        self.oldpolicy = oldpolicy
        super().__init__()

    def get_event_loop(self):
        return self.oldpolicy.get_event_loop()

    def set_event_loop(self, loop):
        self.oldpolicy.set_event_loop(loop)

    def new_event_loop(self):
        loop = self.oldpolicy.new_event_loop()
        loop.create_task(interactive_console(loop, locals=None, banner=None, serve=self.serve))
        return loop


def set_interactive_policy(serve=None):
    """Use an interactive event loop by default."""
    asyncio.set_event_loop_policy(InteractiveEventLoopPolicy(serve, asyncio.get_event_loop_policy()))


def run_console(selector=None, locals=None, banner=None, serve=None):
    """Run the interactive event loop."""
    loop = asyncio.get_event_loop()
    console_task = loop.create_task(interactive_console(loop, locals, banner, serve))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
