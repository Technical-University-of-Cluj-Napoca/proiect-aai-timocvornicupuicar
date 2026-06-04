import os
import re
import json
from dotenv import load_dotenv

from src.dtos import ClauseDTO, RiskAssessmentDTO, RecommendationDTO, RiskLevel, RetrievalResultDTO
from src.utils import get_llm

load_dotenv()

SYSTEM_PROMPT = (
    "Ești un avocat expert în redactarea și auditul contractelor în limba română.\n"
    "Sarcina ta este să propui o reformulare legală și echilibrată pentru o clauză contractuală care prezintă riscuri.\n\n"
    "REGULI DE REDACTARE:\n"
    "1. Folosește un stil juridic formal, clar, precis și concis, adecvat contractelor comerciale din România.\n"
    "2. Asigură-te că reformularea elimină complet riscurile identificate și este fundamentată strict pe contextul legislativ oferit.\n"
    "3. Menține un echilibru contractual între părți (de ex. dacă se impun penalități, acestea trebuie să fie rezonabile și simetrice; dacă se colectează date personale, trebuie incluse obligațiile legale de notificare și consimțământ).\n"
    "4. Returnează răspunsul tău EXCLUSIV ca un text JSON valid, fără alte introduceri sau formatări de blocuri de cod (de ex. ```json):\n\n"
    "{\n"
    "  \"reformulated_text\": \"Textul reformulat al clauzei în limba română\",\n"
    "  \"explanation\": \"Justificarea juridică a modificărilor propuse și trimiterea la textele de lege aplicabile din context (în limba română)\"\n"
    "}"
)

SELECTION_PROMPT = (
    "Ești un avocat senior consultant din România.\n"
    "Sarcina ta este să evaluezi 3 propuneri independente de reformulare pentru o clauză contractuală cu risc RIDICAT.\n"
    "Analizează cele 3 opțiuni și alege-o pe cea mai conformă cu legislația de referință din context, care folosește cel mai bun limbaj juridic și menține echilibrul contractual. Dacă este necesar, poți sintetiza elemente din cele 3 opțiuni pentru a crea varianta ideală.\n\n"
    "Text original clauză:\n{original_text}\n\n"
    "Opțiunea de reformulare 1:\n{opt_1}\n\n"
    "Opțiunea de reformulare 2:\n{opt_2}\n\n"
    "Opțiunea de reformulare 3:\n{opt_3}\n\n"
    "Context legislativ de referință:\n{context}\n\n"
    "Returnează răspunsul tău EXCLUSIV ca un text JSON valid, fără blocuri markdown de cod (de ex. ```json) și fără alte explicații:\n\n"
    "{\n"
    "  \"reformulated_text\": \"Varianta finală optimă și completă a clauzei reformulate în limba română\",\n"
    "  \"explanation\": \"Explicația juridică detaliată de ce această variantă a fost aleasă/sintetizată ca fiind cea mai conformă și sigură\"\n"
    "}"
)

class RecommendationAgent:
    def __init__(self):
        self._llm = None
        self._creative_llm = None
        
    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm
        
    @property
    def creative_llm(self):
        """Initializes an LLM with slightly higher temperature for generating diverse candidates."""
        if self._creative_llm is None:
            openai_key = os.getenv("OPENAI_API_KEY")
            google_key = os.getenv("GOOGLE_API_KEY")
            
            if openai_key:
                try:
                    from langchain_openai import ChatOpenAI
                    self._creative_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
                except ImportError:
                    pass
            if self._creative_llm is None and google_key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._creative_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
            else:
                self._creative_llm = self.llm
        return self._creative_llm

    def _call_reformatter(self, use_creative: bool, clause: ClauseDTO, issues: list[str], context_str: str) -> dict:
        """Helper to invoke the LLM for reformulating a clause."""
        llm_client = self.creative_llm if use_creative else self.llm
        
        human_prompt = (
            f"Clauza de reformulat:\n"
            f"Text original: {clause.text}\n"
            f"Tip clauză: {clause.type.value}\n"
            f"Probleme identificate: {', '.join(issues)}\n\n"
            f"Context legislativ disponibil:\n"
            f"{context_str}"
        )
        
        prompt = [
            ("system", SYSTEM_PROMPT),
            ("human", human_prompt)
        ]
        
        response = llm_client.invoke(prompt)
        content = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n", "", content)
            content = re.sub(r"\n```$", "", content)
            
        return json.loads(content)

    def recommend(self, clause: ClauseDTO, risk_assessment: RiskAssessmentDTO, context_chunks: list[RetrievalResultDTO]) -> RecommendationDTO:
        """
        Generates reformulation recommendations.
        Only runs LLM queries for RIDICAT and MEDIU risk levels.
        Implements self-consistency for RIDICAT risks.
        """

        if risk_assessment.risk_level not in [RiskLevel.RIDICAT, RiskLevel.MEDIU]:
            print(f"Risk level for clause {clause.id} is {risk_assessment.risk_level.value}. Skipping recommendation LLM call.")
            return RecommendationDTO(
                clause_id=clause.id,
                original_text=clause.text,
                reformulated_text="",
                explanation="Nu este necesară nicio reformulare. Clauza este conformă sau prezintă risc scăzut.",
                sources=[c.source for c in context_chunks],
                candidates=None
            )

        context_str = ""
        for chunk in context_chunks:
            context_str += f"Sursa: {chunk.source}\n{chunk.text}\n\n"
            
        sources = list(set([c.source for c in context_chunks]))

        if risk_assessment.risk_level == RiskLevel.MEDIU:
            try:
                data = self._call_reformatter(False, clause, risk_assessment.issues, context_str)
                return RecommendationDTO(
                    clause_id=clause.id,
                    original_text=clause.text,
                    reformulated_text=data.get("reformulated_text", ""),
                    explanation=data.get("explanation", "Clauză modificată pentru corectarea riscului mediu."),
                    sources=sources,
                    candidates=None
                )
            except Exception as e:
                print(f"Error reformulating MEDIU risk clause {clause.id}: {e}")
                return RecommendationDTO(
                    clause_id=clause.id,
                    original_text=clause.text,
                    reformulated_text="",
                    explanation=f"A apărut o eroare tehnică la generarea recomandării: {e}",
                    sources=sources,
                    candidates=None
                )

        print(f"Applying self-consistency recommendation logic for high-risk clause {clause.id}...")
        candidates = []

        for i in range(3):
            try:
                cand_data = self._call_reformatter(True, clause, risk_assessment.issues, context_str)
                cand_text = cand_data.get("reformulated_text", "")
                if cand_text:
                    candidates.append(cand_text)
                    print(f"Generated candidate {i+1} successfully.")
            except Exception as e:
                print(f"Error generating candidate {i+1} for clause {clause.id}: {e}")

        if not candidates:
            try:
                data = self._call_reformatter(False, clause, risk_assessment.issues, context_str)
                return RecommendationDTO(
                    clause_id=clause.id,
                    original_text=clause.text,
                    reformulated_text=data.get("reformulated_text", ""),
                    explanation=data.get("explanation", ""),
                    sources=sources,
                    candidates=[]
                )
            except Exception as e:
                return RecommendationDTO(
                    clause_id=clause.id,
                    original_text=clause.text,
                    reformulated_text="",
                    explanation=f"Nu s-au putut genera propuneri de reformulare din cauza unei erori tehnice: {e}",
                    sources=sources,
                    candidates=[]
                )

        try:
            opt_1 = candidates[0]
            opt_2 = candidates[1] if len(candidates) > 1 else opt_1
            opt_3 = candidates[2] if len(candidates) > 2 else opt_1
            
            selection_human = SELECTION_PROMPT.format(
                original_text=clause.text,
                opt_1=opt_1,
                opt_2=opt_2,
                opt_3=opt_3,
                context=context_str
            )
            
            prompt = [
                ("system", SYSTEM_PROMPT),
                ("human", selection_human)
            ]
            
            response = self.llm.invoke(prompt)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n", "", content)
                content = re.sub(r"\n```$", "", content)
                
            final_data = json.loads(content)
            
            return RecommendationDTO(
                clause_id=clause.id,
                original_text=clause.text,
                reformulated_text=final_data.get("reformulated_text", opt_1),
                explanation=final_data.get("explanation", "Varianta sintetizată din propunerile independente."),
                sources=sources,
                candidates=candidates
            )
        except Exception as e:
            print(f"Error executing final selection call for clause {clause.id}: {e}")
            return RecommendationDTO(
                clause_id=clause.id,
                original_text=clause.text,
                reformulated_text=candidates[0], # Return the first candidate as fallback
                explanation="Varianta preluată din prima propunere independentă din cauza eșecului procesului de selecție.",
                sources=sources,
                candidates=candidates
            )

    def generate_report(self, results: list[dict], output_path: str) -> str:
        """
        Compiles the final Markdown audit report from workflow results
        and saves it to output_path.
        """
        # Calculate summary statistics
        total_clauses = len(results)
        risks_count = {
            RiskLevel.RIDICAT: 0,
            RiskLevel.MEDIU: 0,
            RiskLevel.SCAZUT: 0,
            RiskLevel.CONFORM: 0,
            RiskLevel.NECUNOSCUT: 0
        }
        
        metadata = None
        for res in results:
            risk_lvl = res["risk"].risk_level
            risks_count[risk_lvl] = risks_count.get(risk_lvl, 0) + 1
            if "metadata" in res:
                metadata = res["metadata"]

        report_md = "# RAPORT DE AUDIT JURIDIC - ANALIZĂ DE RISC CONTRACTUAL\n\n"

        if metadata:
            report_md += "## 1. Informații Generale Contract\n\n"
            report_md += "| Proprietate | Valoare |\n"
            report_md += "| --- | --- |\n"
            report_md += f"| **Titlu Contract** | {metadata.title} |\n"
            report_md += f"| **Număr Pagini** | {metadata.page_count} |\n"
            
            parties_str = " / ".join([p.name for p in metadata.parties])
            report_md += f"| **Părți Contractante** | {parties_str or 'Nespecificate'} |\n"
            report_md += f"| **Data Semnării** | {metadata.signing_date or 'Nespecificată'} |\n"
            report_md += f"| **Data Intrării în Vigoare** | {metadata.effective_date or 'Nespecificată'} |\n"
            report_md += f"| **Valoare Contract** | {metadata.value} |\n"
            report_md += f"| **Durată Contract** | {metadata.duration} |\n\n"
            
        # Add executive summary
        report_md += "## 2. Rezumat Executiv Risc\n\n"
        report_md += f"În total au fost analizate **{total_clauses}** clauze contractuale extrase din document. Distribuția nivelului de risc este următoarea:\n\n"
        report_md += f"- 🔴 **Risc RIDICAT**: {risks_count[RiskLevel.RIDICAT]} clauze\n"
        report_md += f"- 🟡 **Risc MEDIU**: {risks_count[RiskLevel.MEDIU]} clauze\n"
        report_md += f"- 🔵 **Risc SCĂZUT**: {risks_count[RiskLevel.SCAZUT]} clauze\n"
        report_md += f"- 🟢 **Conforme (Fără risc)**: {risks_count[RiskLevel.CONFORM]} clauze\n"
        report_md += f"- ⚫ **Necunoscute (Lipsă context RAG)**: {risks_count[RiskLevel.NECUNOSCUT]} clauze\n\n"

        high_risk_pct = (risks_count[RiskLevel.RIDICAT] / total_clauses * 100) if total_clauses > 0 else 0
        if high_risk_pct > 20:
            report_md += "> [!CAUTION]\n"
            report_md += f"> **Atenție:** Documentul conține un procent ridicat de clauze cu risc ridicat ({high_risk_pct:.1f}%). Se recomandă renegocierea imediată conform recomandărilor de mai jos.\n\n"
        elif risks_count[RiskLevel.RIDICAT] > 0 or risks_count[RiskLevel.MEDIU] > 0:
            report_md += "> [!WARNING]\n"
            report_md += "> **Atenție:** Au fost identificate clauze cu neconformități legale care necesită atenție sporită.\n\n"
        else:
            report_md += "> [!NOTE]\n"
            report_md += "> **Felicitări:** Contractul prezintă un profil de risc foarte curat și respectă majoritatea normelor legislative standard.\n\n"

        report_md += "## 3. Analiza Detaliată și Recomandări de Reformulare\n\n"
        
        clause_index = 1
        for res in results:
            clause = res["clause"]
            risk = res["risk"]
            rec = res["rec"]

            if risk.risk_level == RiskLevel.RIDICAT:
                risk_icon = "🔴 RIDICAT"
            elif risk.risk_level == RiskLevel.MEDIU:
                risk_icon = "🟡 MEDIU"
            elif risk.risk_level == RiskLevel.SCAZUT:
                risk_icon = "🔵 SCĂZUT"
            elif risk.risk_level == RiskLevel.CONFORM:
                risk_icon = "🟢 CONFORM"
            else:
                risk_icon = "⚫ NECUNOSCUT"
                
            report_md += f"### Clauza {clause_index}: {clause.section} (Pagina {clause.page})\n"
            report_md += f"- **Tip Clauză**: `{clause.type.value}`\n"
            report_md += f"- **Evaluare Risc**: **{risk_icon}**\n"
            
            if risk.issues:
                report_md += "- **Deficiențe constatate**:\n"
                for issue in risk.issues:
                    report_md += f"  - {issue}\n"
                    
            if risk.references:
                report_md += f"- **Surse de referință în corpus**: {', '.join([f'`{r}`' for r in risk.references])}\n"
                
            report_md += "\n#### Textul Original al Clauzei:\n"
            report_md += f"```text\n{clause.text}\n```\n"

            if rec.reformulated_text:
                report_md += "\n#### Reformulare Propusă:\n"
                report_md += f"```text\n{rec.reformulated_text}\n```\n"
                report_md += f"\n**Explicație Juridică:**\n{rec.explanation}\n"
                
            report_md += "\n---\n\n"
            clause_index += 1

        report_md += "\n*Raport generat în mod automat de către agentul de analiză juridică AI la data de 04.06.2026.*\n"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
            
        print(f"Markdown report compiled and saved to '{output_path}'.")
        return report_md
