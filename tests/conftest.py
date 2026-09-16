import pytest
from syrupy.extensions.json import JSONSnapshotExtension


@pytest.fixture
def snapshot_json(snapshot):  # ruff: ignore[missing-type-function-argument, missing-return-type-undocumented-public-function]
    return snapshot.with_defaults(extension_class=JSONSnapshotExtension)
