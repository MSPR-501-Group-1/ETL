from fastapi import FastAPI

from api.routes.pipeline_routes import router as pipeline_router


def create_app() -> FastAPI:
    app = FastAPI(title="HealthAI ETL API", version="1.0.0")
    app.include_router(pipeline_router)
    return app

app = create_app()
