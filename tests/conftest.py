import random
import pytest

@pytest.fixture(autouse=True)
def _set_seed():
    random.seed(1)
