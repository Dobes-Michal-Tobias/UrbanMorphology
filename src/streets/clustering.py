"""Feature matrix assembly and unsupervised clustering over settlement-level metrics."""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.config import RANDOM_SEED

DEFAULT_FEATURE_COLUMNS = [
    "orientation_entropy",
    "circuity_avg",
    "streets_per_node_avg",
    "intersection_density_km",
    "street_length_avg",
    "clustering_coefficient_avg",
    "betweenness_centrality_avg",
]


def build_feature_matrix(df: pd.DataFrame, feature_columns: list[str] = DEFAULT_FEATURE_COLUMNS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Standardize the chosen metric columns; drops rows with any missing metric.

    Returns (standardized feature matrix, the corresponding rows of `df` — same
    index — so cluster labels/coordinates can be joined back to settlement names).
    """
    clean = df.dropna(subset=feature_columns).reset_index(drop=True)
    X = StandardScaler().fit_transform(clean[feature_columns])
    return pd.DataFrame(X, columns=feature_columns, index=clean.index), clean


def fit_kmeans(X: pd.DataFrame, k: int) -> tuple[KMeans, float]:
    """Fit KMeans with `k` clusters; returns the fitted model and its silhouette score."""
    model = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init="auto")
    labels = model.fit_predict(X)
    score = silhouette_score(X, labels) if k > 1 else float("nan")
    return model, score


def sweep_k(X: pd.DataFrame, k_values: range) -> dict[int, float]:
    """Silhouette score for each candidate k — inspect before picking the final k for fit_kmeans."""
    return {k: fit_kmeans(X, k)[1] for k in k_values}


def project_2d(X: pd.DataFrame) -> pd.DataFrame:
    """PCA projection to 2D for cluster visualization."""
    coords = PCA(n_components=2, random_state=RANDOM_SEED).fit_transform(X)
    return pd.DataFrame(coords, columns=["pc1", "pc2"], index=X.index)
