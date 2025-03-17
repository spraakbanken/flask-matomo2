# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2025-03-17

### Added

- Make it possible to control tracking by http method by [@kod-kristoff](https://github.com/kod-kristoff)
- Enable setting http timeout by [@kod-kristoff](https://github.com/kod-kristoff)
- Only support Python version 3.9 and above.

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
