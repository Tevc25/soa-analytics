from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from routers.router import router
import uvicorn
import os

app = FastAPI(
    title="Analytics Service",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

def get_allowed_origins():
    env_origins = os.getenv("CORS_ORIGINS")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",")]

    common_ports = [3000, 3001, 5173, 5174, 8080, 8081]
    return [
        f"http://{host}:{port}"
        for host in ["localhost", "127.0.0.1"]
        for port in common_ports
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    """Serve OpenAPI schema without authentication."""
    return get_openapi(title=app.title, version="1.0.0", routes=app.routes)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Serve Swagger UI without authentication."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_ui_parameters={"persistAuthorization": True},
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)
