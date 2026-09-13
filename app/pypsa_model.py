import pandas as pd
import pypsa

DATA_DIR = "data/processed"
IMPORT_GENERATOR = "Εισαγωγές/Εξαγωγές Συστήματος"
NEW_RES_CAPACITY_FACTOR = 0.25  # υπόθεση: μέσος συντελεστής διαθεσιμότητας ΑΠΕ σε αυτό το snapshot


def build_network(
    new_res_mw: float = 0,
    import_limit_mw: float | None = None,
    demand_change_pct: float = 0,
) -> pypsa.Network:
    """Χτίζει το δίκτυο PyPSA της Ηπείρου από τα CSV, με προαιρετικές παραμέτρους σεναρίου.

    new_res_mw: νέα ισχύς ΑΠΕ (MW) προς προσθήκη, κατανεμημένη αναλογικά με τον
        πληθυσμό στους ίδιους κόμβους όπου έχουμε ήδη εκτιμήσει ζήτηση.
    import_limit_mw: αν δοθεί, αντικαθιστά το p_nom της γεννήτριας εισαγωγών/εξαγωγών
        (0 = καμία εισαγωγή επιτρεπτή, δηλ. πλήρης ενεργειακή ανεξαρτησία Ηπείρου).
    demand_change_pct: ποσοστιαία μεταβολή όλων των φορτίων (π.χ. 10 = +10%).
    """
    buses = pd.read_csv(f"{DATA_DIR}/buses_epirus.csv")
    links = pd.read_csv(f"{DATA_DIR}/links_epirus.csv")
    generators = pd.read_csv(f"{DATA_DIR}/generators_epirus.csv")
    loads = pd.read_csv(f"{DATA_DIR}/loads_epirus.csv")

    if import_limit_mw is not None:
        generators.loc[generators["name"] == IMPORT_GENERATOR, "p_nom"] = import_limit_mw

    loads["p_set"] = loads["p_set"] * (1 + demand_change_pct / 100)

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

    if new_res_mw > 0:
        weights = loads["p_set"] / loads["p_set"].sum()
        n.add(
            "Generator",
            "ΑΠΕ (νέα) - " + loads["name"].values,
            bus=loads["bus"].values,
            carrier="res_new",
            p_nom=(new_res_mw * weights).values,
            p_max_pu=NEW_RES_CAPACITY_FACTOR,
            marginal_cost=0,
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
