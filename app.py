import datetime
import io
import sqlite3
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Gestion des Titres & Chèques",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS for Modern UI / Mise en page
st.markdown(
    """
<style>
    /* Global Styles */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Card Styles */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        color: white;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }
    
    /* Form Header Styling */
    .stForm {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Buttons Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 3. Database Setup (SQLite)
def init_db():
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS titres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            reference TEXT,
            client TEXT,
            banque TEXT,
            montant REAL,
            echeance TEXT,
            statut TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


def load_data():
    conn = sqlite3.connect("data_gestion.db")
    df = pd.read_sql_query("SELECT * FROM titres", conn)
    conn.close()
    return df


def insert_data(titre_type, ref, client, bank, amount, due_date, status):
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO titres (type, reference, client, banque, montant, echeance, statut)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (titre_type, ref, client, bank, amount, str(due_date), status),
    )
    conn.commit()
    conn.close()


def update_status(item_id, new_status):
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute(
        "UPDATE titres SET statut = ? WHERE id = ?", (new_status, item_id)
    )
    conn.commit()
    conn.close()


# 4. Login Authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Connexion / Login</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur / Username")
            password = st.text_input("Mot de passe / Password", type="password")
            submit_login = st.form_submit_button("Se connecter / Log In", use_container_width=True)
            if submit_login:
                if username == "admin" and password == "admin123":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Identifiants incorrects / Invalid credentials")
    st.stop()

# ----------------------------------------------------
# Translations (French / English)
# ----------------------------------------------------
TEXTS = {
    "Français": {
        "title": "📊 Plateforme de Gestion des Chèques & Effets",
        "menu_dash": "Tableau de Bord",
        "menu_saisie": "Saisie & Modification",
        "menu_remise": "Bordereau de Remise",
        "menu_impayes": "Suivi des Impayés",
        "total_portefeuille": "En Portefeuille",
        "total_remis": "Remis en Banque",
        "total_paye": "Payés / Encaissés",
        "total_impaye": "Impayés",
        "alerts_title": "⚠️ Échéances Proches (7 prochains jours)",
        "type": "Type de Titre",
        "ref": "N° Référence / Chèque",
        "client": "Client / Tireur",
        "bank": "Banque",
        "amount": "Montant (DH)",
        "due_date": "Date d'Échéance",
        "status": "Statut",
        "save_btn": "Enregistrer le Titre",
        "update_btn": "Mettre à jour",
        "search_label": "Rechercher (Référence ou Client)",
        "filter_bank": "Filtrer par Banque",
        "filter_status": "Filtrer par Statut",
        "all": "Tous",
        "export_excel": "Exporter Excel",
        "export_pdf": "Générer PDF",
        "logout": "Déconnexion",
        "no_data": "Aucune donnée disponible.",
    },
    "English": {
        "title": "📊 Check & Bill Management Platform",
        "menu_dash": "Dashboard",
        "menu_saisie": "Data Entry & Edit",
        "menu_remise": "Remittance Slip",
        "menu_impayes": "Unpaid Tracking",
        "total_portefeuille": "Portfolio Total",
        "total_remis": "Deposited Total",
        "total_paye": "Paid Total",
        "total_impaye": "Unpaid Total",
        "alerts_title": "⚠️ Upcoming Due Dates (Next 7 days)",
        "type": "Instrument Type",
        "ref": "Reference / Check N°",
        "client": "Client / Issuer",
        "bank": "Bank",
        "amount": "Amount (DH)",
        "due_date": "Due Date",
        "status": "Status",
        "save_btn": "Save Record",
        "update_btn": "Update",
        "search_label": "Search (Reference or Client)",
        "filter_bank": "Filter by Bank",
        "filter_status": "Filter by Status",
        "all": "All",
        "export_excel": "Export Excel",
        "export_pdf": "Generate PDF",
        "logout": "Log Out",
        "no_data": "No data available.",
    },
}

# Sidebar Controls
st.sidebar.title("⚙️ Navigation")
lang = st.sidebar.selectbox("🌐 Language / Langue", ["Français", "English"])
t = TEXTS[lang]

menu = st.sidebar.radio(
    "Menu",
    [
        t["menu_dash"],
        t["menu_saisie"],
        t["menu_remise"],
        t["menu_impayes"],
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button(f"🔴 {t['logout']}", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()

st.title(t["title"])
st.markdown("---")

df = load_data()

# ----------------------------------------------------
# 1. Tableau de Bord / Dashboard
# ----------------------------------------------------
if menu == t["menu_dash"]:
    st.subheader(t["menu_dash"])

    # KPIs Summary
    c1, c2, c3, c4 = st.columns(4)
    v_portefeuille = (
        df[df["statut"] == "En portefeuille"]["montant"].sum() if not df.empty else 0
    )
    v_remis = (
        df[df["statut"] == "Remis à la banque"]["montant"].sum() if not df.empty else 0
    )
    v_paye = df[df["statut"] == "Payé"]["montant"].sum() if not df.empty else 0
    v_impaye = (
        df[df["statut"] == "Impayé"]["montant"].sum() if not df.empty else 0
    )

    c1.metric(t["total_portefeuille"], f"{v_portefeuille:,.2f} DH")
    c2.metric(t["total_remis"], f"{v_remis:,.2f} DH")
    c3.metric(t["total_paye"], f"{v_paye:,.2f} DH")
    c4.metric(t["total_impaye"], f"{v_impaye:,.2f} DH")

    st.markdown("<br>", unsafe_allow_html=True)

    # Alerts Section (7 days ahead)
    st.subheader(t["alerts_title"])
    if not df.empty:
        df["echeance_dt"] = pd.to_datetime(df["echeance"])
        today = pd.Timestamp(datetime.date.today())
        next_week = today + pd.Timedelta(days=7)

        upcoming = df[
            (df["echeance_dt"] >= today)
            & (df["echeance_dt"] <= next_week)
            & (df["statut"] == "En portefeuille")
        ]

        if upcoming.empty:
            st.info("Aucune échéance dans les 7 prochains jours.")
        else:
            st.warning(
                f"{len(upcoming)} titre(s) en portefeuille arrivent à échéance sous peu:"
            )
            st.dataframe(
                upcoming[
                    ["id", "type", "reference", "client", "montant", "echeance"]
                ],
                use_container_width=True,
            )
    else:
        st.info(t["no_data"])

# ----------------------------------------------------
# 2. Saisie, Recherche & Modification
# ----------------------------------------------------
elif menu == t["menu_saisie"]:
    st.subheader(t["menu_saisie"])

    with st.expander("➕ Ajouter un nouveau titre", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                titre_type = st.selectbox(
                    t["type"], ["Chèque", "Effet", "Versement"]
                )
                ref = st.text_input(t["ref"])
                client = st.text_input(t["client"])
                bank = st.selectbox(
                    t["bank"],
                    [
                        "Attijariwafa Bank",
                        "Banque Populaire",
                        "BMCE / Bank of Africa",
                        "CIH Bank",
                        "Société Générale",
                        "BMCI",
                        "Crédit du Maroc",
                        "Autre",
                    ],
                )
            with col2:
                amount = st.number_input(
                    t["amount"], min_value=0.0, step=100.0, format="%.2f"
                )
                due_date = st.date_input(t["due_date"], datetime.date.today())
                status = st.selectbox(
                    t["status"],
                    ["En portefeuille", "Remis à la banque", "Payé", "Impayé"],
                )

            if st.form_submit_button(t["save_btn"], use_container_width=True):
                insert_data(
                    titre_type, ref, client, bank, amount, due_date, status
                )
                st.success("Enregistré avec succès!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtres & Recherche
    st.subheader("🔍 Recherche & Modification")
    if not df.empty:
        col_s, col_b, col_st = st.columns(3)
        with col_s:
            search_query = st.text_input(t["search_label"])
        with col_b:
            banks = [t["all"]] + list(df["banque"].unique())
            selected_bank = st.selectbox(t["filter_bank"], banks)
        with col_st:
            statuses = [t["all"]] + list(df["statut"].unique())
            selected_status = st.selectbox(t["filter_status"], statuses)

        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df["reference"]
                .str.contains(search_query, case=False, na=False)
                | filtered_df["client"].str.contains(
                    search_query, case=False, na=False
                )
            ]
        if selected_bank != t["all"]:
            filtered_df = filtered_df[filtered_df["banque"] == selected_bank]
        if selected_status != t["all"]:
            filtered_df = filtered_df[filtered_df["statut"] == selected_status]

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("##### ✏️ Changer le statut d'un titre")
        col_id, col_new_st, col_act = st.columns([1, 2, 1])
        with col_id:
            target_id = st.number_input(
                "ID du titre", min_value=1, step=1, value=1
            )
        with col_new_st:
            new_st = st.selectbox(
                "Nouveau Statut",
                ["En portefeuille", "Remis à la banque", "Payé", "Impayé"],
                key="update_st_val",
            )
        with col_act:
            st.write("")
            st.write("")
            if st.button(t["update_btn"], use_container_width=True):
                update_status(target_id, new_st)
                st.success(f"Statut mis à jour pour ID {target_id}")
                st.rerun()
    else:
        st.info(t["no_data"])

# ----------------------------------------------------
# 3. Bordereau de Remise (PDF / Excel)
# ----------------------------------------------------
elif menu == t["menu_remise"]:
    st.subheader(t["menu_remise"])
    df_portefeuille = df[df["statut"] == "En portefeuille"]

    if df_portefeuille.empty:
        st.info(t["no_data"])
    else:
        selected_ids = []
        for idx, row in df_portefeuille.iterrows():
            if st.checkbox(
                f"ID: {row['id']} | {row['type']} N° {row['reference']} | {row['client']} | {row['montant']} DH | Échéance: {row['echeance']}",
                key=f"chk_{row['id']}",
            ):
                selected_ids.append(row["id"])

        if selected_ids:
            remise_df = df_portefeuille[df_portefeuille["id"].isin(selected_ids)]
            st.dataframe(remise_df, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
                    remise_df.to_excel(
                        writer, index=False, sheet_name="Bordereau"
                    )
                st.download_button(
                    label=f"📥 {t['export_excel']}",
                    data=buffer_excel.getvalue(),
                    file_name="Bordereau.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            with col2:

                def generate_pdf(data):
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
                    elements = []
                    styles = getSampleStyleSheet()
                    elements.append(
                        Paragraph(
                            "<b>BORDEREAU DE REMISE DE CHEQUES / EFFETS</b>",
                            styles["Title"],
                        )
                    )
                    elements.append(Spacer(1, 20))

                    table_data = [
                        [
                            "Type",
                            "Référence",
                            "Client",
                            "Banque",
                            "Montant (DH)",
                            "Échéance",
                        ]
                    ]
                    total = 0
                    for _, r in data.iterrows():
                        table_data.append(
                            [
                                str(r["type"]),
                                str(r["reference"]),
                                str(r["client"]),
                                str(r["banque"]),
                                f"{r['montant']:.2f}",
                                str(r["echeance"]),
                            ]
                        )
                        total += float(r["montant"])
                    table_data.append(
                        ["TOTAL", "", "", "", f"{total:.2f} DH", ""]
                    )

                    pdf_table = Table(table_data)
                    pdf_table.setStyle(
                        TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, 0),
                                    colors.HexColor("#1e3d59"),
                                ),
                                (
                                    "TEXTCOLOR",
                                    (0, 0),
                                    (-1, 0),
                                    colors.whitesmoke,
                                ),
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                            ]
                        )
                    )
                    elements.append(pdf_table)
                    doc.build(elements)
                    return pdf_buffer.getvalue()

                st.download_button(
                    label=f"📄 {t['export_pdf']}",
                    data=generate_pdf(remise_df),
                    file_name="Bordereau.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

# ----------------------------------------------------
# 4. Suivi des Impayés
# ----------------------------------------------------
elif menu == t["menu_impayes"]:
    st.subheader(t["menu_impayes"])
    df_impayes = df[df["statut"] == "Impayé"]

    if df_impayes.empty:
        st.success("Aucun titre impayé enregistré / No unpaid instruments.")
    else:
        st.error(f"Attention: {len(df_impayes)} titre(s) marqué(s) Impayé.")
        st.dataframe(df_impayes, use_container_width=True)
        st.metric(
            "Total Impayés (DH)",
            value=f"{df_impayes['montant'].sum():,.2f} DH",
        )
