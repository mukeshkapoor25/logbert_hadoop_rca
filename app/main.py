# from fastapi import FastAPI
# from app.api.routes import router

# app = FastAPI()
# app.include_router(router)

# from fastapi import FastAPI
# from app.routes import rca

# app = FastAPI(title="LogBERT Hadoop RCA API")

# app.include_router(rca.router, prefix="/rca", tags=["Root Cause Analysis"])

from fastapi import FastAPI
from app.routes.routes import router as rca_router

app = FastAPI(title="LogBERT Hadoop RCA")

app.include_router(rca_router, prefix="/api")