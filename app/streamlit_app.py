import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pypsa_model import build_network

st.set_page_config(page_title="PyPSA Epirus GR", layout="wide")

st.title("Δίκτυο Ηλεκτρικής Ενέργειας Ηπείρου")
st.caption(
    "Phase 2 — πραγματική τοπολογία & γεννήτριες ΑΔΜΗΕ, πρώτο μοντέλο βελτιστοποίησης PyPSA."
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

network = build_network()

st.header("📚 Πώς φτιάχνεται το μοντέλο PyPSA (εκπαιδευτικό)")
st.caption(
    "Παρένθεση πριν τη βελτιστοποίηση: τι είναι κάθε 'component' του PyPSA, ο πραγματικός "
    "κώδικας που το φτιάχνει σε αυτό το project, και τα πραγματικά δεδομένα που προκύπτουν."
)

tab_bus, tab_gen, tab_load, tab_link, tab_opt = st.tabs(
    ["Bus", "Generator", "Load", "Link", "Snapshot & optimize()"]
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
        "χρησιμοποιείται μόνο αν τα υδροηλεκτρικά δεν επαρκούν."
    )
    st.dataframe(network.generators[["bus", "carrier", "p_nom", "marginal_cost"]], use_container_width=True)

with tab_load:
    st.markdown(
        "**Load** = κατανάλωση συνδεδεμένη σε ένα bus. Το `p_set` είναι η ζήτηση που *πρέπει* "
        "να καλυφθεί — ο solver δεν έχει επιλογή εδώ, είναι περιορισμός (constraint), όχι απόφαση."
    )
    st.code(
        'n.add(\n'
        '    "Load", loads["name"].values,\n'
        '    bus=loads["bus"].values,\n'
        '    p_set=loads["p_set"].values,   # ζήτηση σε MW\n'
        ')',
        language="python",
    )
    st.caption(
        "Οι 4 τιμές `p_set` εδώ είναι **εκτιμήσεις** (πληθυσμιακή αναλογία), όχι πραγματικές "
        "μετρήσεις κατανάλωσης — βλ. [[Κενό - Ζήτηση ανά περιφέρεια]] στο Obsidian."
    )
    st.dataframe(network.loads[["bus", "p_set"]], use_container_width=True)

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

with tab_opt:
    st.markdown(
        "**Snapshot** = μία χρονική στιγμή για την οποία λύνουμε το πρόβλημα (εδώ έχουμε μόνο "
        "μία, `\"now\"` — καμία χρονοσειρά ακόμα, αυτό έρχεται σε επόμενη φάση). "
        "**`network.optimize()`** στήνει ένα γραμμικό πρόβλημα βελτιστοποίησης: "
        "*ελαχιστοποίησε* το συνολικό κόστος παραγωγής (Σ `marginal_cost` × `p`), "
        "με περιορισμούς: (α) κάθε Load καλύπτεται ακριβώς, (β) καμία γεννήτρια δεν ξεπερνά "
        "το `p_nom` της, (γ) καμία γραμμή/Link δεν ξεπερνά τη χωρητικότητά της. Το λύνει ο "
        "solver **HiGHS** (open-source)."
    )
    st.code('network.optimize(solver_name="highs")', language="python")
    st.caption(
        "Το αποτέλεσμα φαίνεται παρακάτω. Το 'Status: Optimal' σημαίνει ότι βρέθηκε λύση που "
        "ικανοποιεί όλους τους περιορισμούς με το ελάχιστο δυνατό κόστος."
    )

st.divider()
st.header("Βελτιστοποίηση PyPSA (μία στιγμή - single snapshot)")
st.caption(
    "Η ζήτηση ανά Περιφερειακή Ενότητα είναι **εκτίμηση** (αναλογία πληθυσμού 2021 επί εθνικής "
    "αιχμής), όχι μετρημένα στοιχεία — βλ. πίνακα φορτίων παρακάτω."
)

network.optimize(solver_name="highs")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Παραγωγή ανά γεννήτρια")
    dispatch = network.generators_t.p.iloc[0].rename("Παραγωγή (MW)")
    st.bar_chart(dispatch)

with col2:
    st.subheader("Ισοζύγιο")
    total_demand = network.loads["p_set"].sum()
    total_gen = network.generators_t.p.iloc[0].sum()
    st.metric("Συνολική ζήτηση", f"{total_demand:.1f} MW")
    st.metric("Συνολική παραγωγή", f"{total_gen:.1f} MW")
    st.metric(
        "Εισαγωγές/Εξαγωγές συστήματος",
        f"{network.generators_t.p.iloc[0].get('Εισαγωγές/Εξαγωγές Συστήματος', 0):.1f} MW",
        help="Θετικό = εισαγωγή ισχύος από το υπόλοιπο σύστημα μέσω ΚΥΤ Άραχθος",
    )

with st.expander("Ροές στις γραμμές (Links)"):
    flows = network.links_t.p0.iloc[0].rename("Ροή (MW, θετικό = bus0→bus1)")
    st.dataframe(flows, use_container_width=True)

with st.expander("Δεδομένα εισόδου (γεννήτριες / φορτία)"):
    st.write("Γεννήτριες")
    st.dataframe(pd.read_csv("data/processed/generators_epirus.csv"), use_container_width=True)
    st.write("Φορτία")
    st.dataframe(pd.read_csv("data/processed/loads_epirus.csv"), use_container_width=True)
