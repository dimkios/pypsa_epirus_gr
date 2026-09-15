# [Τίτλος — προσωρινός] PyPSA-Epirus: An Open, Provenance-Tracked Regional Power System Model for North-Western Greece

**Συγγραφέας/είς**: [συμπλήρωσε]
**Ίδρυμα / Affiliation**: [συμπλήρωσε]
**Στοχευόμενο συνέδριο**: [π.χ. PyPSA Meets Earth, ή energy-systems workshop — συμπλήρωσε]
**Κατάσταση**: προσχέδιο (draft) — βασισμένο στο [devplan.md](../devplan.md) και το Obsidian vault τεκμηρίωσης δεδομένων

---

## Keywords
open energy modelling, PyPSA, regional power systems, data provenance, reproducibility, Greece, Epirus, renewable energy integration

## Abstract (draft, ~220 λέξεις)

> Sub-national power system models are often built either from proprietary utility data, unavailable to researchers, or from pan-European tools such as PyPSA-Eur, whose default spatial clustering and OpenStreetMap-derived network data are too coarse or unreliable for small, data-scarce administrative regions. We present PyPSA-Epirus, an open regional power system model for the Epirus region of Greece (population ≈320,000), built entirely from public primary sources: substation topology and hydropower capacities extracted from the Greek transmission system operator's (ADMIE) Ten-Year Network Development Plan single-line diagrams; ~522 MW of installed wind and solar capacity from ADMIE's renewable-energy connection register; a demand allocation combining regional GDP (Eurostat) and population (ELSTAT) following the PyPSA-Eur methodology; and solar availability from the PVGIS satellite irradiance dataset. Every parameter in the model is tagged with a confidence level and source citation, and every data-sourcing decision — including dead ends and gaps (e.g., a real municipal consumption dataset that exists but is access-restricted) — is documented. Using a linear optimal power flow formulation over a representative 24-hour day, we show that Epirus's existing hydropower (712 MW) and renewable (522 MW) capacity substantially exceeds its estimated peak demand (~317 MW), consistent with its role as a net electricity exporter via the real Greece–Italy GRITA interconnector (500 MW), which we identify as terminating at the same substation used for system balancing in our model. We discuss the methodology's reproducibility and its limitations as a basis for future work.

---

## 1. Motivation / Introduction

- **Πρόβλημα**: Πολλά sub-national energy models είτε βασίζονται σε ιδιωτικά δεδομένα (μη αναπαραγώγιμα) είτε σε pan-European εργαλεία (π.χ. PyPSA-Eur) που δεν έχουν αρκετή χωρική ανάλυση ή αξιοπιστία δεδομένων για μικρές, data-scarce περιφέρειες.
- **Case study**: Ήπειρος, Ελλάδα — ορεινή, αραιοκατοικημένη περιφέρεια (~320.000 κάτοικοι) με σημαντική υδροηλεκτρική υποδομή αλλά ελάχιστα δημόσια διαθέσιμα δεδομένα δικτύου σε δομημένη μορφή.
- **Συνεισφορά**: (1) το πρώτο (απ' όσο γνωρίζουμε) ανοιχτό PyPSA μοντέλο για την Ήπειρο· (2) μια αναπαραγώγιμη μεθοδολογία εξαγωγής δικτύου από single-line diagrams διαχειριστή συστήματος όταν δεν υπάρχουν δομημένα open data· (3) ρητή τεκμηρίωση confidence/πηγής ανά παράμετρο ως πρακτική διαφάνειας — σπάνια σε τέτοιου είδους μοντέλα.
- Τοποθέτηση σε σχέση με το PyPSA-Eur: εξηγούμε γιατί επιλέξαμε custom μοντέλο αντί για extraction (§2.5).

## 2. Data & Methodology

### 2.1 Network topology
- Πηγή: ΑΔΜΗΕ, Δεκαετές Πρόγραμμα Ανάπτυξης Συστήματος Μεταφοράς (ΔΠΑ) 2021-2030, ενότητα single-line diagrams ("ΔΠΠ-Η").
- 17 κόμβοι (υποσταθμοί, υδροηλεκτρικοί σταθμοί, Κέντρο Υπερύψηλης Τάσης), 20 γραμμές — εξήχθησαν χειροκίνητα από τα διαγράμματα (καμία δομημένη export επιλογή δεν υπήρχε).
- 2 επιπλέον κόμβοι (Μαργαρίτι, Αμπέλια) προστέθηκαν για να χωρέσουν σημεία σύνδεσης ΑΠΕ εκτός του αρχικού συνόλου transmission-level διαγραμμάτων.

### 2.2 Generation — hydropower
- 5 πραγματικοί υδροηλεκτρικοί σταθμοί, εξαγόμενοι από τα ίδια single-line diagrams: Πουρνάρι Ι (300MW), Πηγές Αώου (210MW), Μεσοχώρα (160MW), Πουρνάρι ΙΙ (33.6MW), Λούρος (8.7MW) — **σύνολο 712.3MW**.

### 2.3 Generation — renewables
- Πηγή: ΑΔΜΗΕ, μητρώο σταθμών ΑΠΕ με προσφορά σύνδεσης/σε λειτουργία (εξαμηνιαία ενημέρωση).
- 125 σταθμοί, φιλτραρισμένοι στις 4 Περιφερειακές Ενότητες Ηπείρου, ομαδοποιημένοι ανά κόμβο σύνδεσης και κατηγορία έργου.
- **522.1 MW σύνολο**: 233.0MW αιολικά, 284.3MW φωτοβολταϊκά, 4.8MW μικρά υδροηλεκτρικά.

### 2.4 Demand
- Καμία δημόσια πηγή μετρημένης κατανάλωσης ανά περιφέρεια δεν εντοπίστηκε προσβάσιμη (η πλησιέστερη, ΔΕΔΔΗΕ ανά-δήμο στοιχεία, απαιτεί διαπιστευτήρια δήμου).
- Εκτίμηση με τη μεθοδολογία διαμοιρασμού ζήτησης του PyPSA-Eur: 60% βάσει πραγματικού ΑΕΠ ανά NUTS3 (Eurostat `nama_10r_3gdp`, 2023) + 40% βάσει πληθυσμού (ΕΛΣΤΑΤ, απογραφή 2021), επί εκτιμώμενης συνολικής αιχμής **~317MW**.
- Μεθοδολογική λεπτομέρεια: το Eurostat ενώνει τις Π.Ε. Άρτας και Πρέβεζας σε ένα NUTS3 (EL541) — το συνδυασμένο ΑΕΠ μοιράστηκε αναλογικά με πληθυσμό.

### 2.5 Γιατί όχι PyPSA-Eur
- Το προεπιλεγμένο clustered δίκτυο PyPSA-Eur δεν φτάνει σε ανάλυση περιφέρειας (η Ελλάδα συνήθως 1-4 κόμβοι συνολικά).
- Το μη-ομαδοποιημένο "base network" βασίζεται σε αυτόματη εξαγωγή από OpenStreetMap (GridKit) — τρίτου μέρους προσέγγιση με γνωστά κενά στη ΝΑ Ευρώπη, λιγότερο έγκυρη από την απευθείας πηγή (ΑΔΜΗΕ).
- Υιοθετήθηκε όμως η μεθοδολογία διαμοιρασμού ζήτησης του PyPSA-Eur (§2.4) ως best practice.

### 2.6 Weather / solar availability
- PVGIS (Ευρωπαϊκή Επιτροπή, JRC), δορυφορική βάση PVGIS-SARAH2, σύστημα 1kWp, συντεταγμένες Ιωαννίνων, έτος 2020 — ωριαίος μέσος όρος ανά ώρα ημέρας σε όλο το έτος.
- **Περιορισμός**: το ίδιο προφίλ εφαρμόζεται προσωρινά και στα αιολικά, ελλείψει πραγματικού προφίλ ανέμου (θα απαιτούσε atlite/ERA5 + λογαριασμό Copernicus CDS).

## 3. Model formulation

- PyPSA `Network` με 24 ωριαία snapshots (μία αντιπροσωπευτική ημέρα).
- Γραμμές μοντελοποιημένες ως PyPSA `Link` (αμφίδρομες, `p_min_pu=-1`) αντί για `Line` — δεν βρέθηκε δημόσια πηγή αντίστασης/επαγωγής γραμμών (πιθανό μελλοντικό βήμα, §5).
- Slack γεννήτρια εισαγωγών/εξαγωγών στο ΚΥΤ Άραχθος, p_nom=500MW — που αντιστοιχεί στην πραγματική χωρητικότητα της υποβρύχιας διασύνδεσης **GRITA Ελλάδας-Ιταλίας** (Galatina–Άραχθος, σε λειτουργία από το 2001), επιβεβαιωμένο ότι καταλήγει ακριβώς στον ίδιο κόμβο.
- Προαιρετικό `StorageUnit` (μπαταρία) στο ΚΥΤ Άραχθος, `cyclic_state_of_charge=True`, 95% απόδοση ανά κατεύθυνση.
- Επίλυση με τον open-source solver HiGHS.

## 4. Preliminary results

- Ισοζύγιο βάσης (χωρίς σενάριο): ζήτηση 317MW = παραγωγή 317MW, **μηδενικές εισαγωγές** — η Ήπειρος καλύπτει την εκτιμώμενη ζήτησή της αποκλειστικά με τοπικά υδροηλεκτρικά.
- Συνολική τοπική εγκατεστημένη ισχύς (υδροηλεκτρικά + ΑΠΕ) ≈ **1234MW**, ≈3.9× την εκτιμώμενη αιχμή ζήτησης — ποσοτική ένδειξη του ρόλου της Ηπείρου ως καθαρού εξαγωγέα ενέργειας.
- Ενδεικτικά σενάρια (sliders στην εφαρμογή): προσθήκη νέας ΑΠΕ, περιορισμός εισαγωγών, μεταβολή ζήτησης, προσθήκη αποθήκευσης — δείχνουν πότε/αν η αποθήκευση αποκτά οικονομική αξία (μόνο υπό συνδυασμό υψηλής ΑΠΕ + μειωμένης ζήτησης, δεδομένης της ευελιξίας των υπαρχόντων υδροηλεκτρικών).

## 5. Limitations & Future Work

- **Link αντί για Line**: απλοποιημένη μεταφορά ισχύος, όχι πραγματική φυσική ροή (καμία πηγή αντίστασης/επαγωγής). Προτεινόμενη λύση: τυπικός κατάλογος γραμμών PyPSA + υπολογισμένο μήκος από συντεταγμένες.
- **Ζήτηση**: εκτίμηση (ΑΕΠ+πληθυσμός), όχι μετρημένη — πραγματική πηγή (ΔΕΔΔΗΕ) υπάρχει αλλά είναι access-restricted σε επίπεδο δήμου.
- **Προφίλ ανέμου**: υποκατάσταση με το ηλιακό προφίλ PVGIS, ελλείψει atlite/ERA5.
- **Χρονική ανάλυση**: μία αντιπροσωπευτική ημέρα (24 snapshots), όχι πλήρες έτος.
- **Δύο νέοι κόμβοι** (Μαργαρίτι, Αμπέλια) με τοπολογικά συμπερασμένες (όχι επιβεβαιωμένες σε single-line diagram) συνδέσεις.
- Μελλοντική επέκταση: επίπεδο χώρας ("PyPSA GREECE"), πλήρες power flow, πραγματικό προφίλ ανέμου.

## 6. Conclusion
[Να γραφτεί μετά την πρώτη ανατροφοδότηση από το συνέδριο]

## Data & Code Availability
Πλήρης κώδικας, δεδομένα και τεκμηρίωση πηγών: https://github.com/dimkios/pypsa_epirus_gr (README.md, `data/processed/`, `devplan.md`)

## References [προς συμπλήρωση]
- PyPSA: Brown, Hörsch, Schlachtberger (2018)
- PyPSA-Eur: Hörsch et al. (2018), τεκμηρίωση methodology διαμοιρασμού ζήτησης
- ADMIE, Δεκαετές Πρόγραμμα Ανάπτυξης Συστήματος Μεταφοράς
- Eurostat, `nama_10r_3gdp`
- PVGIS (JRC), PVGIS-SARAH2
- ΕΛΣΤΑΤ, Απογραφή Πληθυσμού 2021

---

## Σημειώσεις προσχεδίου (να αφαιρεθούν πριν την υποβολή)
- Όλα τα νούμερα επιβεβαιώθηκαν από τα τρέχοντα `data/processed/*.csv` στις 2026-09-15.
- Χρειάζεται: τίτλος συνεδρίου/deadline, ονόματα συγγραφέων/ίδρυμα, πλήρεις βιβλιογραφικές αναφορές σε σωστό format, πιθανό σχήμα/εικόνα του δικτύου (screenshot από την εφαρμογή), ακριβές word/page limit του συνεδρίου για προσαρμογή μήκους.
