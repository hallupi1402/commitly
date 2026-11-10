from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from commitly.config import config_dir as default_config_dir, resolve_workspace, state_dir as default_state_dir
from commitly.api.routes import router


def create_app(workspace: Path | None = None, config_dir: Path | None = None, state_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Commitly Local API", version="1.0.0")
    app.state.workspace = resolve_workspace(workspace)
    app.state.config_dir = config_dir or default_config_dir()
    app.state.state_dir = state_dir or default_state_dir()

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        details = [{"location": error.get("loc", []), "message": error.get("msg", "Invalid value")} for error in exc.errors()]
        return JSONResponse(status_code=422, content={"code": "validation_error", "message": "Check the highlighted request fields and try again.", "details": {"errors": details}})

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        return JSONResponse(status_code=exc.status_code, content={"code": "request_failed", "message": message, "details": {}})

    @app.middleware("http")
    async def loopback_write_guard(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            host = (request.url.hostname or "").lower()
            if host not in {"localhost", "127.0.0.1", "::1", "testserver"}:
                return JSONResponse(status_code=400, content={"code": "invalid_host", "message": "Commitly accepts local requests only", "details": {}})
            origin = request.headers.get("origin")
            if origin:
                from urllib.parse import urlsplit
                origin_host = (urlsplit(origin).hostname or "").lower()
                if origin_host not in {"localhost", "127.0.0.1", "::1"}:
                    return JSONResponse(status_code=403, content={"code": "invalid_origin", "message": "Cross-origin writes are not allowed", "details": {}})
        return await call_next(request)

    app.include_router(router)
    built = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if built.is_dir():
        assets = built / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str):
            if path.startswith("api/"):
                return JSONResponse(status_code=404, content={"code": "not_found", "message": "API endpoint not found", "details": {}})
            return FileResponse(built / "index.html")
    return app


app = create_app()
