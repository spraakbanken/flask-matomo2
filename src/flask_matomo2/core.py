"""The Flask middleware for Matomo tracking."""

import json
import logging
import random
import re
import time
import typing

import flask
import httpx
from flask import Flask, g, request

logger = logging.getLogger("flask_matomo2")


DEFAULT_HTTP_TIMEOUT: int = 5


class Matomo:
    """The Matomo object provides the central interface for interacting with Matomo."""

    def __init__(
        self,
        app: typing.Optional[Flask] = None,
        *,
        matomo_url: str,
        id_site: typing.Optional[int] = None,
        token_auth: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        client: typing.Optional[httpx.Client] = None,
        ignored_routes: typing.Optional[list[str]] = None,
        routes_details: typing.Optional[dict[str, dict[str, str]]] = None,
        ignored_patterns: typing.Optional[list[str]] = None,
        ignored_ua_patterns: typing.Optional[list[str]] = None,
        http_timeout: int = DEFAULT_HTTP_TIMEOUT,
        allowed_methods: typing.Union[list[str], typing.Literal["all-methods"]] = "all-methods",
        ignored_methods: typing.Optional[list[str]] = None,
    ) -> None:
        """Matamo tracker plugin.

        Observe that `http_timeout` is ignored if you provide your own http client.

        Args:
            app: created with Flask(__name__)
            matomo_url: url to Matomo installation
            id_site: id of the site that should be tracked on Matomo
            token_auth: token that can be found in the area API in the settings of Matomo
            base_url: base_url to the site that should be tracked. Default: None.
            client: http-client to use for tracking the requests. Must use the same api as `httpx.Client`. Default: creates `httpx.Client`
            ignored_routes: a list of routes to ignore
            routes_details: a dict of details for routes. Default: None.
            ignored_patterns: list of regexes of routes to ignore. Default: None.
            ignored_ua_patterns: list of regexes of User-Agent to ignore requests. Default: None.
            http_timeout: timeout to use when calling matomo. Default: 5.
            allowed_methods: list of methods to track or "all-methods". Default: "all-methods".
            ignored_methods: list of methods to ignore, takes precedence over allowed methods. Default: None.
        """  # noqa: E501
        self.activate(
            app=app,
            matomo_url=matomo_url,
            id_site=id_site,
            token_auth=token_auth,
            base_url=base_url,
            client=client,
            ignored_routes=ignored_routes,
            routes_details=routes_details,
            ignored_patterns=ignored_patterns,
            ignored_ua_patterns=ignored_ua_patterns,
            http_timeout=http_timeout,
            allowed_methods=allowed_methods,
            ignored_methods=ignored_methods,
        )

    @classmethod
    def activate_later(cls) -> "Matomo":
        """Create an instance of this Tracker plugin, that should be activated later."""
        return cls(matomo_url="NOT SET")

    def activate(
        self,
        app: typing.Optional[Flask] = None,
        *,
        matomo_url: str,
        id_site: typing.Optional[int] = None,
        token_auth: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        client: typing.Optional[httpx.Client] = None,
        ignored_routes: typing.Optional[list[str]] = None,
        routes_details: typing.Optional[dict[str, dict[str, str]]] = None,
        ignored_patterns: typing.Optional[list[str]] = None,
        ignored_ua_patterns: typing.Optional[list[str]] = None,
        http_timeout: int = DEFAULT_HTTP_TIMEOUT,
        allowed_methods: typing.Union[list[str], typing.Literal["all-methods"]] = "all-methods",
        ignored_methods: typing.Optional[list[str]] = None,
    ) -> None:
        """Matamo tracker plugin.

        Observe that `http_timeout` is ignored if you provide your own http client.

        Args:
            app: created with Flask(__name__)
            matomo_url: url to Matomo installation
            id_site: id of the site that should be tracked on Matomo
            token_auth: token that can be found in the area API in the settings of Matomo
            base_url: base_url to the site that should be tracked. Default: None.
            client: http-client to use for tracking the requests. Must use the same api as `httpx.Client`. Default: creates `httpx.Client`
            ignored_routes: a list of routes to ignore
            routes_details: a dict of details for routes. Default: None.
            ignored_patterns: list of regexes of routes to ignore. Default: None.
            ignored_ua_patterns: list of regexes of User-Agent to ignore requests. Default: None.
            http_timeout: timeout to use when calling matomo. Default: 5.
            allowed_methods: list of methods to track or "all-methods". Default: "all-methods".
            ignored_methods: list of methods to ignore, takes precedence over allowed methods. Default: None.
        """  # noqa: E501
        if not matomo_url:
            raise ValueError("matomo_url has to be set")

        self.app = app
        # Allow backend url with or without the filename part and/or trailing slash
        self.matomo_url = (
            matomo_url if matomo_url.endswith(("/matomo.php", "/piwik.php")) else matomo_url.strip("/") + "/matomo.php"
        )
        self.id_site = id_site
        self.token_auth = token_auth
        self.base_url = base_url.strip("/") if base_url else base_url
        self.ignored_ua_patterns = []
        if ignored_ua_patterns:
            self.ignored_ua_patterns = [re.compile(pattern) for pattern in ignored_ua_patterns]
        self.ignored_routes: list[str] = ignored_routes or []
        self.routes_details: dict[str, dict[str, str]] = routes_details or {}
        self.client = client or httpx.Client(timeout=http_timeout)
        self.ignored_patterns = []
        if ignored_patterns:
            self.ignored_patterns = [re.compile(pattern) for pattern in ignored_patterns]

        self.allowed_methods: set[str] = set()
        if allowed_methods == "all-methods":
            self.allowed_methods.update("GET", "POST", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE", "PATCH", "CONNECT")
        elif allowed_methods:
            self.allowed_methods.update(method.upper() for method in allowed_methods)
        {method.upper() for method in allowed_methods} if allowed_methods else set()
        self.ignored_methods = {method.upper() for method in ignored_methods} if ignored_methods else set()
        if not self.token_auth:
            logger.warning("'token_auth' not given, NOT tracking ip-address")

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize app.

        Args:
            app: the Flask app to init this plugin to
        """
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request_handler())

    def before_request(self) -> None:
        """Execute this before every request, parses details about request."""
        # Don't track track request, if user used ignore() decorator for route
        url_rule = str(request.url_rule)
        if url_rule in self.ignored_routes:
            return
        if request.method in self.ignored_methods or request.method not in self.allowed_methods:
            return
        if any(ua_pattern.match(str(request.user_agent)) for ua_pattern in self.ignored_ua_patterns):
            return
        if any(pattern.match(url_rule) for pattern in self.ignored_patterns):
            return

        url = self.base_url + request.path if self.base_url else request.url
        action_name = url_rule if request.url_rule else "Not Found"
        user_agent = request.user_agent
        # If request was forwarded (e.g. by a proxy), then get origin IP from
        # HTTP_X_FORWARDED_FOR. If this header field doesn't exist, return
        # remote_addr.
        ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)

        data = {
            # site data
            "idsite": str(self.id_site),
            "rec": "1",
            "apiv": "1",
            "send_image": "0",
            # request data
            "ua": user_agent,
            "action_name": action_name,
            "url": url,
            # "_id": id,
            "cvar": {
                "http_status_code": None,
                "http_method": str(request.method),
            },
            # random data
            "rand": random.getrandbits(32),
        }
        if self.token_auth:
            data["token_auth"] = self.token_auth
            data["cip"] = ip_address

        if request.accept_languages:
            data["lang"] = request.accept_languages[0][0]

        if request.referrer:
            data["urlref"] = request.referrer

        # Overwrite action_name, if it was configured with details()
        if self.routes_details.get(action_name) and self.routes_details.get(action_name, {}).get("action_name"):
            data["action_name"] = self.routes_details.get(action_name, {}).get("action_name")

        g.flask_matomo2 = {
            "tracking": True,
            "start_ns": time.perf_counter_ns(),
            "tracking_data": data,
        }

    @classmethod
    def after_request(cls, response: flask.Response) -> flask.Response:
        """Collect tracking data about current request."""
        tracking_state = g.get("flask_matomo2", {})
        if not tracking_state.get("tracking", False):
            return response

        end_ns = time.perf_counter_ns()
        gt_ms = (end_ns - g.flask_matomo2["start_ns"]) / 1000
        g.flask_matomo2["tracking_data"]["gt_ms"] = gt_ms
        g.flask_matomo2["tracking_data"]["cvar"]["http_status_code"] = response.status_code

        return response

    def teardown_request_handler(self) -> typing.Callable[[typing.Optional[BaseException]], None]:
        """Create an request teardown handler."""

        def teardown_request(exc: typing.Optional[BaseException] = None) -> None:
            """Finish tracking and send to Matomo."""
            tracking_state = g.get("flask_matomo2", {})
            if not tracking_state.get("tracking", False):
                return
            logger.debug("tracking_state=%s", tracking_state)
            tracking_data = tracking_state["tracking_data"]
            for key, value in tracking_state.get("custom_tracking_data", {}).items():
                if key == "cvar" and "cvar" in tracking_data:
                    tracking_data["cvar"].update(value)
                else:
                    tracking_data[key] = value
            if exc:
                tracking_data["ca"] = 1
                tracking_data["cra"] = str(exc)
            self.track(tracking_data=tracking_data)

        return teardown_request

    def track(
        self,
        *,
        tracking_data: dict[str, typing.Any],
    ) -> None:
        """Send request to Matomo.

        Args:
            tracking_data: dict of all variables to track
        """
        if "cvar" in tracking_data:
            cvar = tracking_data.pop("cvar")
            tracking_data["cvar"] = json.dumps(cvar)
        logger.debug("calling '%s' with '%s'", self.matomo_url, tracking_data)
        try:
            r = self.client.post(self.matomo_url, data=tracking_data)

            if r.status_code >= 300:  # noqa: PLR2004
                logger.error(
                    "Tracking call failed (status_code=%d)",
                    r.status_code,
                    extra={"status_code": r.status_code, "text": r.text},
                )
                # raise MatomoError(r.text)
        except httpx.HTTPError as exc:
            logger.exception("Tracking call failed:", extra={"exc": exc})
            logger.exception(exc)

    def ignore(self, route: typing.Optional[str] = None) -> typing.Callable[..., typing.Callable[..., typing.Any]]:
        """Ignore a route and don't track it.

        If the route has a different name than the function you must specify the 'route'.

        Args:
            route: name of the route.

        Examples:
            @app.route("/admin")
            @matomo.ignore()
            def admin():
                return render_template("admin.html")
        """

        def wrap(func: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:
            route_name = route or self.guess_route_name(func.__name__)
            self.ignored_routes.append(route_name)
            return func

        return wrap

    @classmethod
    def guess_route_name(cls, path: str) -> str:
        """Guess the route name."""
        return f"/{path}"

    def details(
        self,
        route: typing.Optional[str] = None,
        *,
        action_name: typing.Optional[str] = None,
    ) -> typing.Callable[..., typing.Any]:
        """Set details like action_name for a route.

        Args:
            route: name of the route.
            action_name: name of the site

        Examples:
            @app.route("/users")
            @matomo.details(action_name="Users")
            def all_users():
                return jsonify(users=[...])
        """

        def wrap(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:
            route_details = {}
            if action_name:
                route_details["action_name"] = action_name

            if route_details:
                route_name = route or self.guess_route_name(f.__name__)
                self.routes_details[route_name] = route_details
            return f

        return wrap
