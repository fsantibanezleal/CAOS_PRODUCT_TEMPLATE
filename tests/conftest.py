"""Make pipeline importable whether or not `pip install -e .` has run (belt-and-suspenders for CI/local).

ADR-0074: CI never trains. When CI_NO_TRAINING=1 (set by the CI workflow) and torch is
installed, the first loss.backward() of a test skips that test, so a torch training test
that forgot its @pytest.mark.bake still cannot train in CI. Locally, without the
variable, everything runs.
"""
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "data-pipeline"))


@pytest.fixture(scope="session", autouse=True)
def _no_training_in_ci():
    if os.environ.get("CI_NO_TRAINING") != "1":
        yield
        return
    try:
        import torch
    except ImportError:
        yield
        return

    def _refuse(*_args, **_kwargs):
        pytest.skip("trains a model: local offline lane only, never CI (ADR-0074)")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(torch.Tensor, "backward", _refuse)
        mp.setattr(torch.autograd, "backward", _refuse)
        yield
