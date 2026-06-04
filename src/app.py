import os
import sys
import streamlit as st
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.dtos import RiskLevel, ClauseType
from src.graph.workflow import build_workflow_graph, run_pipeline

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
if "analyzed_file" not in st.session_state:
    st.session_state["analyzed_file"] = None

st.set_page_config(
    page_title="Audit Contracte Juridice AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .report-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .report-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="report-title">⚖️ Analiză și Audit Automatizat al Contractelor Juridice</div>', unsafe_allow_html=True)
st.markdown('<div class="report-subtitle">Sistem multi-agent bazat pe RAG pentru identificarea clauzelor abuzive sau neconforme cu legislația din România</div>', unsafe_allow_html=True)

st.sidebar.header("🔧 Configurare Analiză")

uploaded_file = st.sidebar.file_uploader(
    "1. Încărcați Contractul (PDF)", 
    type=["pdf"],
    help="Contractul în limba română pe care doriți să îl auditați."
)

st.sidebar.subheader("Setări RAG & Evaluare")

threshold = st.sidebar.slider(
    "Prag de relevanță RAG (similarity)",
    min_value=0.10,
    max_value=0.80,
    value=0.30,
    step=0.05,
    help="Valoarea minimă a scorului de similaritate pentru ca un fragment legal din corpus să fie considerat context util clauzei analizate."
)

high_risk_threshold = st.sidebar.slider(
    "Prag alertă risc ridicat",
    min_value=1,
    max_value=10,
    value=2,
    step=1,
    help="Numărul maxim admis de clauze cu risc RIDICAT înainte de declanșarea unei alerte roșii în document."
)

analyze_button = st.sidebar.button(
    "🚀 Start Audit Contract",
    disabled=uploaded_file is None,
    use_container_width=True
)


if uploaded_file is not None and st.session_state["analyzed_file"] != uploaded_file.name:
    st.session_state["analysis_result"] = None
    st.session_state["analyzed_file"] = None

if uploaded_file is None:
    st.info("👈 Vă rugăm să încărcați un contract în format PDF din meniul lateral pentru a începe auditul.")
    

    st.subheader("Tipuri de clauze analizate & Legislația de referință")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Clauze contractuale analizate:**
        *   🔴 **Penalități de întârziere** (Legea 98/2016, asimetrie penalități)
        *   🔴 **Prelucrare date personale / GDPR** (Regulament UE 2016/679)
        *   🔴 **Clauze de forță majoră** (Art. 1351 Cod Civil)
        *   🔴 **Reziliere unilaterală** (ANPC clauze abuzive în detrimentul consumatorului)
        *   🔴 **Cesiunea contractului** (UNCITRAL, acord părți)
        *   🔴 **Răspundere limitată** (Art. 1355 Cod Civil, excludere culpă gravă/intenție)
        *   🔴 **Clauze de confidențialitate** (GDPR, NDA standard)
        *   🔴 **Jurisdicție și arbitraj** (Regulament UE 1215/2012, clauze abuzive de arbitraj)
        """)
        
    with col2:
        st.markdown("""
        **Corpusul Juridic RAG:**
        *   **GDPR:** Regulamentul (UE) 2016/679 și Ghidurile conexe
        *   **Achiziții Publice:** Legea 98/2016 (Art. 164)
        *   **Legea 193/2000:** Protecția consumatorilor împotriva clauzelor abuzive
        *   **Codul Civil Român:** Reglementările generale de răspundere și forță majoră
        *   **UNCITRAL:** Legile model privind comerțul electronic și semnăturile
        *   **ANPC:** Ghiduri oficiale de bune practici în comerț și servicii
        """)
else:
    if analyze_button:
        with st.status("Analiză în desfășurare... Vă rugăm să așteptați.", expanded=True) as status:
            try:
                os.makedirs("data", exist_ok=True)
                temp_pdf_path = os.path.join("data", uploaded_file.name)
                with open(temp_pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                status.write("📄 Se parsează contractul PDF și se extrag clauzele...")
                workflow_graph = build_workflow_graph()
                app = workflow_graph.compile()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = f"data/{os.path.splitext(uploaded_file.name)[0]}_audit_report_{timestamp}.md"

                status.write("🔍 Se interoghează indexul RAG și se evaluează riscurile...")
                inputs = {
                    "pdf_path": temp_pdf_path,
                    "report_path": report_path,
                    "iteration": 0,
                    "timestamp": timestamp
                }

                pipeline_state = app.invoke(inputs)
                
                status.write("📝 Se generează reformulările contractuale și raportul de audit...")
                
                st.session_state["analysis_result"] = pipeline_state
                st.session_state["analyzed_file"] = uploaded_file.name
                
                status.update(label="✅ Audit finalizat cu succes!", state="complete", expanded=False)
            except Exception as e:
                status.update(label=f"❌ Eroare la execuția analizei: {str(e)}", state="error", expanded=True)
                st.error(f"Detalii eroare: {e}")
                

    if st.session_state["analysis_result"] is not None:
        state = st.session_state["analysis_result"]
        parsed_doc = state["parsed_doc"]
        risk_map = state["risk_map"]
        recommendations = state["recommendations"]
        report_path = state["report_path"]

        total_clauses = len(parsed_doc.clauses)
        risks_count = {
            RiskLevel.RIDICAT: 0,
            RiskLevel.MEDIU: 0,
            RiskLevel.SCAZUT: 0,
            RiskLevel.CONFORM: 0,
            RiskLevel.NECUNOSCUT: 0
        }
        for r in risk_map.values():
            risks_count[r.risk_level] = risks_count.get(r.risk_level, 0) + 1
            

        high_risk_count = risks_count[RiskLevel.RIDICAT]
        if high_risk_count >= high_risk_threshold:
            st.error(f"⚠️ **ALERTĂ DE RISC MAJOR:** Contractul conține **{high_risk_count}** clauze evaluate cu risc **RIDICAT**! Acest lucru depășește pragul de alertă configurat ({high_risk_threshold}). Se recomandă revizuirea imediată.")
        elif high_risk_count > 0:
            st.warning(f"⚠️ **Atenție:** Au fost identificate **{high_risk_count}** clauze cu risc **RIDICAT** și **{risks_count[RiskLevel.MEDIU]}** cu risc **MEDIU**.")
        else:
            st.success("✅ Audit finalizat. Nu a fost detectat niciun risc major în document.")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f'<div class="metric-card"><div style="color: #ef4444;" class="metric-value">{risks_count[RiskLevel.RIDICAT]}</div><div style="font-size: 0.85rem; color: #64748b;">Risc RIDICAT</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div style="color: #f59e0b;" class="metric-value">{risks_count[RiskLevel.MEDIU]}</div><div style="font-size: 0.85rem; color: #64748b;">Risc MEDIU</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div style="color: #eab308;" class="metric-value">{risks_count[RiskLevel.SCAZUT]}</div><div style="font-size: 0.85rem; color: #64748b;">Risc SCĂZUT</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div style="color: #10b981;" class="metric-value">{risks_count[RiskLevel.CONFORM]}</div><div style="font-size: 0.85rem; color: #64748b;">CONFORM</div></div>', unsafe_allow_html=True)
        with col5:
            st.markdown(f'<div class="metric-card"><div style="color: #64748b;" class="metric-value">{risks_count[RiskLevel.NECUNOSCUT]}</div><div style="font-size: 0.85rem; color: #64748b;">NECUNOSCUT</div></div>', unsafe_allow_html=True)
            
        st.write("")

        metadata = parsed_doc.metadata
        with st.expander("📄 Metadate Contract Identificate", expanded=True):
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.markdown(f"**Titlu:** {metadata.title}")
                parties_list = ", ".join([p.name for p in metadata.parties])
                st.markdown(f"**Părți:** {parties_list or 'Nespecificate'}")
                st.markdown(f"**Număr Pagini:** {metadata.page_count}")
            with m_col2:
                st.markdown(f"**Data Semnării:** {metadata.signing_date or 'Nespecificată'}")
                st.markdown(f"**Valoare Contract:** {metadata.value}")
                st.markdown(f"**Durată Contract:** {metadata.duration}")
                

        st.subheader("📋 Centralizator Analiză Clauze")
        
        html_table = """
        <table style="width:100%; border-collapse: collapse; margin: 15px 0; font-family: sans-serif; border: 1px solid #dee2e6;">
            <thead>
                <tr style="background-color: #f8fafc; border-bottom: 2px solid #dee2e6; color: #334155;">
                    <th style="padding: 12px 15px; text-align: left; font-weight: 600;">ID Clauză</th>
                    <th style="padding: 12px 15px; text-align: left; font-weight: 600;">Secțiune Contract</th>
                    <th style="padding: 12px 15px; text-align: left; font-weight: 600;">Tip Clauză</th>
                    <th style="padding: 12px 15px; text-align: center; font-weight: 600;">Nivel Risc</th>
                </tr>
            </thead>
            <tbody>
        """
        for clause in parsed_doc.clauses:
            risk = risk_map.get(clause.id)
            if not risk:
                continue
                

            bg_color = "#ffffff"
            text_color = "#0f172a"
            risk_label = risk.risk_level.value
            
            if risk.risk_level == RiskLevel.RIDICAT:
                bg_color = "#ffe3e3"
                text_color = "#991b1b"
            elif risk.risk_level == RiskLevel.MEDIU:
                bg_color = "#fff3bf"
                text_color = "#92400e"
            elif risk.risk_level == RiskLevel.SCAZUT:
                bg_color = "#fff9c4"
                text_color = "#854d0e"
            elif risk.risk_level == RiskLevel.CONFORM:
                bg_color = "#d3f9d8"
                text_color = "#166534"
            elif risk.risk_level == RiskLevel.NECUNOSCUT:
                bg_color = "#f1f5f9"
                text_color = "#475569"
                
            html_table += f"""
                <tr style="background-color: {bg_color}; border-bottom: 1px solid #dee2e6; color: {text_color};">
                    <td style="padding: 12px 15px; font-weight: bold;">{clause.id}</td>
                    <td style="padding: 12px 15px;">{clause.section}</td>
                    <td style="padding: 12px 15px;"><code>{clause.type.value}</code></td>
                    <td style="padding: 12px 15px; text-align: center; font-weight: bold;">{risk_label}</td>
                </tr>
            """
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)
        

        st.subheader("🔍 Evaluare detaliată și Reformulări propuse")
        
        clause_idx = 1
        for clause in parsed_doc.clauses:
            risk = risk_map.get(clause.id)
            if not risk:
                continue
                

            if risk.risk_level in [RiskLevel.RIDICAT, RiskLevel.MEDIU, RiskLevel.NECUNOSCUT]:
                rec = next((r for r in recommendations if r.clause_id == clause.id), None)
                
                title_status = f"🔴 RIDICAT" if risk.risk_level == RiskLevel.RIDICAT else f"🟡 MEDIU"
                if risk.risk_level == RiskLevel.NECUNOSCUT:
                    title_status = f"⚫ NECUNOSCUT"
                    
                with st.expander(f"Clauza {clause_idx}: {clause.section} (Nivel {title_status})"):
                    st.write("**Text original din contract:**")
                    st.code(clause.text, language="text")
                    
                    if risk.issues:
                        st.markdown("**Deficiențe identificate:**")
                        for issue in risk.issues:
                            st.markdown(f"- ⚠️ {issue}")
                            
                    if risk.references:
                        st.markdown(f"**Surse de referință în corpus:** {', '.join([f'`{r}`' for r in risk.references])}")
                        
                    if rec and rec.reformulated_text:
                        st.markdown("🆕 **Reformulare propusă (Echilibrată și Conformă):**")
                        st.code(rec.reformulated_text, language="text")
                        st.markdown(f"**Justificare Juridică:**\n{rec.explanation}")

                        if rec.candidates:
                            with st.expander("Visualizare opțiuni de autoconsecvență (Self-Consistency candidates)"):
                                for c_idx, candidate in enumerate(rec.candidates):
                                    st.write(f"Candidatul {c_idx+1}:")
                                    st.code(candidate, language="text")
                    elif risk.risk_level == RiskLevel.NECUNOSCUT:
                        st.info("Clauza nu a putut fi evaluată deoarece nu există referințe legislative corespunzătoare în vectorstore.")
                    else:
                        st.write("Clauză conformă sau nu necesită modificări.")
                        
            clause_idx += 1
            

        st.write("")
        st.subheader("📥 Export Raport Audit")
        

        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
                
            st.download_button(
                label="📥 Descarcă Raportul de Audit (Markdown)",
                data=report_content,
                file_name=os.path.basename(report_path),
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.warning("Raportul Markdown nu a fost generat pe disc.")
