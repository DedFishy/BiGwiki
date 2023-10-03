from flask import Flask
import dotenv
from errors import DebugError
import os
from app import App

dotenv.load_dotenv()

app = App(__name__)

if __name__ == "__main__":
    if not os.getenv("DEBUG"):
        raise DebugError("You shouldn't run the Flask debug server in a production environment! Set the .env variable DEBUG to true if you need to debug.")
    app.run(os.getenv("DEBUG_HOST"), os.getenv("DEBUG_PORT"))