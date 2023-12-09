from litestar import Router

from emishows.api.routes.shows.controller import Controller

router = Router(
    path="/shows",
    route_handlers=[
        Controller,
    ],
)
