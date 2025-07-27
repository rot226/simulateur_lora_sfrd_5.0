import sys
import pandas as pd
import matplotlib.pyplot as plt


def load_data(files: list[str]) -> pd.DataFrame:
    """Load and concatenate metrics CSV files."""
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def get_sf_columns(df: pd.DataFrame) -> tuple[list[str], list[int]]:
    """Return columns storing SF distribution and their numeric value."""
    # Columns created by pandas.json_normalize: "sf_distribution.7"
    cols = [c for c in df.columns if c.startswith("sf_distribution.")]
    if cols:
        sfs = [int(c.split(".")[1]) for c in cols]
        return cols, sfs
    # Fallback to flat columns: "sf7"
    cols = [c for c in df.columns if c.startswith("sf") and c[2:].isdigit()]
    sfs = [int(c[2:]) for c in cols]
    return cols, sfs


def plot_distribution(df: pd.DataFrame) -> None:
    cols, sfs = get_sf_columns(df)
    if not cols:
        print("Aucune colonne de distribution SF trouvée")
        return
    counts = df[cols].sum()
    plt.bar([f"SF{sf}" for sf in sfs], counts)
    plt.xlabel("Facteur d'étalement")
    plt.ylabel("Nombre")
    plt.title("Répartition des SF")
    plt.grid(axis="y")
    plt.savefig("sf_distribution.png")
    print("Graphique sauvegardé dans sf_distribution.png")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_sf_distribution.py metrics1.csv [...]")
    else:
        df = load_data(sys.argv[1:])
        plot_distribution(df)
