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
st.header("Βελτιστοποίηση PyPSA (μία στιγμή - single snapshot)")
st.caption(
    "Η ζήτηση ανά Περιφερειακή Ενότητα είναι **εκτίμηση** (αναλογία πληθυσμού 2021 επί εθνικής "
    "αιχμής), όχι μετρημένα στοιχεία — βλ. πίνακα φορτίων παρακάτω."
)

network = build_network()
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
