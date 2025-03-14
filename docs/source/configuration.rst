Configuration
===============

Matomo url *required*
---------------------

You must give the the `matomo_url`. If the given url doesn't end with `/matomo.php` or `/piwik.php`
then `/matomo.php` will be added.

This can be set either in the constructor:

.. code-block:: python
  matomo = Matomo(matomo_url="https://trackingserver")
  # or, equivalently,
  matomo = Matomo(matomo_url="https://trackingserver/matomo.php")

Or when activating the Matomo object:

.. code-block:: python
  matomo = Matomo.activate_later()

  matomo.activate(matomo_url="https://trackingserver")
  # or, equivalently,
  matomo.activate(matomo_url="https://trackingserver/matomo.php")

Id site *required*
------------------

You must also give the `id_site` as an int.

This can be given either in the constructor or in the call to `activate`.

Token auth
----------

You can optionally give `token_auth` (retrieved from your tracking server), this is required to track
some information.

This can be given either in the constructor or in the call to `activate`.

Base url
--------

If your app is behind a proxy, you can adjust the tracked url by setting `base_url`.
This only needed if you don't adjust the url any other way (gunicorn, reverse_proxied, etc)

This can be given either in the constructor or in the call to `activate`.

Client
------

You can supply your own http client by setting `client`.
This must use the same api as `httpx`:s `Client`.

If not supplied a new `httpx.Client` will be created.

Http timeout
------------

You can override the default timeout (5 seconds) of the client by setting `http_timeout`.

This setting will be ignore if you provide a custom client.

Details about a route
---------------------

You can set details for a route, which will overwrite the parsed details.

.. code-block:: python

  @app.route("/users")
  @matomo.details(route="/users", action_name="Users")
  def all_users():
      return render_template("users.html")

Or passing the information to the `Matomo` constructor.

.. code-block:: python

  matomo = Matomo(
    ...,
    routes_details={"/users": {"action_name": "Users"}},
  )


Ignore routes
-------------

If you wan't to prevent one route from being tracked, you can ignore it by adding a decorator in front of the function.

.. code-block:: python

  @app.route("/admin")
  @matomo.ignore()
  def admin():
      return render_template("admin.html")

Or passing the information to the `Matomo` constructor.

.. code-block:: python

  matomo = Matomo(
    ...,
    ignored_routes=["/admin"],
  )

Ignore routes by patterns
-------------------------

You can also prevent all routes that match a pattern from being tracked, by giving the pattern(s) to the Matomo constructor.

.. code-block:: python

  matomo = Matomo(
    ...,
    ignored_patterns=["/.*admin.*"],
  )

Ignore tracking based on user-agent regex
-----------------------------------------

You can skip tracking requests made with specific user-agents.

.. code-block:: python

  matomo = Matomo(
    ...,
    ignored_ua_patterns=[".*bot.*"],
  )

Tracking based on HTTP method
-----------------------------

You can controll which HTTP methods that should be tracked.

Either by specifing `allow_methods` to allow.

.. code-block:: python

  matomo = Matomo(
    ...,
    allowed_methods=["get", "POST"],
  )

Or `ignored_methods`to ignore specific methods.

.. code-block:: python

  matomo = Matomo(
    ...,
    ignored_methods=["OPTIONS"],
  )

If both `allowed_methods` and `ignored_methods` is given, `ignored_methods` takes presedecnce.
