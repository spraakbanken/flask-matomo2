import copy
import time
import typing
from dataclasses import dataclass
from unittest import mock

import flask
import httpx
import pytest
from flask import Flask
from syrupy import matchers
from werkzeug import exceptions as werkzeug_exc

from flask_matomo2 import Matomo
from flask_matomo2.trackers import PerfMsTracker


@dataclass
class Response:
    status_code: int
    text: str = "text"


@pytest.fixture(name="matomo_client")
def fixture_matomo_client() -> httpx.Client:
    client = mock.Mock(spec=httpx.Client)

    client.post = mock.Mock(return_value=Response(status_code=204))
    return client


@pytest.fixture(name="settings", scope="session")
def fixture_settings() -> dict:
    return {"idsite": 1, "base_url": "http://testserver", "token_auth": "FAKE_TOKEN"}


def create_app(matomo_client: httpx.Client, settings: dict) -> Flask:
    matomo = Matomo.activate_later()
    app = Flask(__name__)

    app.config.update({"TESTING": True})
    matomo.activate(
        app,
        client=matomo_client,
        matomo_url="http://trackingserver",
        id_site=settings["idsite"],
        token_auth=settings["token_auth"],
        ignored_routes=["/health"],
        ignored_patterns=[".*/old.*"],
        ignored_ua_patterns=["creepy-bot.*"],
        allowed_methods=["GET", "PoST", "HEAD", "OPTIONS"],
        ignored_methods=["OptiOns"],
    )

    @app.route("/foo", methods=("GET", "POST", "PUT"))
    def foo() -> str:
        return "foo"

    @app.route("/health")
    def health_fn() -> str:
        return "ok"

    @app.route("/heartbeat")
    @matomo.ignore()
    def heartbeat() -> str:
        return "ok"

    @app.route("/some/old/path")
    @app.route("/old/path")
    @app.route("/really/old")
    def old() -> str:
        return "old"

    @app.route("/set/custom/var")
    def custom_var() -> str:
        with PerfMsTracker(scope=flask.g.flask_matomo2, key="pf_srv"):
            flask.g.flask_matomo2["custom_tracking_data"] = {
                "e_a": "Playing",
                "cvar": {"anything": "goes"},
            }
            time.sleep(0.1)
        return "custom_var"

    @app.route("/bor")
    @matomo.details(action_name="Foo-Bor")
    def bor() -> str:
        return "foo-bor"

    @app.route("/bar")
    def bar() -> str:
        raise werkzeug_exc.InternalServerError("bar doesn't work")

    # async def baz(request):
    #     data = await request.json()
    #     return JSONResponse({"data": data})

    # app.add_route("/baz", baz, methods=["POST"])
    return app


@pytest.fixture(name="app")
def fixture_app(matomo_client: httpx.Client, settings: dict) -> Flask:
    return create_app(matomo_client, settings)


@pytest.fixture(name="app_wo_token")
def fixture_app_wo_token(matomo_client: httpx.Client, settings: dict) -> Flask:
    new_settings = copy.deepcopy(settings)
    new_settings["token_auth"] = None
    return create_app(matomo_client, new_settings)


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> typing.Generator[httpx.Client, None, None]:
    with httpx.Client(transport=httpx.WSGITransport(app=app), base_url="http://testserver") as client:
        yield client


@pytest.fixture(name="client_wo_token")
def fixture_client_wo_token(
    app_wo_token: Flask,
) -> typing.Generator[httpx.Client, None, None]:
    with httpx.Client(transport=httpx.WSGITransport(app=app_wo_token), base_url="http://testserver") as client:
        yield client


def make_matcher():  # noqa: ANN201
    return matchers.path_type({"gt_ms": (float,), "rand": (int,)})


def test_matomo_client_sets_urlref_if_referer_exists(
    client: httpx.Client,
    matomo_client: mock.Mock,
    snapshot_json,  # noqa: ANN001
) -> None:
    _response = client.get("/foo", headers={"Referer": "http://example.com"})

    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())


@pytest.mark.parametrize(
    "in_url, stored_url",
    [
        ("http://trackingserver", "http://trackingserver/matomo.php"),
        ("http://trackingserver/", "http://trackingserver/matomo.php"),
        ("http://trackingserver/matomo.php", "http://trackingserver/matomo.php"),
        ("http://trackingserver/piwik.php", "http://trackingserver/piwik.php"),
    ],
)
def test_matomo_url_works_with_or_without_trailing_slash_or_filename(in_url: str, stored_url: str) -> None:
    matomo = Matomo(matomo_url=in_url)
    assert matomo.matomo_url == stored_url


def test_matomo_client_gets_called_on_get_foo(client: httpx.Client, matomo_client: mock.Mock, snapshot_json) -> None:  # noqa: ANN001
    response = client.get("/foo")
    assert response.status_code == 200

    matomo_client.post.assert_called()

    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())


def test_matomo_client_is_not_called_when_user_agent_should_be_ignored(
    client: httpx.Client, matomo_client: mock.Mock
) -> None:
    response = client.get("/foo", headers={"user-agent": "creepy-bot-with-suffix"})
    assert response.status_code == 200

    matomo_client.post.assert_not_called()


def test_matomo_client_is_not_called_when_method_should_be_ignored(
    client: httpx.Client, matomo_client: mock.Mock
) -> None:
    response = client.options("/foo")
    assert response.status_code == 200

    matomo_client.post.assert_not_called()


def test_matomo_client_is_not_called_when_method_is_not_allowed(client: httpx.Client, matomo_client: mock.Mock) -> None:
    response = client.put("/foo")
    assert response.status_code == 200

    matomo_client.post.assert_not_called()


def test_middleware_works_without_token(client_wo_token: httpx.Client, matomo_client: mock.Mock, snapshot_json) -> None:  # noqa: ANN001
    response = client_wo_token.get("/foo")
    assert response.status_code == 200

    matomo_client.post.assert_called()  # get.assert_called()

    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())


def test_lang_gets_tracked_if_accept_language_is_set(
    client: httpx.Client,
    matomo_client: mock.Mock,
    snapshot_json,  # noqa: ANN001
) -> None:
    response = client.get("/foo", headers={"accept-language": "sv"})
    assert response.status_code == 200

    matomo_client.post.assert_called()  # get.assert_called()

    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())


def test_x_forwarded_for_changes_ip(client: httpx.Client, matomo_client: mock.Mock, snapshot_json) -> None:  # noqa: ANN001
    forwarded_ip = "127.0.0.2"
    response = client.get("/foo", headers={"x-forwarded-for": forwarded_ip})
    assert response.status_code == 200

    matomo_client.post.assert_called()  # get.assert_called()

    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())


def test_matomo_client_doesnt_gets_called_on_get_health(
    client: httpx.Client,
    matomo_client: mock.Mock,
) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    matomo_client.post.assert_not_called()


def test_matomo_client_doesnt_gets_called_on_get_heartbeat(
    client: httpx.Client,
    matomo_client: mock.Mock,
) -> None:
    response = client.get("/heartbeat")
    assert response.status_code == 200

    matomo_client.post.assert_not_called()


def test_matomo_details_updates_action_name(client: httpx.Client, matomo_client: mock.Mock, snapshot_json) -> None:  # noqa: ANN001
    response = client.get("/bor")
    assert response.status_code == 200

    matomo_client.post.assert_called()  # get.assert_called()

    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())


@pytest.mark.parametrize("path", ["/some/old/path", "/old/path", "/really/old"])
def test_matomo_client_doesnt_gets_called_on_get_old(client: httpx.Client, matomo_client: mock.Mock, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    matomo_client.post.assert_not_called()


def test_matomo_client_gets_called_on_get_custom_var(
    client: httpx.Client,
    matomo_client: mock.Mock,
    snapshot_json,  # noqa: ANN001
) -> None:
    response = client.get("/set/custom/var")
    assert response.status_code == 200

    matomo_client.post.assert_called()

    matcher = matchers.path_type({"gt_ms": (float,), "rand": (int,), "pf_srv": (float,)})
    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=matcher)


def test_api_works_even_if_tracking_fails(client: httpx.Client, matomo_client: mock.Mock) -> None:
    matomo_client.post = mock.Mock(return_value=Response(status_code=500))
    response = client.get("/foo")

    assert response.status_code == 200

    matomo_client.post.assert_called()


def test_app_works_even_if_tracking_raises(client: httpx.Client, matomo_client: mock.Mock) -> None:
    matomo_client.post = mock.Mock(side_effect=httpx.HTTPError("custom"))
    response = client.get("/foo")

    assert response.status_code == 200

    matomo_client.post.assert_called()


def test_matomo_client_gets_called_on_get_bar(client: httpx.Client, matomo_client: mock.Mock, snapshot_json) -> None:  # noqa: ANN001
    response = client.get("/bar")
    assert response.status_code >= 500

    matomo_client.post.assert_called()
    assert matomo_client.post.call_args.kwargs["data"] == snapshot_json(matcher=make_matcher())
