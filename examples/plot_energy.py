import sys
import pandas as pd
import matplotlib.pyplot as plt


def load_data(files: list[str]) -> pd.DataFrame:
    """Load and concatenate CSV files."""
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def plot_total_energy(df: pd.DataFrame) -> None:
    col = None
    for c in ("energy_J", "energy"):
        if c in df.columns:
            col = c
            break
    if col is None:
        print("Aucune colonne d'énergie trouvée")
        return
    df[col].plot(marker="o")
    plt.xlabel("Simulation")
    plt.ylabel("Énergie totale (J)")
    plt.title("Énergie consommée par simulation")
    plt.grid(True)
    plt.savefig("energy_total.png")
    print("Graphique sauvegardé dans energy_total.png")


def plot_energy_by_node(df: pd.DataFrame) -> None:
    if "node_id" not in df.columns or "energy_consumed_J_node" not in df.columns:
        print("Colonnes 'node_id' ou 'energy_consumed_J_node' manquantes")
        return
    grouped = df.groupby("node_id")["energy_consumed_J_node"].sum()
    grouped.plot(kind="bar")
    plt.xlabel("ID nœud")
    plt.ylabel("Énergie consommée (J)")
    plt.title("Énergie consommée par nœud")
    plt.grid(axis="y")
    plt.savefig("energy_by_node.png")
    print("Graphique sauvegardé dans energy_by_node.png")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python plot_energy.py fichier1.csv [...]\n"
            "Si le CSV contient les colonnes node_id et energy_consumed_J_node, "
            "un graphique par nœud sera généré."
        )
    else:
        df = load_data(sys.argv[1:])
        if {"node_id", "energy_consumed_J_node"}.issubset(df.columns):
            plot_energy_by_node(df)
        else:
            plot_total_energy(df)
