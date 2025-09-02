# models/fds.py
import numpy as np
from scipy.stats import beta

class RiskModel:
    def __init__(self, alpha=1, beta_param=1):
        self.alpha = alpha
        self.beta_param = beta_param

    def update(self, outcome: int):
        """Update Bayesian parameters based on repayment outcome (1=good, 0=bad)."""
        self.alpha += outcome
        self.beta_param += (1 - outcome)

    def score(self):
        """Return mean of Beta distribution as risk score (probability of repayment)."""
        return self.alpha / (self.alpha + self.beta_param)
