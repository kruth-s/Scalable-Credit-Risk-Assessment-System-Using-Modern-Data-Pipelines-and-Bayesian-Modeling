# tests/test_model.py
import pytest
from models.fds import RiskModel

def test_risk_model_update():
    model = RiskModel()
    model.update(1)  # good repayment
    assert model.score() > 0.5
    model.update(0)  # default
    assert 0 < model.score() < 1
