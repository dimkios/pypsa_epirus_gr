import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pypsa_model import build_network

st.set_page_config(page_title="PyPSA Epirus GR", layout="wide")

st.title("Δίκτυο Ηλεκτρικής Ενέργειας Ηπείρου")
st.caption(
    "Phase 3 — πραγματική τοπολογία & γεννήτριες ΑΔΜΗΕ, μοντέλο βελτιστοποίησης PyPSA "
    "με παραμετροποιήσιμο σενάριο (ΑΠΕ, εισαγωγές, ζήτηση)."
)

buses = pd.read_csv("data/processed/buses_epirus.csv")
links = pd.read_csv("data/processed/links_epirus.csv")

TYPE_LABELS = {
    "substation": "Υποσταθμός",
    "hydro": "Υδροηλεκτρικός Σταθμός",
    "kyt": "Κέντρο Υπερύψηλης Τάσης",
}
buses["Τύπος"] = buses["type"].map(TYPE_LABELS)
bus_coords = buses.set_index("name")[["lat", "lon"]]

fig = px.scatter_map(
    buses,
    lat="lat",
    lon="lon",
    color="regional_unit",
    hover_name="name",
    hover_data={"lat": False, "lon": False, "confidence": True, "Τύπος": True},
    zoom=7.4,
    center={"lat": 39.55, "lon": 20.85},
    height=650,
)

for _, link in links.iterrows():
    b0, b1 = bus_coords.loc[link["bus0"]], bus_coords.loc[link["bus1"]]
    fig.add_trace(
        go.Scattermap(
            lat=[b0["lat"], b1["lat"]],
            lon=[b0["lon"], b1["lon"]],
            mode="lines",
            line={"width": 2, "color": "gray"},
            hoverinfo="skip",
            showlegend=False,
        )
    )

fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

st.plotly_chart(fig, use_container_width=True)

with st.expander("Πίνακας κόμβων"):
    st.dataframe(
        buses[["name", "regional_unit", "Τύπος", "lat", "lon", "confidence", "source_note"]],
        use_container_width=True,
    )

st.caption(
    "Πηγή: ΑΔΜΗΕ, Δεκαετές Πρόγραμμα Ανάπτυξης Συστήματος Μεταφοράς 2021-2030 "
    "(κόμβοι, γραμμές και ισχύς γεννητριών από τα single-line diagrams). "
    "Οι συντεταγμένες με confidence='approximate' προέκυψαν από ανάγνωση του γεωγραφικού "
    "χάρτη του ΑΔΜΗΕ, όχι από επίσημες δημοσιευμένες συντεταγμένες."
)

st.divider()
st.header("Σενάριο")
st.caption(
    "Phase 4 — μία τυπική ημέρα (24 ωριαία snapshots) αντί για μία στιγμή. "
    "Πειραματίσου με παραμέτρους και δες πώς αλλάζει το ημερήσιο ισοζύγιο."
)

col_res, col_import, col_demand, col_batt = st.columns(4)
with col_res:
    new_res_mw = st.slider(
        "Νέα ισχύς ΑΠΕ (MW)",
        min_value=0,
        max_value=500,
        value=0,
        step=10,
        help=(
            "Κατανέμεται αναλογικά με τον πληθυσμό στους 4 κόμβους-φορτία. Ακολουθεί "
            "πραγματικό μέσο ηλιακό προφίλ από το PVGIS (Ιωάννινα, 2020) — δεν είναι πλέον "
            "υποθετική καμπύλη, βλ. tab 'Generator' παρακάτω."
        ),
    )
with col_import:
    import_limit_mw = st.slider(
        "Μέγιστες επιτρεπτές εισαγωγές (MW)",
        min_value=0,
        max_value=1000,
        value=1000,
        step=50,
        help="0 = πλήρης ενεργειακή ανεξαρτησία Ηπείρου από το υπόλοιπο σύστημα.",
    )
with col_demand:
    demand_change_pct = st.slider(
        "Μεταβολή ζήτησης (%)",
        min_value=-20,
        max_value=100,
        value=0,
        step=5,
        help="Εφαρμόζεται ομοιόμορφα σε όλα τα εκτιμώμενα φορτία, σε κάθε ώρα.",
    )
with col_batt:
    battery_mw = st.slider(
        "Ισχύς μπαταρίας (MW)",
        min_value=0,
        max_value=200,
        value=0,
        step=10,
        help=(
            "Τοποθετείται στο ΚΥΤ Άραχθος. Χωρητικότητα = 4 ώρες × ισχύς. "
            "Με άφθονα ευέλικτα υδροηλεκτρικά, η μπαταρία συχνά δεν χρειάζεται — "
            "δοκίμασε να προσθέσεις πολλή ΑΠΕ ΚΑΙ να μειώσεις τη ζήτηση για να τη δεις να δουλεύει."
        ),
    )

network = build_network(
    new_res_mw=new_res_mw,
    import_limit_mw=import_limit_mw,
    demand_change_pct=demand_change_pct,
    battery_mw=battery_mw,
)

st.divider()
st.header("📚 Πώς φτιάχνεται το μοντέλο PyPSA (εκπαιδευτικό)")
st.caption(
    "Παρένθεση πριν τη βελτιστοποίηση: τι είναι κάθε 'component' του PyPSA, ο πραγματικός "
    "κώδικας που το φτιάχνει σε αυτό το project, και τα πραγματικά δεδομένα που προκύπτουν."
)

tab_bus, tab_gen, tab_load, tab_link, tab_storage, tab_opt = st.tabs(
    ["Bus", "Generator", "Load", "Link", "StorageUnit", "Snapshot & optimize()"]
)

with tab_bus:
    st.markdown(
        "**Bus** = ένας ηλεκτρικός κόμβος του δικτύου (υποσταθμός, σταθμός παραγωγής, ΚΥΤ). "
        "Όλα τα άλλα components (Generator, Load, Link) συνδέονται *πάνω* σε buses — είναι ο "
        "βασικός 'σκελετός' κάθε δικτύου PyPSA."
    )
    st.code(
        'n.add("Bus", buses["name"].values, x=buses["lon"].values, y=buses["lat"].values)',
        language="python",
    )
    st.caption("`x`, `y` = γεωγραφικό μήκος/πλάτος (χρησιμεύουν μόνο για οπτικοποίηση σε χάρτη).")
    st.dataframe(network.buses[["x", "y"]], use_container_width=True)

with tab_gen:
    st.markdown(
        "**Generator** = πηγή παραγωγής συνδεδεμένη σε ένα bus. Ο solver αποφασίζει πόσο θα "
        "'παράξει' η καθεμία (μέσα στο όριο `p_nom`), επιλέγοντας πάντα πρώτα τις φθηνότερες "
        "(μικρότερο `marginal_cost`) — αυτό λέγεται *merit order*."
    )
    st.code(
        'n.add(\n'
        '    "Generator", generators["name"].values,\n'
        '    bus=generators["bus"].values,\n'
        '    carrier=generators["carrier"].values,\n'
        '    p_nom=generators["p_nom"].values,          # μέγιστη ισχύς (MW)\n'
        '    marginal_cost=generators["marginal_cost"].values,  # κόστος ανά MWh\n'
        ')',
        language="python",
    )
    st.caption(
        "Στο δικό μας δίκτυο: 5 πραγματικά υδροηλεκτρικά (χαμηλό marginal_cost=5) + 1 τεχνητή "
        "'γεννήτρια' εισαγωγών (marginal_cost=60) που αναπαριστά το υπόλοιπο ελληνικό σύστημα — "
        "χρησιμοποιείται μόνο αν τα υδροηλεκτρικά δεν επαρκούν — και, αν το ρύθμισες παραπάνω "
        "στο 'Σενάριο', επιπλέον γεννήτριες 'ΑΠΕ (νέα)' με marginal_cost=0 (δηλ. προτιμώνται "
        "πρώτες από τον solver, πριν καν τα υδροηλεκτρικά). Η διαθεσιμότητά τους (`p_max_pu`) "
        "ανά ώρα προέρχεται από **πραγματικά δεδομένα ηλιακής ακτινοβολίας PVGIS** για τα "
        "Ιωάννινα (μέσος όρος έτους 2020, δορυφορική βάση PVGIS-SARAH2) — όχι πια υπόθεση σχήματος."
    )
    st.dataframe(network.generators[["bus", "carrier", "p_nom", "marginal_cost"]], use_container_width=True)
    if new_res_mw > 0:
        st.caption("Ωριαία διαθεσιμότητα ΑΠΕ (p_max_pu) — πραγματικό προφίλ PVGIS:")
        res_cols = [c for c in network.generators_t.p_max_pu.columns if c.startswith("ΑΠΕ (νέα)")]
        if res_cols:
            st.line_chart(network.generators_t.p_max_pu[res_cols[0]])

with tab_load:
    st.markdown(
        "**Load** = κατανάλωση συνδεδεμένη σε ένα bus. Το `p_set` είναι η ζήτηση που *πρέπει* "
        "να καλυφθεί — ο solver δεν έχει επιλογή εδώ, είναι περιορισμός (constraint), όχι απόφαση. "
        "Από το Phase 4 και μετά, έχουμε **24 snapshots** (μία τυπική ημέρα), οπότε το `p_set` "
        "δεν είναι πια ένας αριθμός αλλά μια *χρονοσειρά* — γι' αυτό ζει στο `n.loads_t.p_set` "
        "(η κατάληξη `_t` δηλώνει 'time-varying' σε όλο το PyPSA)."
    )
    st.code(
        'n.add("Load", loads["name"].values, bus=loads["bus"].values)\n\n'
        '# το p_set γίνεται χρονοσειρά: αιχμή (peak) × τυποποιημένο 24ωρο προφίλ ζήτησης\n'
        'demand_profile = pd.Series(DEMAND_PROFILE, index=n.snapshots)\n'
        'n.loads_t.p_set = pd.DataFrame(\n'
        '    {name: peak * demand_profile for name, peak in zip(loads["name"], loads["p_set"])}\n'
        ')',
        language="python",
    )
    st.caption(
        "Οι τιμές αιχμής (`peak`) είναι **εκτιμήσεις** (πληθυσμιακή αναλογία), όχι πραγματικές "
        "μετρήσεις κατανάλωσης — βλ. [[Κενό - Ζήτηση ανά περιφέρεια]] στο Obsidian. Το *σχήμα* "
        "της καμπύλης (DEMAND_PROFILE) είναι επίσης παραδοχή, όχι μετρημένο προφίλ Ηπείρου."
    )
    st.line_chart(network.loads_t.p_set)

with tab_link:
    st.markdown(
        "**Link** = ελεγχόμενη μεταφορά ισχύος μεταξύ δύο buses, με όριο χωρητικότητας `p_nom`. "
        "Το χρησιμοποιούμε αντί για το 'κανονικό' `Line` του PyPSA επειδή το `Line` χρειάζεται "
        "πραγματικές ηλεκτρικές παραμέτρους (αντίσταση/επαγωγή) που δεν υπάρχουν στα διαγράμματα "
        "του ΑΔΜΗΕ — μόνο τάση και ισχύ μετασχηματιστών. Το `Link` είναι απλούστερο: απλά δεν "
        "επιτρέπει ροή πάνω από το `p_nom`."
    )
    st.code(
        'n.add(\n'
        '    "Link", (links["bus0"] + " -> " + links["bus1"]).values,\n'
        '    bus0=links["bus0"].values,\n'
        '    bus1=links["bus1"].values,\n'
        '    p_nom=links["p_nom"].values,\n'
        '    p_min_pu=-1,   # -1 = επιτρέπεται ροή ΚΑΙ προς τις δύο κατευθύνσεις\n'
        ')',
        language="python",
    )
    st.caption(
        "Χωρίς `p_min_pu=-1`, το Link θα επέτρεπε ροή μόνο από bus0 προς bus1 — σαν μονόδρομος. "
        "Μια πραγματική γραμμή μεταφοράς είναι αμφίδρομη, γι' αυτό το προσθέτουμε."
    )
    st.dataframe(network.links[["bus0", "bus1", "p_nom", "p_min_pu"]], use_container_width=True)

with tab_storage:
    if battery_mw > 0:
        st.markdown(
            "**StorageUnit** = μπαταρία (ή γενικά αποθήκευση): μπορεί είτε να *καταναλώνει* "
            "ισχύ (φορτίζει, `p<0`) είτε να *παράγει* (αποφορτίζει, `p>0`). Το `max_hours` "
            "καθορίζει τη χωρητικότητα σε MWh = `p_nom` × `max_hours`. Το "
            "`cyclic_state_of_charge=True` αναγκάζει η στάθμη στο τέλος της ημέρας να ισούται "
            "με αυτή στην αρχή — αλλιώς ο solver θα την άδειαζε τελείως την πρώτη μέρα (δεν θα "
            "υπήρχε λόγος να κρατήσει απόθεμα για 'αύριο')."
        )
        st.code(
            'n.add(\n'
            '    "StorageUnit", "Μπαταρία Ηπείρου",\n'
            '    bus="Άραχθος ΚΥΤ",\n'
            '    p_nom=battery_mw,        # μέγιστη ισχύς φόρτισης/αποφόρτισης (MW)\n'
            '    max_hours=4,             # χωρητικότητα = 4 × p_nom MWh\n'
            '    cyclic_state_of_charge=True,\n'
            '    efficiency_store=0.95, efficiency_dispatch=0.95,   # 5% απώλειες ανά κατεύθυνση\n'
            ')',
            language="python",
        )
        st.caption("Στάθμη φόρτισης (state of charge) στη διάρκεια της ημέρας:")
        st.line_chart(network.storage_units_t.state_of_charge)
        st.caption("Ισχύς μπαταρίας (θετικό = αποφόρτιση/τροφοδοτεί το δίκτυο, αρνητικό = φόρτιση):")
        st.line_chart(network.storage_units_t.p)
    else:
        st.info(
            "Δεν έχεις προσθέσει μπαταρία (slider 'Ισχύς μπαταρίας' = 0 παραπάνω). "
            "Ανέβασε το slider για να δεις εδώ πώς φορτίζει/αποφορτίζει μέσα στην ημέρα."
        )

with tab_opt:
    st.markdown(
        "**Snapshot** = μία χρονική στιγμή για την οποία λύνουμε το πρόβλημα. Από το Phase 4 "
        "έχουμε **24 snapshots** (`n.set_snapshots(range(24))`) — μία τυπική ημέρα, ώρα-ώρα, "
        "αντί για μία μόνο στιγμή. Αυτό είναι που δίνει νόημα στην αποθήκευση: μπορεί να "
        "φορτίσει σε μια ώρα και να αποφορτίσει σε άλλη. "
        "**`network.optimize()`** στήνει ένα γραμμικό πρόβλημα βελτιστοποίησης *για όλες τις "
        "ώρες μαζί*: ελαχιστοποίησε το συνολικό κόστος παραγωγής (Σ `marginal_cost` × `p`, "
        "αθροισμένο σε όλες τις ώρες), με περιορισμούς: (α) κάθε Load καλύπτεται ακριβώς σε "
        "κάθε ώρα, (β) καμία γεννήτρια/γραμμή δεν ξεπερνά το όριό της σε καμία ώρα, (γ) η "
        "μπαταρία δεν αδειάζει/γεμίζει πέρα από τη χωρητικότητά της. Το λύνει ο solver "
        "**HiGHS** (open-source)."
    )
    st.code('n.set_snapshots(range(24))\n...\nnetwork.optimize(solver_name="highs")', language="python")
    st.caption(
        "Το αποτέλεσμα φαίνεται παρακάτω. Το 'Status: Optimal' σημαίνει ότι βρέθηκε λύση που "
        "ικανοποιεί όλους τους περιορισμούς, σε όλες τις ώρες μαζί, με το ελάχιστο δυνατό κόστος."
    )

st.divider()
st.header("Βελτιστοποίηση PyPSA — μία τυπική ημέρα (24 ωριαία snapshots)")
st.caption(
    "Η ζήτηση ανά Περιφερειακή Ενότητα και το σχήμα της ημερήσιας καμπύλης είναι **εκτιμήσεις**, "
    "όχι μετρημένα στοιχεία — βλ. tab 'Load' παραπάνω."
)

network.optimize(solver_name="highs")

st.subheader("Παραγωγή ανά γεννήτρια, ώρα προς ώρα (MW)")
st.area_chart(network.generators_t.p)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Ημερήσιο ισοζύγιο (MWh)")
    total_demand = network.loads_t.p_set.sum().sum()
    total_gen = network.generators_t.p.sum().sum()
    import_energy = network.generators_t.p.get(
        "Εισαγωγές/Εξαγωγές Συστήματος", pd.Series(0, index=network.snapshots)
    ).sum()
    st.metric("Συνολική ημερήσια ζήτηση", f"{total_demand:.0f} MWh")
    st.metric("Συνολική ημερήσια παραγωγή", f"{total_gen:.0f} MWh")
    st.metric(
        "Εισαγωγές συστήματος (ημερήσιο σύνολο)",
        f"{import_energy:.0f} MWh",
        help="Άθροισμα ισχύος εισαγωγών σε όλες τις ώρες, μέσω ΚΥΤ Άραχθος",
    )

with col2:
    if battery_mw > 0:
        st.subheader("Στάθμη μπαταρίας (MWh)")
        st.line_chart(network.storage_units_t.state_of_charge)
    else:
        st.subheader("Μέγιστη ωριαία ζήτηση ανά κόμβο")
        st.bar_chart(network.loads_t.p_set.max())

with st.expander("Ροές στις γραμμές (Links), ώρα προς ώρα"):
    st.dataframe(network.links_t.p0, use_container_width=True)

with st.expander("Δεδομένα εισόδου (γεννήτριες / φορτία) — μετά τις ρυθμίσεις σεναρίου"):
    st.write("Γεννήτριες (στατικά χαρακτηριστικά)")
    st.dataframe(
        network.generators[["bus", "carrier", "p_nom", "marginal_cost"]],
        use_container_width=True,
    )
    st.write("Φορτία, ώρα προς ώρα (MW)")
    st.dataframe(network.loads_t.p_set, use_container_width=True)
