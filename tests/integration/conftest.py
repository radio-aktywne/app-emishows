from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, BasicAuth
from litestar import Litestar
from litestar.testing import AsyncTestClient
from prisma import Prisma

from emishows.api.app import AppBuilder
from emishows.config.builder import ConfigBuilder
from emishows.config.models import Config
from tests.utils.containers import AsyncDockerContainer
from tests.utils.waiting.conditions import CallableCondition
from tests.utils.waiting.strategies import TimeoutStrategy
from tests.utils.waiting.waiter import Waiter


@pytest.fixture(scope="session")
def config() -> Config:
    """Loaded configuration."""

    return ConfigBuilder().build()


@pytest.fixture(scope="session")
def app(config: Config) -> Litestar:
    """Reusable application."""

    return AppBuilder(config).build()


@pytest_asyncio.fixture(scope="session")
async def datashows() -> AsyncGenerator[AsyncDockerContainer]:
    """Datashows container."""

    async def _check() -> None:
        async with Prisma(
            datasource={
                "url": "postgres://user:password@localhost:34000/database",
            }
        ):
            return

    container = AsyncDockerContainer(
        "ghcr.io/radio-aktywne/databases/datashows:latest",
        network="host",
        privileged=True,
    )

    waiter = Waiter(
        condition=CallableCondition(_check),
        strategy=TimeoutStrategy(30),
    )

    async with container as container:
        await waiter.wait()
        yield container


@pytest_asyncio.fixture(scope="session")
async def datatimes() -> AsyncGenerator[AsyncDockerContainer]:
    """Datatimes container."""

    async def _check() -> None:
        auth = BasicAuth(username="user", password="password")
        client = AsyncClient(
            base_url="http://localhost:36000",
            auth=auth,
        )
        async with client as client:
            response = await client.get("/user/datatimes")
            response.raise_for_status()

    container = AsyncDockerContainer(
        "ghcr.io/radio-aktywne/databases/datatimes:latest",
        network="host",
    )

    waiter = Waiter(
        condition=CallableCondition(_check),
        strategy=TimeoutStrategy(30),
    )

    async with container as container:
        await waiter.wait()
        yield container


@pytest_asyncio.fixture(scope="session")
async def client(
    app: Litestar, datashows: AsyncDockerContainer, datatimes: AsyncDockerContainer
) -> AsyncGenerator[AsyncTestClient]:
    """Reusable test client."""

    async with AsyncTestClient(app=app) as client:
        yield client
