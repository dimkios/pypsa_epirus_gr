import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="PyPSA Epirus GR", layout="wide")

st.title("Δίκτυο Ηλεκτρικής Ενέργειας Ηπείρου")
st.caption(
    "Phase 1 — πραγματικοί υποσταθμοί/σταθμοί ΑΔΜΗΕ, χωρίς μοντελοποίηση PyPSA ακόμα."
)

buses = pd.read_csv("data/processed/buses_epirus.csv")

TYPE_LABELS = {
    "substation": "Υποσταθμός",
    "hydro": "Υδροηλεκτρικός Σταθμός",
    "kyt": "Κέντρο Υπερύψηλης Τάσης",
}
buses["Τύπος"] = buses["type"].map(TYPE_LABELS)

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
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

st.plotly_chart(fig, use_container_width=True)

with st.expander("Πίνακας κόμβων"):
    st.dataframe(
        buses[["name", "regional_unit", "Τύπος", "lat", "lon", "confidence", "source_note"]],
        use_container_width=True,
    )

st.caption(
    "Πηγή: ΑΔΜΗΕ, Δεκαετές Πρόγραμμα Ανάπτυξης Συστήματος Μεταφοράς 2021-2030. "
    "Οι συντεταγμένες με confidence='approximate' προέκυψαν από ανάγνωση του γεωγραφικού "
    "χάρτη του ΑΔΜΗΕ, όχι από επίσημες δημοσιευμένες συντεταγμένες."
)
