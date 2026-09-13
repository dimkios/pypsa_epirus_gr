import pandas as pd
import pypsa

DATA_DIR = "data/processed"
IMPORT_GENERATOR = "Εισαγωγές/Εξαγωγές (Σύστημα + GRITA Ιταλία)"
NEW_RES_CAPACITY_FACTOR = 0.25  # δεν χρησιμοποιείται πια άμεσα - βλ. SOLAR_PROFILE

# Τυποποιημένο 24ωρο προφίλ ζήτησης (0-1, 1.0 = ώρα αιχμής).
# Τυπική καμπύλη οικιακής/εμπορικής κατανάλωσης: χαμηλό τη νύχτα, δύο αιχμές (πρωί/βράδυ).
# ΔΕΝ είναι μετρημένα στοιχεία Ηπείρου - γενική παραδοχή σχήματος καμπύλης.
DEMAND_PROFILE = [
    0.55, 0.50, 0.47, 0.45, 0.45, 0.48, 0.55, 0.65, 0.75, 0.82, 0.85, 0.87,
    0.83, 0.80, 0.78, 0.78, 0.80, 0.85, 0.95, 1.00, 0.95, 0.85, 0.72, 0.62,
]

# 24ωρο προφίλ διαθεσιμότητας ηλιακού ΑΠΕ (0-1) — ΠΡΑΓΜΑΤΙΚΑ δεδομένα από PVGIS
# (re.jrc.ec.europa.eu, Ευρωπαϊκή Επιτροπή, δορυφορική βάση ακτινοβολίας PVGIS-SARAH2),
# συντεταγμένες Ιωαννίνων (39.665, 20.8537), σύστημα 1kWp με 14% απώλειες, έτος 2020.
# Κάθε τιμή = μέσος όρος ισχύος εξόδου (ανά kWp) σε αυτή την ώρα, σε όλες τις μέρες του έτους —
# δηλ. "τυπική ημέρα" που ήδη συνυπολογίζει σύννεφα και εποχική διακύμανση.
# Δεδομένα: data/raw/pvgis_ioannina_2020.json.
SOLAR_PROFILE = [
    0.0, 0.0, 0.0, 0.0, 0.0103, 0.0648, 0.1655, 0.2914, 0.3892, 0.4577, 0.4785, 0.4617,
    0.4041, 0.3317, 0.2273, 0.1263, 0.0483, 0.0076, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]

BATTERY_BUS = "Άραχθος ΚΥΤ"


def build_network(
    new_res_mw: float = 0,
    import_limit_mw: float | None = None,
    demand_change_pct: float = 0,
    battery_mw: float = 0,
    battery_hours: float = 4,
) -> pypsa.Network:
    """Χτίζει το δίκτυο PyPSA της Ηπείρου πάνω σε 24 ωριαία snapshots (μία τυπική μέρα).

    new_res_mw: νέα ισχύς ΑΠΕ (MW), κατανεμημένη αναλογικά με πληθυσμό στους 4 κόμβους-φορτία,
        με διαθεσιμότητα που ακολουθεί το SOLAR_PROFILE.
    import_limit_mw: αν δοθεί, αντικαθιστά το p_nom της γεννήτριας εισαγωγών/εξαγωγών
        (0 = καμία εισαγωγή επιτρεπτή, δηλ. πλήρης ενεργειακή ανεξαρτησία Ηπείρου).
    demand_change_pct: ποσοστιαία μεταβολή όλων των φορτίων (π.χ. 10 = +10%).
    battery_mw: ισχύς μπαταρίας (MW) στον κόμβο ΚΥΤ Άραχθος. 0 = καμία μπαταρία.
    battery_hours: ώρες αποθήκευσης στη μέγιστη ισχύ (π.χ. 4 = χωρητικότητα 4×battery_mw MWh).
    """
    buses = pd.read_csv(f"{DATA_DIR}/buses_epirus.csv")
    links = pd.read_csv(f"{DATA_DIR}/links_epirus.csv")
    generators = pd.read_csv(f"{DATA_DIR}/generators_epirus.csv")
    loads = pd.read_csv(f"{DATA_DIR}/loads_epirus.csv")

    if import_limit_mw is not None:
        generators.loc[generators["name"] == IMPORT_GENERATOR, "p_nom"] = import_limit_mw

    loads["p_set"] = loads["p_set"] * (1 + demand_change_pct / 100)

    n = pypsa.Network()
    n.set_snapshots(range(24))

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

    # Οι υδρο-γεννήτριες και οι εισαγωγές θεωρούνται διαθέσιμες όλες τις ώρες (p_max_pu=1,
    # η προεπιλογή) — απλοποίηση, δεν μοντελοποιούμε εποχιακή/ημερήσια διαθεσιμότητα νερού.

    # ΠΡΑΓΜΑΤΙΚΗ ήδη-εγκατεστημένη ισχύς ΑΠΕ (αιολικά+φωτοβολταϊκά) ανά κόμβο — όχι υποθετική,
    # από αρχείο ΑΔΜΗΕ "ΑΠΕ με προσφορά σύνδεσης/σε λειτουργία" (Απρίλιος 2026). Σύνολο ~522MW.
    # Απλοποίηση: εφαρμόζουμε το ίδιο SOLAR_PROFILE και στα αιολικά (δεν έχουμε ακόμα πραγματικό
    # προφίλ ανέμου) — υποεκτιμά πιθανώς τη νυχτερινή παραγωγή των αιολικών πάρκων.
    res_existing = pd.read_csv(f"{DATA_DIR}/res_existing_epirus.csv")
    res_existing_names = "ΑΠΕ (υπάρχουσα) - " + res_existing["bus"].values
    n.add(
        "Generator",
        res_existing_names,
        bus=res_existing["bus"].values,
        carrier="res_existing",
        p_nom=res_existing["p_nom"].values,
        marginal_cost=0,
    )
    solar_profile_existing = pd.Series(SOLAR_PROFILE, index=n.snapshots)
    n.generators_t.p_max_pu = pd.concat(
        [
            n.generators_t.p_max_pu,
            pd.DataFrame({name: solar_profile_existing for name in res_existing_names}),
        ],
        axis=1,
    )

    n.add("Load", loads["name"].values, bus=loads["bus"].values)
    demand_profile = pd.Series(DEMAND_PROFILE, index=n.snapshots)
    n.loads_t.p_set = pd.DataFrame(
        {name: peak * demand_profile for name, peak in zip(loads["name"], loads["p_set"])}
    )

    if new_res_mw > 0:
        weights = loads["p_set"] / loads["p_set"].sum()
        res_names = "ΑΠΕ (νέα) - " + loads["name"].values
        n.add(
            "Generator",
            res_names,
            bus=loads["bus"].values,
            carrier="res_new",
            p_nom=(new_res_mw * weights).values,
            marginal_cost=0,
        )
        solar_profile = pd.Series(SOLAR_PROFILE, index=n.snapshots)
        n.generators_t.p_max_pu = pd.concat(
            [n.generators_t.p_max_pu, pd.DataFrame({name: solar_profile for name in res_names})],
            axis=1,
        )

    if battery_mw > 0:
        n.add(
            "StorageUnit",
            "Μπαταρία Ηπείρου",
            bus=BATTERY_BUS,
            p_nom=battery_mw,
            max_hours=battery_hours,
            cyclic_state_of_charge=True,  # η στάθμη στο τέλος της μέρας = στάθμη στην αρχή
            efficiency_store=0.95,
            efficiency_dispatch=0.95,
        )

    return n


if __name__ == "__main__":
    network = build_network()
    network.optimize(solver_name="highs")

    print("\nΠαραγωγή ανά γεννήτρια (MW) ανά ώρα:")
    print(network.generators_t.p)

    print("\nΣυνολική ημερήσια ζήτηση:", network.loads_t.p_set.sum().sum(), "MWh")
    print("Συνολική ημερήσια παραγωγή:", network.generators_t.p.sum().sum(), "MWh")
