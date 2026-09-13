import pandas as pd
import pypsa

DATA_DIR = "data/processed"


def build_network() -> pypsa.Network:
    buses = pd.read_csv(f"{DATA_DIR}/buses_epirus.csv")
    links = pd.read_csv(f"{DATA_DIR}/links_epirus.csv")
    generators = pd.read_csv(f"{DATA_DIR}/generators_epirus.csv")
    loads = pd.read_csv(f"{DATA_DIR}/loads_epirus.csv")

    n = pypsa.Network()

    n.add("Bus", buses["name"].values, x=buses["lon"].values, y=buses["lat"].values)

    n.add(
        "Link",
        (links["bus0"] + " -> " + links["bus1"]).values,
        bus0=links["bus0"].values,
        bus1=links["bus1"].values,
        p_nom=links["p_nom"].values,
        p_min_pu=-1,  # allow flow in both directions, like a real AC line
    )

    n.add(
        "Generator",
        generators["name"].values,
        bus=generators["bus"].values,
        carrier=generators["carrier"].values,
        p_nom=generators["p_nom"].values,
        marginal_cost=generators["marginal_cost"].values,
    )

    n.add(
        "Load",
        loads["name"].values,
        bus=loads["bus"].values,
        p_set=loads["p_set"].values,
    )

    return n


if __name__ == "__main__":
    network = build_network()
    network.optimize(solver_name="highs")

    print("\nΠαραγωγή ανά γεννήτρια (MW):")
    print(network.generators_t.p.iloc[0])

    print("\nΡοές γραμμών (MW, θετικό = bus0->bus1):")
    print(network.links_t.p0.iloc[0])

    print("\nΣυνολική ζήτηση:", network.loads["p_set"].sum(), "MW")
    print("Συνολική παραγωγή:", network.generators_t.p.iloc[0].sum(), "MW")
