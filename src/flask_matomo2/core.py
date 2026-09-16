"""The Flask middleware for Matomo tracking."""

import logging
import typing as t

import flask
import httpx2 as httpx
from flask import Flask, g, request
from matomo_core.core import MatomoCore

logger = logging.getLogger("flask_matomo2")


DEFAULT_HTTP_TIMEOUT: int = 5


class Matomo:
    """The Matomo object provides the central interface for interacting with Matomo."""

    def __init__(
        self,
        app: Flask | None = None,
        *,
        matomo_url: str,
        id_site: int | None = None,
        token_auth: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
        ignored_routes: list[str] | None = None,
        routes_details: dict[str, dict[str, str]] | None = None,
        ignored_patterns: list[str] | None = None,
        ignored_ua_patterns: list[str] | None = None,
        http_timeout: int = DEFAULT_HTTP_TIMEOUT,
        allowed_methods: list[str] | t.Literal["all-methods"] = "all-methods",
        ignored_methods: list[str] | None = None,
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
        app: Flask | None = None,
        *,
        matomo_url: str,
        id_site: int | None = None,
        token_auth: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
        ignored_routes: list[str] | None = None,
        routes_details: dict[str, dict[str, str]] | None = None,
        ignored_patterns: list[str] | None = None,
        ignored_ua_patterns: list[str] | None = None,
        http_timeout: int = DEFAULT_HTTP_TIMEOUT,
        allowed_methods: list[str] | t.Literal["all-methods"] = "all-methods",
        ignored_methods: list[str] | None = None,
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
        self.matomo_core = MatomoCore(
            matomo_url=matomo_url,
            id_site=id_site,
            token_auth=token_auth,
            base_url=base_url,
            ignored_routes=ignored_routes,
            ignored_methods=ignored_methods,
            ignored_patterns=ignored_patterns,
            ignored_ua_patterns=ignored_ua_patterns,
            routes_details=routes_details,
            allowed_methods=allowed_methods,
        )

        self.client = client or httpx.Client(timeout=http_timeout)

        if app is not None:
            self.init_app(app)

    @property
    def matomo_url(self) -> str:
        """The url to matomo for this middleware."""
        return self.matomo_core.matomo_url

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
        g.flask_matomo2 = self.matomo_core.build_tracking_state(
            request_url_rule=str(request.url_rule),
            method=request.method,
            user_agent=str(request.user_agent),
            request_path=request.path,
            request_url=request.url,
            remote_addr=request.remote_addr,
            forwarded_for=request.environ.get("HTTP_X_FORWARDED_FOR"),
            lang=request.accept_languages[0][0] if request.accept_languages else None,
            referrer=request.referrer,
        )

    @classmethod
    def after_request(cls, response: flask.Response) -> flask.Response:
        """Collect tracking data about current request."""
        tracking_state = g.get("flask_matomo2", {})
        if not tracking_state.get("tracking", False):
            return response

        MatomoCore.track_request_end(status_code=response.status_code, tracking_state=tracking_state)
        return response

    def teardown_request_handler(self) -> t.Callable[[BaseException | None], None]:
        """Create an request teardown handler."""

        def teardown_request(exc: BaseException | None = None) -> None:
            """Finish tracking and send to Matomo."""
            tracking_state = g.get("flask_matomo2", {})
            if not tracking_state.get("tracking", False):
                return
            logger.debug("tracking_state=%s", tracking_state)
            MatomoCore.prepare_tracking_data_for_matomo(tracking_state, exc=exc)
            tracking_data = tracking_state["tracking_data"]
            self.track(tracking_data=tracking_data)

        return teardown_request

    def track(
        self,
        *,
        tracking_data: dict[str, t.Any],
    ) -> None:
        """Send request to Matomo.

        Args:
            tracking_data: dict of all variables to track
        """
        logger.debug("calling '%s' with '%s'", self.matomo_url, tracking_data)
        try:
            r = self.client.post(self.matomo_url, data=tracking_data)

            if r.status_code >= httpx.codes.BAD_REQUEST:
                logger.error(
                    "Tracking call failed (status_code=%d)",
                    r.status_code,
                    extra={"status_code": r.status_code, "text": r.text},
                )
                # raise MatomoError(r.text)
        except httpx.HTTPError as exc:
            logger.exception("Tracking call failed:", extra={"exc": exc})
            logger.exception(exc)

    def ignore(self, route: str | None = None) -> t.Callable[..., t.Callable[..., t.Any]]:
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

        def wrap(
            func: t.Callable[..., t.Any],
        ) -> t.Callable[..., t.Any]:
            route_name = route or self.guess_route_name(
                func.__name__,  # ty: ignore[unresolved-attribute]
            )
            self.matomo_core.ignored_routes.append(route_name)
            return func

        return wrap

    @classmethod
    def guess_route_name(cls, path: str) -> str:
        """Guess the route name."""
        return f"/{path}"

    def details(
        self,
        route: str | None = None,
        *,
        action_name: str | None = None,
    ) -> t.Callable[..., t.Any]:
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

        def wrap(
            f: t.Callable[..., t.Any],
        ) -> t.Callable[..., t.Any]:
            route_details = {}
            if action_name:
                route_details["action_name"] = action_name

            if route_details:
                route_name = route or self.guess_route_name(
                    f.__name__,  # ty: ignore[unresolved-attribute]
                )
                self.matomo_core.routes_details[route_name] = route_details
            return f

        return wrap
