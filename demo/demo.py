import numpy as np
import pandas as pd
from sklearn.datasets import make_circles
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_random_state


def make_hyperparameter_optimization_problem():
    X, y = make_circles(n_samples=50_000, random_state=0, noise=0.10)

    pd.DataFrame({0: X[:, 0], 1: X[:, 1], "class": y}).sample(4_000).plot.scatter(
        x=0, y=1, alpha=0.2, c="class", cmap="bwr"
    )

    rng = check_random_state(42)
    random_feats = rng.uniform(-1, 1, size=(X.shape[0], 4))
    X = np.hstack((X, random_feats))

    return X, y


def make_train_test(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=5_000, random_state=42)

    scaler = StandardScaler().fit(X_train)

    X_train = scaler.transform(X_train)
    X_test = scaler.transform(X_test)

    return X_train, X_test, y_train, y_test
