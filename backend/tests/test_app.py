from fastapi import FastAPI

from app.main import app


def test_app_initializes():
    assert isinstance(app, FastAPI)
    assert app.title == "FuturePath AI Backend"


def test_openapi_schema_generates():
    schema = app.openapi()
    assert schema["openapi"]
    assert "/api/v1/health" in schema["paths"]
