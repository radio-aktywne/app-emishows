from litestar import Router

from emishows.api.routes.schedule.controller import Controller

router = Router(
    path="/schedule",
    route_handlers=[
        Controller,
    ],
)
