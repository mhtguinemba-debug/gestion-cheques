import datetime
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import streamlit as st

# 1. إعدادات الصفحة / Configuration de la page
st.set_page_config(
    page_title="Gestion des Titres & Chèques", page_icon="💳", layout="wide"
)

# 2. القواميس للغتين (Dictionnaire Bilingue FR / EN)
TEXTS = {
    "Français": {
        "title": "📊 Gestion des Chèques, Effets et Versements",
        "lang_select": "Langue / Language",
        "menu_saisie": "Saisie (إدخال)",
        "menu_remise": "Bordereau de Remise (جدول الإيداع)",
        "menu_impayes": "Suivi des Impayés (المرفوضات)",
        "type": "Type de Titre",
        "ref": "N° de Chèque / Effet / Réf",
        "client": "Client / Tireur",
        "bank": "Banque",
        "amount": "Montant (DH)",
        "due_date": "Date d'Échéance",
        "status": "Statut",
        "save_btn": "Enregistrer le Titre",
        "success_msg": "Titre enregistré avec succès !",
        "select_remise": "Sélectionner les titres à remettre à la banque",
        "export_excel": "Exporter en Excel",
        "export_pdf": "Générer Bordereau PDF",
        "no_data": "Aucune donnée disponible.",
    },
    "English": {
        "title": "📊 Check, Bill & Deposit Management",
        "lang_select": "Langue / Language",
        "menu_saisie": "Data Entry",
        "menu_remise": "Remittance / Deposit Slip",
        "menu_impayes": "Unpaid Tracking",
        "type": "Instrument Type",
        "ref": "Reference / Check N°",
        "client": "Client / Issuer",
        "bank": "Bank",
        "amount": "Amount",
        "due_date": "Due Date",
        "status": "Status",
        "save_btn": "Save Instrument",
        "success_msg": "Instrument saved successfully!",
        "select_remise": "Select instruments to deposit",
        "export_excel": "Export to Excel",
        "export_pdf": "Generate PDF Remittance",
        "no_data": "No data available.",
    },
}

# 3. اختيار اللغة من القائمة الجانبية
lang = st.sidebar.selectbox("🌐 Language / Langue", ["Français", "English"])
t = TEXTS[lang]

# 4. تهيئة ذاكرة البيانات (Session State)
if "data" not in st.session_state:
    st.session_state["data"] = pd.DataFrame(
        columns=[
            "ID",
            "Type",
            "Référence",
            "Client",
            "Banque",
            "Montant",
            "Échéance",
            "Statut",
        ]
    )

st.title(t["title"])

# 5. القائمة الجانبية للتنقل
menu = st.sidebar.radio(
    "Navigation", [t["menu_saisie"], t["menu_remise"], t["menu_impayes"]]
)

# ----------------------------------------------------
# 1. قسم الإدخال (Saisie)
# ----------------------------------------------------
if menu == t["menu_saisie"]:
    st.subheader(t["menu_saisie"])

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
                    "Autre / Other",
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

        submit = st.form_submit_button(t["save_btn"])

        if submit:
            new_id = len(st.session_state["data"]) + 1
            new_data = {
                "ID": new_id,
                "Type": titre_type,
                "Référence": ref,
                "Client": client,
                "Banque": bank,
                "Montant": amount,
                "Échéance": str(due_date),
                "Statut": status,
            }
            st.session_state["data"] = pd.concat(
                [st.session_state["data"], pd.DataFrame([new_data])],
                ignore_index=True,
            )
            st.success(t["success_msg"])

    st.markdown("---")
    st.dataframe(st.session_state["data"], use_container_width=True)

# ----------------------------------------------------
# 2. قسم جدول الإيداع وتصدير PDF / Excel (Bordereau de Remise)
# ----------------------------------------------------
elif menu == t["menu_remise"]:
    st.subheader(t["menu_remise"])

    df = st.session_state["data"]
    df_portefeuille = df[df["Statut"] == "En portefeuille"]

    if df_portefeuille.empty:
        st.info(t["no_data"])
    else:
        st.write(t["select_remise"])
        selected_ids = []

        for idx, row in df_portefeuille.iterrows():
            chk = st.checkbox(
                f"ID: {row['ID']} | {row['Type']} N° {row['Référence']} | {row['Client']} | {row['Montant']} DH | Date: {row['Échéance']}",
                key=f"chk_{row['ID']}",
            )
            if chk:
                selected_ids.append(row["ID"])

        if selected_ids:
            remise_df = df_portefeuille[
                df_portefeuille["ID"].isin(selected_ids)
            ]
            st.markdown("### 📋 Sélection pour la remise")
            st.dataframe(remise_df, use_container_width=True)

            col1, col2 = st.columns(2)

            # تصدير إلى Excel
            with col1:
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
                    remise_df.to_excel(
                        writer, index=False, sheet_name="Bordereau"
                    )
                st.download_button(
                    label=f"📥 {t['export_excel']}",
                    data=buffer_excel.getvalue(),
                    file_name="Bordereau_de_Remise.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # تصدير إلى PDF
            with col2:

                def generate_pdf(data):
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
                    elements = []
                    styles = getSampleStyleSheet()

                    title = Paragraph(
                        "<b>BORDEREAU DE REMISE DE CHEQUES / EFFETS</b>",
                        styles["Title"],
                    )
                    elements.append(title)
                    elements.append(Spacer(1, 20))

                    # إعداد جدول PDF
                    table_data = [
                        [
                            "Type",
                            "Référence",
                            "Client / Tireur",
                            "Banque",
                            "Montant (DH)",
                            "Échéance",
                        ]
                    ]
                    total = 0
                    for _, r in data.iterrows():
                        table_data.append(
                            [
                                str(r["Type"]),
                                str(r["Référence"]),
                                str(r["Client"]),
                                str(r["Banque"]),
                                f"{r['Montant']:.2f}",
                                str(r["Échéance"]),
                            ]
                        )
                        total += float(r["Montant"])

                    table_data.append(
                        ["TOTAL", "", "", "", f"{total:.2f} DH", ""]
                    )

                    t_style = TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor("#1e3d59"),
                            ),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                            (
                                "BACKGROUND",
                                (0, 1),
                                (-1, -1),
                                colors.HexColor("#f5f5f5"),
                            ),
                            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                            (
                                "FONTNAME",
                                (0, -1),
                                (-1, -1),
                                "Helvetica-Bold",
                            ),
                        ]
                    )
                    pdf_table = Table(table_data)
                    pdf_table.setStyle(t_style)
                    elements.append(pdf_table)

                    doc.build(elements)
                    return pdf_buffer.getvalue()

                pdf_data = generate_pdf(remise_df)
                st.download_button(
                    label=f"📄 {t['export_pdf']}",
                    data=pdf_data,
                    file_name="Bordereau_Remise.pdf",
                    mime="application/pdf",
                )

# ----------------------------------------------------
# 3. قسم متابعة المرفوضات (Suivi des Impayés)
# ----------------------------------------------------
elif menu == t["menu_impayes"]:
    st.subheader(t["menu_impayes"])

    df = st.session_state["data"]
    df_impayes = df[df["Statut"] == "Impayé"]

    if df_impayes.empty:
        st.success(
            "Aucun titre impayé enregistré. / No unpaid instruments found."
        )
    else:
        st.error(
            f"Attention: {len(df_impayes)} titre(s) marqué(s) comme Impayé."
        )
        st.dataframe(df_impayes, use_container_width=True)

        # حساب المجموع
        total_impaye = df_impayes["Montant"].sum()
        st.metric(
            label="Total Montant Impayé (DH)", value=f"{total_impaye:,.2f} DH"
        )
