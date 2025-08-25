import os

from app.config import REQUIRED_ENVS


def test_required_envs_defined():
    assert "GCP_PROJECT" in REQUIRED_ENVS
    # This is a contract test to remind you to set required envs in staging/prod.
