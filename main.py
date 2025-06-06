from fastapi import FastAPI
from db import Base, engine  # <-- Add engine here
from routes import auth, designer_order_routes, order_routes, store_routes
from models.user import User  # This ensures table gets registered
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Create all tables
Base.metadata.create_all(bind=engine) # type: ignore

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media", StaticFiles(directory="media"), name="media")
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(store_routes.router, prefix="/stores", tags=["Stores"])
app.include_router(order_routes.router, prefix="/orders", tags=["Orders"])
app.include_router(designer_order_routes.router, prefix="/designer", tags=["Designer Cake Orders"])
