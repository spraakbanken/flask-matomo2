# flask-matomo2

[![PyPI version](https://img.shields.io/pypi/v/flask-matomo2.svg?style=flat-square&colorB=dfb317)](https://pypi.org/project/flask-matomo2/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flask-matomo2)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/flask-matomo2)](https://pypi.org/project/flask-matomo2/)
 [![Docs](https://img.shields.io/badge/docs-readthedocs-red.svg?style=flat-square)](https://flask-matomo2.readthedocs.io)
![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)

[![Maturity badge - level 3](https://img.shields.io/badge/Maturity-Level%203%20--%20Stable-green.svg)](https://github.com/spraakbanken/getting-started/blob/main/scorecard.md)
[![Stage](https://img.shields.io/pypi/status/sparv-sbx-ocr-correction-viklofg-sweocr)](https://pypi.org/project/flask-matomo2/)

[![Code Coverage](https://codecov.io/gh/spraakbanken/flask-matomo2/branch/main/graph/badge.svg)](https://codecov.io/gh/spraakbanken/flask-matomo2/)

[![CI(check)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/check.yml/badge.svg)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/check.yml)
[![CI(release)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/release.yml/badge.svg)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/release.yml)
[![CI(scheduled)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/scheduled.yml/badge.svg)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/scheduled.yml)
[![CI(test)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/test.yml/badge.svg)](https://github.com/spraakbanken/flask-matomo2/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/flask-matomo2/badge/?version=latest)](https://flask-matomo2.readthedocs.io/en/latest/?badge=latest)

flask-matomo2 is a library which lets you track the requests of your Flask website using Matomo (Piwik).

Forked from [LucasHild/flask-matomo](https://github.com/LucasHild/flask-matomo).

## Installation

```bash
pip install flask-matomo2
```

## Using flask-matomo2 in your project

Simply add `flask-matomo2` to your dependencies:

```toml
# pyproject.toml
dependencies = [
  "flask-matomo2",
]
```

### Using uv

```bash
uv add flask-matomo2
```

### Using Poetry

```bash
poetry add flask-matomo2
```

### Using PDM

```bash
pdm add flask-matomo2
```

## Usage

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

app = Flask(__name__)
matomo = Matomo(
    app, 
    matomo_url="https://matomo.mydomain.com",
    id_site=5, token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

@app.route("/")
def index():
  return jsonify({"page": "index"})

if __name__ == "__main__":
  app.run()
```

In the code above:

1. The *Matomo* object is created by passing in the Flask application and arguments to configure Matomo.
2. The *matomo_url* parameter is the url to your Matomo installation.
3. The *id_site* parameter is the id of your site. This is used if you track several websites with one Matomo installation. It can be found if you open your Matomo dashboard, change to site you want to track and look for &idSite= in the url.
4. The *token_auth* parameter can be found in the area API in the settings of Matomo. It is required for tracking the ip address.

### Adding details to route

You can provide details to a route in 2 ways, first by using the `matomo.details` decorator:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5, token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
@matomo.details(action_name="Foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

Here the `Matomo` object is created before the `Flask` object and then calling `init_app`.
Or by giving details to the Matomo constructor:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

app = Flask(__name__)
matomo = Matomo(
  app,
  matomo_url="https://matomo.mydomain.com",
  id_site=5,
  token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  routes_details={
    "/foo": {
      "action_name": "Foo"
    }
  }
)

@app.route("/foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

### Adjusting the tracked url

If your app is behind a proxy and you don't adjust the url in any other way, you can adjust the tracked url by setting `base_url` without trailing `/` in either the constructor:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
    base_url="https://mydomain.com/apps")
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
@matomo.details(action_name="Foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

Or a call to `activate`:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo.activate_later()

matomo.activate(
    matomo_url="https://matomo.mydomain.com",
    id_site=5, 
    base_url="https://mydomain.com/apps"
)
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
@matomo.details(action_name="Foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

The result is that a request to `/foo` will be tracked as `https://mydomain.com/apps/foo`.

### Using a custom client

By default, Matomo uses `httpx.Client` to make the tracking call. You can override this by setting `client` as long as the client uses the same api as [`httpx`:s](https://www.python-httpx.org/) `Client`.

### Setting timeout for client requests

By default, Matomo uses a 5 seconds timeout for the client. You can override this timeout by setting `http_timeout`.
Note that this settings will be ignored if you provide a custom client.

### Ignoring a route

You can ignore tracking a route by decorating the route with `@matomo.ignore()`:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
)
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
@matomo.ignore()
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

Or ignore the route in the matomo constructor:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
    ignored_routes=["/foo"]
)
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

### Ignore routes by patterns

You can also ignore routes by giving a list of regexes to the constructor:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
    ignored_patterns=["/fo.*"]
)
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

### Ignore requests by User-Agent patterns

You can supply regex patterns to ignore request based on User-Agent:

```python
from flask import Flask, jsonify
from flask_matomo2 import Matomo

matomo = Matomo(
    matomo_url="https://matomo.mydomain.com",
    id_site=5,
    ignored_ua_patterns=[".*bot.*"]
)
app = Flask(__name__)
matomo.init_app(app)

@app.route("/foo")
def foo():
  return jsonify({"page": "foo"})

if __name__ == "__main__":
  app.run()
```

## Meta

Spraakbanken 2023-2024 - [https://spraakbanken.gu.se](https://spraakbanken.gu.se)
Lucas Hild (original project `Flask-Matomo`)- [https://lucas-hild.de](https://lucas.hild.de)
This project is licensed under the MIT License - see the LICENSE file for details

# Release Notes

## Latest Changes

## 0.5.0 - 2024-08-14

### Added

* track urlref. PR [#58](https://github.com/spraakbanken/flask-matomo2/pull/58) by [@kod-kristoff](https://github.com/kod-kristoff).

## 0.4.4 - 2024-08-14

### Documentation

* add metadata about python versions.

* sort out documentation of params . PR [#56](https://github.com/spraakbanken/flask-matomo2/pull/56) by [@kod-kristoff](https://github.com/kod-kristoff).

## 0.4.1 - 2024-08-14

### Changed

* fix: add "/matomo.php" to matomo_url if needed. PR [#55](https://github.com/spraakbanken/flask-matomo2/pull/55) by [@arildm](https://github.com/arildm).
  
## 0.4.0 - 2024-03-04

### Changed

* Use post request when tracking. PR [#51](https://github.com/spraakbanken/flask-matomo2/pull/51) by [@kod-kristoff](https://github.com/kod-kristoff).
* Enable late activation. PR [#50](https://github.com/spraakbanken/flask-matomo2/pull/50) by [@kod-kristoff](https://github.com/kod-kristoff).
* fix: allow for dont tracking based on user-agent. PR [#34](https://github.com/spraakbanken/flask-matomo2/pull/34) by [@kod-kristoff](https://github.com/kod-kristoff).

## 0.3.0 - 2023-05-25

### Added

* Add PerfMsTracker. PR [#33](https://github.com/spraakbanken/flask-matomo2/pull/33) by [@kod-kristoff](https://github.com/kod-kristoff).

## 0.2.0 - 2023-05-22

### Changed

* Track original IP address if request was forwarded by proxy. [Tanikai/flask-matomo](https://github.com/Tanikai/flask-matomo) by [@Tanakai](https://github.com/Tanakai).
* Change ignored routes to compare against rules instead of endpoint. [MSU-Libraries/flask-matomo](https://github.com/MSU-Libraries/flask-matomo) by [@meganschanz](https://github.com/meganschanz).
* Add ignored UserAgent prefix; set action to be url_rule. [MSU-Libraries/flask-matomo](https://github.com/MSU-Libraries/flask-matomo) by [@natecollins](https://github.com/natecollins).
* Fix matomo.ignore decorator.
* Handle request even if tracking fails. PR [#30](https://github.com/spraakbanken/flask-matomo2/pull/30) by [@kod-kristoff](https://github.com/kod-kristoff).
* Ignore routes by regex. PR [#29](https://github.com/spraakbanken/flask-matomo2/pull/29) by [@kod-kristoff](https://github.com/kod-kristoff).
* Make token_auth optional. PR [#28](https://github.com/spraakbanken/flask-matomo2/pull/28) by [@kod-kristoff](https://github.com/kod-kristoff).
* Track dynamic request data. PR [#27](https://github.com/spraakbanken/flask-matomo2/pull/27) by [@kod-kristoff](https://github.com/kod-kristoff).
* Also track request time. PR [#26](https://github.com/spraakbanken/flask-matomo2/pull/26) by [@kod-kristoff](https://github.com/kod-kristoff).
* Extend tracked variables. PR [#25](https://github.com/spraakbanken/flask-matomo2/pull/25) by [@kod-kristoff](https://github.com/kod-kristoff).
* fix matomo.details decorator. PR [#19](https://github.com/spraakbanken/flask-matomo2/pull/19) by [@kod-kristoff](https://github.com/kod-kristoff).

## 0.1.0

* Forked from [LucasHild/flask-matomo](https://github.com/LucasHild/flask-matomo).
* Renamed to `flask-matomo2`.
* Add test suite.
* Setup CI with Github Actions.
