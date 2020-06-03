aiohttp_openapi
===============

.. image:: https://travis-ci.com/clayman083/aiohttp-openapi.svg?branch=master
    :target: https://travis-ci.com/clayman083/aiohttp-openapi

The library provides expose OpenAPI specification for `aiohttp.web`__-based applications.

.. _aiohttp_web: http://aiohttp.readthedocs.org/en/latest/web.html

__ aiohttp_web_


Installation
------------

    $ pip install https://github.com/clayman083/aiohttp-openapi.git


Usage
-----

The library allows us to expose OpenAPI specification,
which would be generated from application routes.


A trivial usage example:

.. code:: python

    from aiohttp import web
    from aiohttp_openapi import (
        JSONResponse,
        Parameter,
        ParameterIn,
        register_operation,
        RequestBody,
        setup as setup_openapi,
    )
    from marshmallow import fields, Schema


    class PayloadSchema(Schema):
        origin = fields.Str(description="Origin URL")
        disposable = fields.Bool(
            missing=False, description="Short URL should be disposable"
        )


    class ShortURLSchema(Schema):
        key = fields.Int(data_key="id", dump_only=True)
        url = fields.Str(description="Short URL")
        disposable = fields.Bool(default=False)
        created = fields.DateTime(
            dump_only=True,
            default=datetime.utcnow,
            doc_default="The current datetime",
        )


    class ResponseSchema(Schema):
        short_url = fields.Nested(ShortURLSchema, data_key="shortURL")


    RequestIDParameter = Parameter(
        in_=ParameterIn.header,
        name="X-Request-ID",
        schema={"type": "string", "format": "uuid"},
        required=True,
    )


    @register_operation(
        description="Add new short URL",
        parameters=(RequestIDParameter,),
        request_body=RequestBody(
            description="Add short URL for origin", schema=PayloadSchema
        ),
        responses=(
            JSONResponse(
                description="New short URL added",
                schema=ResponseSchema,
                status_code=201,
            ),
        ),
    )
    async def handler(request):
        return web.Response(text='Hello world')


    def make_app():
        app = web.Application()

        app.router.add_get('/', handler)

        setup_openapi(
            app,
            title="Shortner",
            version="0.1.0",
            description="Shortner service API",
        )

        return app

    web.run_app(make_app())


Now you can access your specification on `/api/spec.json` endpoint.


Developing
----------

Install for local development::

    $ poetry install

Run tests with::

    $ tox


License
-------

``aiohttp_openapi`` is offered under the MIT license.
