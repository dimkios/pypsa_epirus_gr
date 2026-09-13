from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pypsa_model import IMPORT_GENERATOR, build_network

st.set_page_config(page_title="PyPSA Epirus GR", layout="wide")

_GREEK_MONTHS = [
    "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
    "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
]
_today = date.today()
_today_str = f"{_today.day} {_GREEK_MONTHS[_today.month - 1]} {_today.year}"

_header_col1, _header_col2 = st.columns([1, 3])
with _header_col1:
    st.image("data/logo.png", width=300)
with _header_col2:
    st.markdown(
        f"<div style='text-align: right; padding-top: 0.5rem;'>{_today_str}</div>",
        unsafe_allow_html=True,
    )
st.markdown(
    "<hr style='margin-top: -1rem; margin-bottom: 0; padding: 0;'>", unsafe_allow_html=True
)

st.caption(
    "Εφαρμογή μοντελοποίησης και βελτιστοποίησης του δικτύου ηλεκτρικής ενέργειας της "
    "Περιφέρειας Ηπείρου (Ελλάδα), με χρήση PyPSA."
)

buses = pd.read_csv("data/processed/buses_epirus.csv")
links = pd.read_csv("data/processed/links_epirus.csv")
res_existing = pd.read_csv("data/processed/res_existing_epirus.csv")

TYPE_LABELS = {
    "substation": "Υποσταθμός",
    "hydro": "Υδροηλεκτρικός Σταθμός",
    "kyt": "Κέντρο Υπερύψηλης Τάσης",
}
buses["Τύπος"] = buses["type"].map(TYPE_LABELS)


def _res_summary(bus_name: str) -> str:
    rows = res_existing[res_existing["bus"] == bus_name]
    if rows.empty:
        return "—"
    parts = [f"{r['p_nom']:.1f}MW {r['category']}" for _, r in rows.iterrows()]
    return f"{rows['p_nom'].sum():.1f}MW ΑΠΕ ({', '.join(parts)})"


buses["ΑΠΕ"] = buses["name"].map(_res_summary)
bus_coords = buses.set_index("name")[["lat", "lon"]]

fig = px.scatter_map(
    buses,
    lat="lat",
    lon="lon",
    color="regional_unit",
    hover_name="name",
    hover_data={"lat": False, "lon": False, "confidence": True, "Τύπος": True, "ΑΠΕ": True},
    zoom=7.4,
    center={"lat": 39.55, "lon": 20.85},
    height=650,
)
fig.update_traces(marker={"size": 18})

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
        buses[["name", "regional_unit", "Τύπος", "ΑΠΕ", "lat", "lon", "confidence", "source_note"]],
        use_container_width=True,
    )

st.caption(
    "Πηγή τοπολογίας: ΑΔΜΗΕ, Δεκαετές Πρόγραμμα Ανάπτυξης Συστήματος Μεταφοράς 2021-2030 "
    "(κόμβοι, γραμμές, ισχύς υδροηλεκτρικών από τα single-line diagrams). "
    "Πηγή ΑΠΕ: ΑΔΜΗΕ, αρχείο σταθμών ΑΠΕ με προσφορά σύνδεσης/σε λειτουργία, Απρίλιος 2026 "
    "(και οι 2 νέοι κόμβοι Μαργαρίτι/Αμπέλια προστέθηκαν γι' αυτό). "
    "Οι συντεταγμένες με confidence='approximate' προέκυψαν από ανάγνωση γεωγραφικού χάρτη ή "
    "κατά προσέγγιση από περιγραφή τοποθεσίας, όχι από επίσημες δημοσιευμένες συντεταγμένες."
)

st.divider()
st.header("Σενάριο")
st.caption(
    "Phase 4 — μία τυπική ημέρα (24 ωριαία snapshots) αντί για μία στιγμή. "
    "Πειραματίσου με παραμέτρους και δες πώς αλλάζει το ημερήσιο ισοζύγιο."
)

col_res, col_restype, col_import, col_demand, col_batt = st.columns(5)
with col_res:
    new_res_mw = st.slider(
        "Νέα ισχύς ΑΠΕ (MW)",
        min_value=0,
        max_value=500,
        value=0,
        step=10,
        help=(
            "ΕΠΙΠΛΕΟΝ ισχύς πάνω από την ήδη υπαρκτή (~522MW, βλ. tab 'Generator'). Κατανέμεται "
            "αναλογικά με τον πληθυσμό στους 4 κόμβους-φορτία."
        ),
    )
with col_restype:
    new_res_type = st.selectbox(
        "Τύπος νέας ΑΠΕ",
        options=["Φωτοβολταϊκά", "Αιολικά"],
        help=(
            "Επηρεάζει μόνο την ετικέτα/carrier της γεννήτριας. Η διαθεσιμότητά της (`p_max_pu`) "
            "ακολουθεί πάντα το ίδιο πραγματικό ηλιακό προφίλ PVGIS (Ιωάννινα, 2020) — δεν έχουμε "
            "ακόμα πραγματικό προφίλ ανέμου, οπότε αν επιλέξεις 'Αιολικά' θεωρείται απλοποιητικά "
            "ότι έχει την ίδια διαθεσιμότητα με τα φωτοβολταϊκά."
        ),
    )
with col_import:
    import_limit_mw = st.slider(
        "Μέγιστες επιτρεπτές εισαγωγές (MW)",
        min_value=0,
        max_value=1000,
        value=500,
        step=50,
        help=(
            "Προεπιλογή 500MW = η πραγματική χωρητικότητα της διασύνδεσης GRITA Ελλάδας-Ιταλίας "
            "(Galatina-Άραχθος, 2001), που καταλήγει στο ΚΥΤ Άραχθος. Πάνω από 500MW εξομοιώνει "
            "υποθετική μελλοντική ενίσχυση (π.χ. GRITA 2, 1000MW, καταλήγει όμως στη Θεσπρωτία "
            "στην πραγματικότητα - δεν είναι ακόμα στο μοντέλο μας). 0 = πλήρης ενεργειακή "
            "ανεξαρτησία Ηπείρου."
        ),
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
    new_res_type=new_res_type,
    import_limit_mw=import_limit_mw,
    demand_change_pct=demand_change_pct,
    battery_mw=battery_mw,
)

# Λύνουμε ΕΔΩ, πριν το εκπαιδευτικό panel — tabs όπως το StorageUnit δείχνουν αποτελέσματα
# βελτιστοποίησης (state_of_charge, p), που δεν υπάρχουν αν δεν έχει ήδη τρέξει το optimize().
opt_status, opt_condition = network.optimize(solver_name="highs")

st.divider()
st.header("📚 Πώς φτιάχνεται το μοντέλο PyPSA")
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
        "Στο δικό μας δίκτυο: 5 πραγματικά υδροηλεκτρικά (χαμηλό marginal_cost=5) + 1 γεννήτρια "
        "εισαγωγών/εξαγωγών (marginal_cost=60 εκτίμηση, χρησιμοποιείται μόνο αν όλα τα άλλα δεν "
        "επαρκούν) με **πραγματικό p_nom=500MW** — η πραγματική χωρητικότητα της διασύνδεσης "
        "**GRITA Ελλάδας-Ιταλίας** (Galatina-Άραχθος, υποβρύχιο 400kV, από το 2001), που τυχαίνει "
        "να καταλήγει ακριβώς στο ΚΥΤ Άραχθος — αντιπροσωπεύει επίσης γενικά τη σύνδεση με το "
        "υπόλοιπο ελληνικό σύστημα + **11 γεννήτριες 'ΑΠΕ ... (υπάρχουσα)'** που αναπαριστούν την "
        "ήδη εγκατεστημένη, πραγματική ισχύ ΑΠΕ Ηπείρου (~522MW, πηγή: αρχείο ΑΔΜΗΕ Απρ.2026), "
        "**σπασμένη ανά τύπο** — δες τη στήλη `carrier`: `solar_existing` (Φωτοβολταϊκά, "
        "284MW), `wind_existing` (Αιολικά, 233MW), `small_hydro_existing` (Μικρά "
        "Υδροηλεκτρικά, 4.8MW) — πάντα ενεργές, όχι εξαρτημένες από το slider. Αν πρόσθεσες κι "
        "άλλα παραπάνω στο 'Σενάριο', εμφανίζεται κι ένα ακόμα σετ γεννητριών 'ΑΠΕ ... (νέα)' με "
        "τον τύπο που επέλεξες. Όλες οι ΑΠΕ έχουν "
        "marginal_cost=0 (προτιμώνται πρώτες από τον solver, πριν καν τα υδροηλεκτρικά) και "
        "διαθεσιμότητα (`p_max_pu`) από **πραγματικά δεδομένα ηλιακής ακτινοβολίας PVGIS** "
        "(Ιωάννινα, μέσος όρος έτους 2020) — απλοποίηση: το ίδιο προφίλ εφαρμόζεται και στα "
        "αιολικά, ελλείψει πραγματικού προφίλ ανέμου ακόμα."
    )
    st.dataframe(network.generators[["bus", "carrier", "p_nom", "marginal_cost"]], use_container_width=True)
    st.caption("Ωριαία διαθεσιμότητα ΑΠΕ (p_max_pu) — πραγματικό προφίλ PVGIS:")
    res_cols = [c for c in network.generators_t.p_max_pu.columns if "ΑΠΕ" in c]
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
        "Οι τιμές αιχμής (`peak`) είναι **εκτιμήσεις**, όχι πραγματικές μετρήσεις κατανάλωσης — "
        "μεθοδολογία pypsa-eur: 60% βάσει πραγματικού ΑΕΠ ανά NUTS3 (Eurostat) + 40% βάσει "
        "πληθυσμού (ΕΛΣΤΑΤ 2021), επί εκτιμώμενης συνολικής αιχμής Ηπείρου ~317MW. Η πραγματική "
        "πηγή μέτρησης (ΔΕΔΔΗΕ ανά Δήμο) υπάρχει αλλά απαιτεί login δήμων — βλ. [[Κενό - Ζήτηση "
        "ανά περιφέρεια]] στο Obsidian. Το *σχήμα* της καμπύλης (DEMAND_PROFILE) παραμένει "
        "παραδοχή, όχι μετρημένο προφίλ Ηπείρου."
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
    st.code(
        'n.set_snapshots(range(24))\n'
        '...\n'
        'status, condition = network.optimize(solver_name="highs")',
        language="python",
    )
    st.caption(
        "Το `network.optimize()` επιστρέφει `(status, condition)`. `condition == 'optimal'` "
        "σημαίνει ότι βρέθηκε λύση που ικανοποιεί όλους τους περιορισμούς, σε όλες τις ώρες "
        "μαζί, με το ελάχιστο δυνατό κόστος. Το αποτέλεσμα εμφανίζεται παρακάτω, στην κορυφή "
        "της ενότητας 'Βελτιστοποίηση PyPSA'."
    )

st.divider()
st.header("Βελτιστοποίηση PyPSA — μία τυπική ημέρα (24 ωριαία snapshots)")
st.caption(
    "Η ζήτηση ανά Περιφερειακή Ενότητα και το σχήμα της ημερήσιας καμπύλης είναι **εκτιμήσεις**, "
    "όχι μετρημένα στοιχεία — βλ. tab 'Load' παραπάνω."
)

if opt_status == "ok" and opt_condition == "optimal":
    st.success(f"Status: {opt_status} — Termination condition: {opt_condition}")
else:
    st.error(
        f"Status: {opt_status} — Termination condition: {opt_condition} "
        "(κάτι δεν πήγε καλά — πιθανόν το σενάριο έκανε το πρόβλημα ανέφικτο, π.χ. πολύ "
        "χαμηλό όριο εισαγωγών μαζί με πολύ υψηλή ζήτηση)"
    )

st.subheader("Παραγωγή ανά γεννήτρια, ώρα προς ώρα (MW)")
st.area_chart(network.generators_t.p)

st.subheader("Ζήτηση: ποιος τύπος πηγής την κάλυψε, ώρα προς ώρα")
st.caption(
    "Συνολική σύνθεση παραγωγής **όλου του συστήματος** ανά τύπο πηγής — όχι ανά κόμβο. Σε "
    "ένα δίκτυο με Links η ισχύς 'αναμειγνύεται' στις γραμμές, οπότε δεν μπορούμε να πούμε με "
    "μαθηματική ακρίβεια ποιο συγκεκριμένο MW σε ποιο φορτίο ήρθε από ποια ακριβώς γεννήτρια — "
    "αυτό το γράφημα δείχνει τη ρεαλιστική εικόνα: τη συνολική σύνθεση παραγωγής τη στιγμή που "
    "καλύπτεται η συνολική ζήτηση. Η διακεκομμένη μαύρη γραμμή είναι η συνολική ζήτηση — όπου η "
    "στοιβαγμένη περιοχή φτάνει τη γραμμή, η ζήτηση καλύφθηκε πλήρως. **Αν έχεις προσθέσει "
    "μπαταρία**, οι δύο δεν ταυτίζονται πάντα: όταν η μπαταρία φορτίζει, η παραγωγή φαίνεται "
    "*πάνω* από τη ζήτηση (το πλεόνασμα αποθηκεύεται, δεν καταναλώνεται)· όταν αποφορτίζει, η "
    "παραγωγή γεννητριών φαίνεται *κάτω* από τη ζήτηση (τη διαφορά την καλύπτει η μπαταρία, "
    "που δεν είναι Generator — δες το ξεχωριστό γράφημα στο tab 'StorageUnit')."
)
CARRIER_GROUPS = {
    "hydro": "Υδροηλεκτρικά (μεγάλα)",
    "small_hydro_existing": "Μικρά Υδροηλεκτρικά",
    "wind_existing": "Αιολικά",
    "wind_new": "Αιολικά",
    "solar_existing": "Φωτοβολταϊκά",
    "solar_new": "Φωτοβολταϊκά",
    "grid_import": "Εισαγωγές (Σύστημα+GRITA)",
}
gen_group = network.generators["carrier"].map(CARRIER_GROUPS)
gen_by_group = network.generators_t.p.T.groupby(gen_group).sum().T

fig_mix = go.Figure()
for col in gen_by_group.columns:
    fig_mix.add_trace(
        go.Scatter(
            x=list(network.snapshots),
            y=gen_by_group[col],
            name=col,
            stackgroup="gen",
            mode="lines",
        )
    )
fig_mix.add_trace(
    go.Scatter(
        x=list(network.snapshots),
        y=network.loads_t.p_set.sum(axis=1),
        name="Συνολική ζήτηση",
        mode="lines",
        line={"color": "black", "width": 2, "dash": "dash"},
    )
)
fig_mix.update_layout(
    xaxis_title="Ώρα", yaxis_title="MW", height=420, margin={"t": 20, "b": 0}
)
st.plotly_chart(fig_mix, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Ημερήσιο ισοζύγιο (MWh)")
    total_demand = network.loads_t.p_set.sum().sum()
    total_gen = network.generators_t.p.sum().sum()
    import_energy = network.generators_t.p.get(
        IMPORT_GENERATOR, pd.Series(0, index=network.snapshots)
    ).sum()
    st.metric("Συνολική ημερήσια ζήτηση", f"{total_demand:.0f} MWh")
    st.metric("Συνολική ημερήσια παραγωγή", f"{total_gen:.0f} MWh")
    st.metric(
        "Εισαγωγές συστήματος (ημερήσιο σύνολο)",
        f"{import_energy:.0f} MWh",
        help=(
            "Άθροισμα ισχύος εισαγωγών σε όλες τις ώρες, μέσω ΚΥΤ Άραχθος — εκεί καταλήγει "
            "πραγματικά η διασύνδεση GRITA Ελλάδας-Ιταλίας (Galatina-Άραχθος, υποβρύχιο "
            "καλώδιο 400kV, 500MW, σε λειτουργία από το 2001). Ο κόμβος συνδέει επίσης την "
            "Ήπειρο με το υπόλοιπο ελληνικό σύστημα, όχι μόνο με την Ιταλία."
        ),
    )

with col2:
    if battery_mw > 0:
        st.subheader("Στάθμη μπαταρίας (MWh)")
        st.line_chart(network.storage_units_t.state_of_charge)
    else:
        st.subheader("Μέγιστη ωριαία ζήτηση ανά κόμβο")
        st.bar_chart(network.loads_t.p_set.max())

with st.expander("Ροές στις γραμμές (Links), ώρα προς ώρα"):
    st.caption(
        "Κάθε στήλη είναι μία γραμμή (`bus0 -> bus1`), κάθε γραμμή του πίνακα μία ώρα (0-23). "
        "Οι τιμές είναι σε MW: **θετικό** = ροή ισχύος από το `bus0` προς το `bus1`, "
        "**αρνητικό** = αντίστροφη ροή (από `bus1` προς `bus0`) — θυμήσου ότι επιτρέψαμε "
        "αμφίδρομη ροή με `p_min_pu=-1` (βλ. tab 'Link' παραπάνω). Αν μια τιμή πλησιάζει το "
        "`p_nom` της αντίστοιχης γραμμής (βλ. tab 'Link' για τα όρια), η γραμμή είναι **κοντά "
        "στο μέγιστο της χωρητικότητάς της** εκείνη την ώρα."
    )
    st.dataframe(network.links_t.p0, use_container_width=True)

with st.expander("Δεδομένα εισόδου (γεννήτριες / φορτία) — μετά τις ρυθμίσεις σεναρίου"):
    st.caption(
        "Αυτό είναι ακριβώς ό,τι \"βλέπει\" ο solver όταν τρέχει το `optimize()` — δηλαδή τα "
        "δεδομένα του δικτύου **μετά** την εφαρμογή των sliders του 'Σενάριο' παραπάνω (νέα "
        "ΑΠΕ, όριο εισαγωγών, μεταβολή ζήτησης). Χρήσιμο για να επαληθεύσεις ότι το σενάριο "
        "που έστησες εφαρμόστηκε όπως το περίμενες, πριν εμπιστευτείς το αποτέλεσμα."
    )
    st.write("Γεννήτριες (στατικά χαρακτηριστικά: ισχύς, κόστος, τύπος — ίδια σε όλες τις ώρες)")
    st.dataframe(
        network.generators[["bus", "carrier", "p_nom", "marginal_cost"]],
        use_container_width=True,
    )
    st.write("Φορτία, ώρα προς ώρα (MW) — η ζήτηση που *πρέπει* να καλυφθεί σε κάθε κόμβο/ώρα")
    st.caption(
        "Για το *ποιος τύπος πηγής* κάλυψε αυτή τη ζήτηση (σε επίπεδο συστήματος, όχι ανά "
        "κόμβο — δες γιατί παραπάνω), βλ. το γράφημα 'Ζήτηση: ποιος τύπος πηγής την κάλυψε' "
        "στην κορυφή της σελίδας."
    )
    st.dataframe(network.loads_t.p_set, use_container_width=True)
