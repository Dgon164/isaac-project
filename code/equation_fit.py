"""
equation_fit.py — gradient descent over a SYMBOLIC BASIS recovers the MECHANISM
and EXTRAPOLATES, where an MLP (a result-surface) does not. (Proposal section 5.8.)

Datapoints are sampled from a hidden generating function inside a bounded range.
  (A) GD with L1 over a menu of math primitives -> commits to a few terms ->
      recovers the equation -> extrapolates outside the range.
  (B) An MLP fit to the SAME points -> tracks inside the range, diverges outside.

Run:  python equation_fit.py
"""
import numpy as np
from sklearn.neural_network import MLPRegressor
import warnings; warnings.filterwarnings("ignore")

rng = np.random.default_rng(0)

def f(x):                                          # the hidden mechanism
    return 0.5*x**2 + 1.5*np.sin(2*x)

xtr = np.sort(rng.uniform(-3, 3, 250))             # datapoints in a BOUNDED range
ytr = f(xtr) + rng.normal(0, 0.05, len(xtr))
xin = np.linspace(-3, 3, 200)                      # interpolation test
xex = np.linspace(3, 7, 200)                       # EXTRAPOLATION test (outside range)


def design(x):                                     # the menu of primitives (the basis)
    x = np.atleast_1d(x).astype(float)
    cols = {"x": x, "x^2": x**2, "x^3": x**3, "sin(x)": np.sin(x),
            "sin(2x)": np.sin(2*x), "sin(3x)": np.sin(3*x), "cos(x)": np.cos(x),
            "cos(2x)": np.cos(2*x), "cos(3x)": np.cos(3*x), "|x|": np.abs(x)}
    names = list(cols)
    return np.stack([cols[n] for n in names], 1), names


X, names = design(xtr)
muX, sdX = X.mean(0), X.std(0) + 1e-9
Xs = (X - muX) / sdX; yc = ytr - ytr.mean()

# GRADIENT DESCENT with L1 (ISTA): commit to a few terms
w = np.zeros(Xs.shape[1]); lr, lam = 0.05, 0.05
for _ in range(60000):
    w = w - lr * (2/len(yc)) * (Xs.T @ (Xs @ w - yc))
    w = np.sign(w) * np.maximum(np.abs(w) - lr*lam, 0.0)      # L1 soft-threshold

coef = w / sdX                                                # back to original units
intercept = ytr.mean() - (muX * coef).sum()
def eqn(x):
    Xx, _ = design(x); return intercept + Xx @ coef

mlp = MLPRegressor(hidden_layer_sizes=(64, 64), max_iter=8000,
                   random_state=0).fit(xtr[:, None], ytr)
mse = lambda yp, yt: float(np.mean((yp - yt)**2))

print("=" * 66)
print("  GD OVER A SYMBOLIC BASIS — mechanism (extrapolates) vs surface (doesn't)")
print("=" * 66)
print("  hidden mechanism :  f(x) = 0.50*x^2 + 1.50*sin(2x)")
terms = " ".join(f"{coef[i]:+.2f}*{names[i]}" for i in range(len(names)) if abs(coef[i]) > 0.08)
print(f"  recovered (GD)   :  f(x) = {intercept:+.2f} {terms}")
print("  " + "-" * 62)
print(f"  {'':<24}{'interp MSE':>13}{'EXTRAP MSE':>14}")
print(f"  {'equation (GD+basis)':<24}{mse(eqn(xin), f(xin)):>13.4f}{mse(eqn(xex), f(xex)):>14.4f}")
print(f"  {'MLP (result surface)':<24}{mse(mlp.predict(xin[:,None]), f(xin)):>13.4f}"
      f"{mse(mlp.predict(xex[:,None]), f(xex)):>14.4f}")
print("  " + "-" * 62)
print("  READ: both fit INSIDE the range; the equation EXTRAPOLATES (it recovered")
print("  the rule), the MLP diverges OUTSIDE (it learned the surface, not the rule).")
