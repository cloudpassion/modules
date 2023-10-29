from sanic.response import json

from .abstract import AbstractServer


class DefaultHandler(AbstractServer):

    async def load_default(self):
        app = self.app

        @app.route('__default__')
        async def default(request):
            return json({})
