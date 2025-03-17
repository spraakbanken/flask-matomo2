Getting Started
===============

Installation
------------

To install flask-matomo2::

  pip install flask-matomo2

Simple integration
------------------

.. code-block:: python

  from flask import Flask, jsonify
  from flask_matomo2 import Matomo

  app = Flask(__name__)
  matomo = Matomo(
    app,
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
    token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", # Optional
    ignore_routes=["/ignore/this/path"], # Optional, can be set with the ignore decorator
    routes_details={"/foo": {"action_name": "FOO"}}, # Optional, can be set with the details decorator
    ignored_patterns=[".*/html.*"], # Optional
    ignored_ua_patterns=[".*bot.*"], # Optional, ignores requests made where the User-Agent matches any of these patterns
  )

  @app.route("/")
  def index():
    return jsonify(route="/")

  @app.route("/ignore/this/path")
  def ignore_this_path():
    return jsonify(route="/ignore/this/path")

  @app.route("/ignore/this/path/also")
  @matomo.ignore()
  def ignore_this_path():
    return jsonify(route="/ignore/this/path/also")

  @app.route("/foo")
  def foo():
    return jsonify(route="/foo")

  @app.route("/foo2")
  @matomo.details(route="/foo2", action_name="FOO/2")
  def _foo2():
    return jsonify(route="/foo2")

  @app.route("/html/path")
  @app.route("/some/html/path")
  @app.route("/some/path.html")
  def html_content():
    return "<html>Prefer tracking html with Matomo JS tracking</html>"

  if __name__ == "__main__":
    app.run()

In the code above:

#. The ``Matomo`` object is created by passing in the Flask application and arguments to configure Matomo.
#. The ``matomo_url`` parameter is the url to your Matomo installation.
#. The ``id_site`` parameter is the id of your site. This is used if you track several websites with on Matomo installation. It can be found if you open your Matomo dashboard, change to site you want to track and look for ``&idSite=`` in the url.
#. The ``token_auth`` parameter can be found in the area API in the settings of Matomo. It is required for tracking the ip address, so if skipping this will skip tracking ip-addresses.
#. The route `/ignore/this/path` is ignored by the call to the Matomo constructor.
#. The route `/ignore/this/path/also` is ignored by using the ``ignore`` decorator.
#. The route `/foo` will be tracked with `action_name=FOO` by the call to the Matomo constructor.
#. The route `/foo2` will be tracked with `action_name=FOO/2` by using the ``details``, note the needed explicit naming of the route name if the function name doesn't match the route name.
#. The routes `/html/path`, `/some/html/path` and `/some/path.html` will be ignored because they match a `ignored_pattern`.
#. All requests made where the User-Agent matches any of the patterns in `ignored_ua_patterns`, will be ignored.

The code can also be written as:

.. code-block:: python
  from flask import Flask, jsonify
  from flask_matomo2 import *

  matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
    token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", # Optional
    ignore_routes=["/ignore/this/path"], # Optional, can be set with the ignore decorator
    routes_details={"/foo": {"action_name": "FOO"}}, # Optional, can be set with the details decorator
    ignored_patterns=[".*/html.*"], # Optional
    ignored_ua_patterns=[".*bot.*"], # Optional, ignores requests made where the User-Agent matches any of these patterns
  )
  app = Flask(__name__)
  matomo.init_app(app)

Late activation
---------------

Sometimes you can't create the `Matomo` object directly, then you can mark as to be activated later:

.. code-block:: python
  ## File: plugins.py
  from flask_matomo2 import Matomo

  matomo = Matomo.activate_later()

  ## File: server.py
  from flask import Flask
  from plugins import matomo

  def create_app(settings: Dict[str, str]) -> Flask:
    app = Flask(__name__)
    matomo.activate(
      app,
      matomo_url=settings["matomo_url"],
      id_site=int(settings["id_site"]),
      base_url="https://example.com/dir",
    )
    @app.route("/")
    def index():
      return jsonify(route="/")

    return app

In this example the matomo object is defined in the file `plugins.py` and can be used by routes defined in other files.
But the `matomo_url` and `id_site` is only available when the app is created by the factory function `create_app`.

In this example we assume that our app is hosted at `https://example.com/dir` by `Apache` or `nginx` and our app is run locally.
To allow `Matomo` to track the correct urls, we can set `base_url="https://example.com/dir"`. (The same can also be solved by setting base_url in gunicorn).

Time custom parts of a request
------------------------------

Sometimes you want to track the time of a call to some other api call.

You can then use `PerfMsTracker` to track that call.

.. code-block:: python
  import flask
  import httpx
  from flask import Flask, jsonify
  from flask_matomo2 import Matomo
  from flask_matomo2.trackers import PerfMsTracker

  app = Flask(__name__)
  matomo = Matomo(
    app,
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
  )

  @app.route("/foo")
  def foo():
    with PerfMsTracker(scope=flask.g.flask_matomo2, key="pf_srv"):
      # call to other api
      data = httpx.get("https://service.mydomain.com")
    return jsonify(route="/foo", data=data)

  if __name__ == "__main__":
    app.run()

In this example, the call to the other api is tracked with the key `pf_srv`.
