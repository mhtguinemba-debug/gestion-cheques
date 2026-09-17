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

# 2. Custom CSS
st.markdown(
    """
<style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        color: white;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }
    .stForm {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""",
    unsafe_allow_html=True,
)


# 3. Database Setup & Automatic Migration
def init_db():
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()

    # Table Titres
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS titres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            societe TEXT,
            type TEXT,
            reference TEXT,
            client TEXT,
            banque TEXT,
            rib TEXT,
            montant REAL,
            echeance TEXT,
            statut TEXT,
            archive INTEGER DEFAULT 0
        )
    """
    )

    # Automatic Migration: Check for missing columns in existing database
    c.execute("PRAGMA table_info(titres)")
    columns = [column[1] for column in c.fetchall()]

    if "societe" not in columns:
        c.execute("ALTER TABLE titres ADD COLUMN societe TEXT DEFAULT 'Ma Société'")
    if "rib" not in columns:
        c.execute("ALTER TABLE titres ADD COLUMN rib TEXT DEFAULT '-'")
    if "archive" not in columns:
        c.execute("ALTER TABLE titres ADD COLUMN archive INTEGER DEFAULT 0")

    # Table Users
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """
    )

    # Default users creation
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO users VALUES (?, ?)",
            [
                ("admin", "admin123"),
                ("user1", "user123"),
                ("user2", "user123"),
                ("user3", "user123"),
            ],
        )
    conn.commit()
    conn.close()


init_db()


def load_data(include_archived=False):
    conn = sqlite3.connect("data_gestion.db")
    query = (
        "SELECT * FROM titres"
        if include_archived
        else "SELECT * FROM titres WHERE archive = 0"
    )
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def insert_data(
    societe, titre_type, ref, client, bank, rib, amount, due_date, status
):
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO titres (societe, type, reference, client, banque, rib, montant, echeance, statut, archive)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """,
        (
            societe,
            titre_type,
            ref,
            client,
            bank,
            rib,
            amount,
            str(due_date),
            status,
        ),
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


def archive_item(item_id):
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute("UPDATE titres SET archive = 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def check_user(username, password):
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password),
    )
    user = c.fetchone()
    conn.close()
    return user is not None


def change_password(username, new_password):
    conn = sqlite3.connect("data_gestion.db")
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password = ? WHERE username = ?",
        (new_password, username),
    )
    conn.commit()
    conn.close()


# 4. Authentication Check
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""

if not st.session_state["authenticated"]:
    st.markdown(
        "<h2 style='text-align: center;'>🔒 Connexion / Login</h2>",
        unsafe_allow_html=True,
    )
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur / Username")
            password = st.text_input("Mot de passe / Password", type="password")
            submit_login = st.form_submit_button(
                "Se connecter / Log In", use_container_width=True
            )
            if submit_login:
                if check_user(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = username
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
        "menu_archive": "Archives",
        "total_portefeuille": "En Portefeuille",
        "total_remis": "Remis en Banque",
        "total_paye": "Payés / Encaissés",
        "total_impaye": "Impayés",
        "alerts_title": "⚠️ Échéances Proches (7 prochains jours)",
        "societe": "Nom de la Société",
        "type": "Type de Titre",
        "ref": "N° Référence / Chèque",
        "client": "Client / Tireur",
        "bank": "Banque",
        "rib": "N° RIB (24 chiffres)",
        "amount": "Montant (DH)",
        "due_date": "Date d'Échéance",
        "status": "Statut",
        "save_btn": "Enregistrer le Titre",
        "update_btn": "Mettre à jour",
        "archive_btn": "Archiver",
        "search_label": "Rechercher (Référence ou Client)",
        "filter_bank": "Filtrer par Banque",
        "filter_status": "Filtrer par Statut",
        "all": "Tous",
        "export_excel": "Exporter Excel",
        "export_pdf": "Générer PDF Bordereau",
        "logout": "Déconnexion",
        "change_pwd": "Changer le mot de passe",
        "no_data": "Aucune donnée disponible.",
    },
    "English": {
        "title": "📊 Check & Bill Management Platform",
        "menu_dash": "Dashboard",
        "menu_saisie": "Data Entry & Edit",
        "menu_remise": "Remittance Slip",
        "menu_impayes": "Unpaid Tracking",
        "menu_archive": "Archives",
        "total_portefeuille": "Portfolio Total",
        "total_remis": "Deposited Total",
        "total_paye": "Paid Total",
        "total_impaye": "Unpaid Total",
        "alerts_title": "⚠️ Upcoming Due Dates (Next 7 days)",
        "societe": "Company Name",
        "type": "Instrument Type",
        "ref": "Reference / Check N°",
        "client": "Client / Issuer",
        "bank": "Bank",
        "rib": "RIB N° (24 digits)",
        "amount": "Amount (DH)",
        "due_date": "Due Date",
        "status": "Status",
        "save_btn": "Save Record",
        "update_btn": "Update",
        "archive_btn": "Archive",
        "search_label": "Search (Reference or Client)",
        "filter_bank": "Filter by Bank",
        "filter_status": "Filter by Status",
        "all": "All",
        "export_excel": "Export Excel",
        "export_pdf": "Generate PDF Remittance",
        "logout": "Log Out",
        "change_pwd": "Change Password",
        "no_data": "No data available.",
    },
}

# Sidebar Navigation
st.sidebar.title("⚙️ Navigation")
st.sidebar.write(
    f"👤 Connecté en tant que: **{st.session_state['current_user']}**"
)
lang = st.sidebar.selectbox("🌐 Language / Langue", ["Français", "English"])
t = TEXTS[lang]

menu = st.sidebar.radio(
    "Menu",
    [
        t["menu_dash"],
        t["menu_saisie"],
        t["menu_remise"],
        t["menu_impayes"],
        t["menu_archive"],
    ],
)

# Password Change Modal in Sidebar
with st.sidebar.expander(f"🔑 {t['change_pwd']}"):
    with st.form("pwd_form"):
        new_pwd = st.text_input("Nouveau mot de passe", type="password")
        submit_pwd = st.form_submit_button("Valider")
        if submit_pwd and new_pwd:
            change_password(st.session_state["current_user"], new_pwd)
            st.success("Mot de passe modifié !")

st.sidebar.markdown("---")
if st.sidebar.button(f"🔴 {t['logout']}", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""
    st.rerun()

st.title(t["title"])
st.markdown("---")

df = load_data()

# ----------------------------------------------------
# 1. Dashboard
# ----------------------------------------------------
if menu == t["menu_dash"]:
    st.subheader(t["menu_dash"])

    c1, c2, c3, c4 = st.columns(4)
    v_portefeuille = (
        df[df["statut"] == "En portefeuille"]["montant"].sum()
        if not df.empty
        else 0
    )
    v_remis = (
        df[df["statut"] == "Remis à la banque"]["montant"].sum()
        if not df.empty
        else 0
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
                    [
                        "id",
                        "societe",
                        "type",
                        "reference",
                        "client",
                        "montant",
                        "echeance",
                    ]
                ],
                use_container_width=True,
            )
    else:
        st.info(t["no_data"])

# ----------------------------------------------------
# 2. Saisie & Modification
# ----------------------------------------------------
elif menu == t["menu_saisie"]:
    st.subheader(t["menu_saisie"])

    with st.expander("➕ Ajouter un nouveau titre", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                societe = st.text_input(t["societe"], value="Ma Société")
                titre_type = st.selectbox(
                    t["type"], ["Chèque", "Effet", "Versement"]
                )
                ref = st.text_input(t["ref"])
                client = st.text_input(t["client"])
            with col2:
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
                rib = st.text_input(t["rib"])
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
                    societe,
                    titre_type,
                    ref,
                    client,
                    bank,
                    rib,
                    amount,
                    due_date,
                    status,
                )
                st.success("Enregistré avec succès!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("🔍 Recherche & Actions")
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
                filtered_df["reference"].str.contains(
                    search_query, case=False, na=False
                )
                | filtered_df["client"].str.contains(
                    search_query, case=False, na=False
                )
            ]
        if selected_bank != t["all"]:
            filtered_df = filtered_df[filtered_df["banque"] == selected_bank]
        if selected_status != t["all"]:
            filtered_df = filtered_df[filtered_df["statut"] == selected_status]

        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("##### ✏️ Actions sur un titre (Statut / Archiver)")
        col_id, col_new_st, col_act1, col_act2 = st.columns([1, 2, 1, 1])
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
        with col_act1:
            st.write("")
            st.write("")
            if st.button(t["update_btn"], use_container_width=True):
                update_status(target_id, new_st)
                st.success(f"Statut mis à jour pour ID {target_id}")
                st.rerun()
        with col_act2:
            st.write("")
            st.write("")
            if st.button(f"📦 {t['archive_btn']}", use_container_width=True):
                archive_item(target_id)
                st.success(f"Titre ID {target_id} archivé !")
                st.rerun()
    else:
        st.info(t["no_data"])

# ----------------------------------------------------
# 3. Bordereau de Remise (PDF & Excel)
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
                f"ID: {row['id']} | {row['societe']} | {row['type']} N° {row['reference']} | {row['client']} | {row['montant']} DH | Banque: {row['banque']} (RIB: {row['rib']})",
                key=f"chk_{row['id']}",
            ):
                selected_ids.append(row["id"])

        if selected_ids:
            remise_df = df_portefeuille[
                df_portefeuille["id"].isin(selected_ids)
            ]
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

                    first_row = data.iloc[0]
                    societe_name = str(first_row.get("societe", "Société"))
                    bank_name = str(first_row.get("banque", "Banque"))
                    rib_num = str(first_row.get("rib", "-"))

                    elements.append(
                        Paragraph(
                            "<b>BORDEREAU DE REMISE DE CHEQUES / EFFETS</b>",
                            styles["Title"],
                        )
                    )
                    elements.append(Spacer(1, 10))
                    elements.append(
                        Paragraph(
                            f"<b>Société:</b> {societe_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Banque:</b> {bank_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>RIB:</b> {rib_num}",
                            styles["Normal"],
                        )
                    )
                    elements.append(Spacer(1, 15))

                    table_data = [
                        [
                            "Type",
                            "Référence",
                            "Client",
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
                                f"{r['montant']:.2f}",
                                str(r["echeance"]),
                            ]
                        )
                        total += float(r["montant"])
                    table_data.append(["TOTAL", "", "", f"{total:.2f} DH", ""])

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
                    file_name="Bordereau_Remise.pdf",
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

# ----------------------------------------------------
# 5. Archives
# ----------------------------------------------------
elif menu == t["menu_archive"]:
    st.subheader(t["menu_archive"])
    df_archived = load_data(include_archived=True)
    df_archived = df_archived[df_archived["archive"] == 1]

    if df_archived.empty:
        st.info("Aucune donnée archivée.")
    else:
        st.dataframe(df_archived, use_container_width=True)
