from enum import Enum
from functools import wraps
from typing import Dict, Iterable, Optional

import attr
import ujson
from aiohttp import web
from apispec import APISpec  # type: ignore
from apispec.ext.marshmallow import MarshmallowPlugin  # type: ignore
from apispec.utils import validate_spec  # type: ignore
from apispec.yaml_utils import load_yaml_from_docstring  # type: ignore
from marshmallow import Schema


class ParameterIn(Enum):
    cookies = "cookies"
    header = "header"
    query = "query"


@attr.dataclass(slots=True, kw_only=True)
class Parameter:
    name: str
    schema: Dict[str, str]
    in_: ParameterIn = ParameterIn.query
    required: bool = False


@attr.dataclass(slots=True, kw_only=True)
class RequestBody:
    description: str
    schema: Schema
    required: bool = False


@attr.dataclass(slots=True, kw_only=True)
class Response:
    description: str
    content_type: str
    status_code: int = 200


@attr.dataclass(slots=True, kw_only=True)
class JSONResponse(Response):
    schema: Schema
    content_type: str = "application/json"


Responses = Iterable[Response]


def register_operation(
    description: str,
    responses: Responses,
    parameters: Optional[Iterable[Parameter]] = None,
    request_body: Optional[RequestBody] = None,
):
    def wrapper(f):
        if not hasattr(f, "spec"):
            f.spec = {
                "operation": {"description": description, "responses": {}}
            }

        operation_from_doc = load_yaml_from_docstring(f.__doc__)

        if operation_from_doc:
            f.spec["operation"] = operation_from_doc

        if description:
            f.spec["operation"]["description"] = description

        if request_body:
            f.spec["operation"]["requestBody"] = {
                "description": request_body.description,
                "content": {
                    "application/json": {"schema": request_body.schema}
                },
            }
            if request_body.required:
                f.spec["operation"]["requestBody"]["required"] = True

        if parameters:
            f.spec["operation"]["parameters"] = [
                {
                    "in": parameter.in_.value,
                    "name": parameter.name,
                    "schema": parameter.schema,
                    "required": parameter.required,
                }
                for parameter in parameters
            ]

        for response in responses:
            f.spec["operation"]["responses"][str(response.status_code)] = {
                "description": response.description,
                "content": {response.content_type: {"schema": response.schema}},
            }

        @wraps(f)
        async def wrapped(*args, **kwargs):
            return await f(*args, **kwargs)

        return wrapped

    return wrapper


async def handler(request: web.Request) -> web.Response:
    """
    Expose API specification to the world
    """

    return web.json_response(request.app["spec"].to_dict(), dumps=ujson.dumps)


def setup(
    app: web.Application,
    *,
    title: str,
    version: str,
    description: str,
    openapi_version: str = "3.0.2",
    path: str = "/api/spec.json",
) -> None:

    app["spec"] = APISpec(
        title=title,
        version=version,
        openapi_version=openapi_version,
        info={"description": description},
        plugins=[MarshmallowPlugin()],
    )

    app.router.add_get(path, handler, name="api.spec")

    for route in app.router.routes():
        if hasattr(route.handler, "spec") and route.resource:
            operation_spec = route.handler.spec["operation"]  # type: ignore
            app["spec"].path(
                path=route.resource.canonical,
                operations={route.method.lower(): operation_spec},
            )

    validate_spec(app["spec"])
