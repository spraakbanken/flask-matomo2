"""Example app using Matomo plugin."""

import logging
import os

from flask import Flask, jsonify

from flask_matomo2 import Matomo

MATOMO_URL = os.environ.get("MATOMO_URL", None)
MATOMO_ID_SITE = os.environ.get("MATOMO_ID_SITE", None)
MATOMO_TOKEN = os.environ.get("MATOMO_TOKEN", None)

logging.basicConfig(
    format="%(levelname)s:\t\b%(asctime)s %(name)s:%(lineno)d %(message)s",
    level=logging.DEBUG,
)

app = Flask(__name__)

matomo = Matomo(app, matomo_url=MATOMO_URL, id_site=MATOMO_ID_SITE, token_auth=MATOMO_TOKEN)


@app.route("/")
def home():  # noqa: ANN201, D103
    return jsonify({"message": "Hello World"})


if __name__ == "__main__":
    app.run(debug=True)
