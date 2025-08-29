from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from routes import auth, users, products, favorites, categories, cart
import os

app = FastAPI()

origins_str = os.getenv("ORIGINS")

if origins_str:
    origins = [origin.strip() for origin in origins_str.split(',')]
else:
    origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/", StaticFiles(directory="static/"), name="images")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(favorites.router)
app.include_router(categories.router)
app.include_router(cart.router)