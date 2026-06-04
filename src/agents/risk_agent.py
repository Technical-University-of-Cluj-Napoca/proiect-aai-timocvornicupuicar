import os
import re
import json
from dotenv import load_dotenv

from src.dtos import ClauseDTO, RetrievalResultDTO, RiskAssessmentDTO, RiskLevel
from src.utils import get_llm

load_dotenv()

SYSTEM_PROMPT = (
    "Ești un expert în drept și evaluator de risc contractual din România.\n"
    "Sarcina ta este să evaluezi o clauză dintr-un contract în raport cu contextul legislativ oferit ca referință.\n\n"
    "REGULI PENTRU EVALUARE:\n"
    "1. Bazează-te EXCLUSIV pe documentele din context. Nu inventa articole, legi sau surse. Orice referință adăugată care nu se află în context este considerată o halucinație și o eroare gravă.\n"
    "2. Clasifică riscul în:\n"
    "   - 'RIDICAT': clauza încalcă prevederi imperative ale legii (de ex. excluderea răspunderii pentru culpă gravă, lipsa totală a consimțământului GDPR, clauze complet asimetrice).\n"
    "   - 'MEDIU': clauza este ambiguă, are un dezechilibru parțial sau omite detalii obligatorii (de ex. termene neclare de notificare, forță majoră definită vag).\n"
    "   - 'SCAZUT': clauza este acceptabilă, dar are vulnerabilități minore.\n"
    "   - 'CONFORM': clauza respectă pe deplin normele legale și bunele practici din context.\n"
    "3. Returnează răspunsul tău EXCLUSIV ca un text JSON valid, respectând structura de mai jos, fără blocuri markdown de cod (de ex. ```json) și fără alte mesaje:\n\n"
    "{\n"
    "  \"clause_id\": \"id-ul clauzei analizate\",\n"
    "  \"risk_level\": \"RIDICAT | MEDIU | SCAZUT | CONFORM\",\n"
    "  \"issues\": [\"Listă de probleme/riscuri identificate în limba română\"],\n"
    "  \"references\": [\"Listă cu numele fișierelor din context care reglementează această problemă (ex: 'gdpr_regulament_2016_679.pdf')\"]\n"
    "}"
)

class RiskAssessmentAgent:
    def __init__(self):
        self._llm = None
        
    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def assess(self, clause: ClauseDTO, context_chunks: list[RetrievalResultDTO]) -> RiskAssessmentDTO:
        """
        Assesses the risk level of a clause based on the retrieved context chunks.
        If context is empty, returns NECUNOSCUT immediately without LLM call.
        """
        if not context_chunks:
            print(f"Context for clause {clause.id} is empty. Skipping LLM call.")
            return RiskAssessmentDTO(
                clause_id=clause.id,
                risk_level=RiskLevel.NECUNOSCUT,
                issues=["Nu s-a putut evalua riscul deoarece nu au fost gasite documente legislative relevante in corpus."],
                references=[],
                context_was_empty=True
            )

        formatted_context = ""
        for i, chunk in enumerate(context_chunks):
            formatted_context += f"--- Document Ref: {chunk.source} (Similarity Score: {chunk.score:.4f}) ---\n"
            formatted_context += f"{chunk.text}\n\n"
            
        human_prompt = (
            f"Clauza de analizat:\n"
            f"ID clauză: {clause.id}\n"
            f"Secțiune contract: {clause.section}\n"
            f"Text clauză: {clause.text}\n\n"
            f"Context Legislativ de Referință:\n"
            f"{formatted_context}"
        )
        
        try:
            prompt = [
                ("system", SYSTEM_PROMPT),
                ("human", human_prompt)
            ]
            response = self.llm.invoke(prompt)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n", "", content)
                content = re.sub(r"\n```$", "", content)
                
            data = json.loads(content)

            risk_str = data.get("risk_level", "NECUNOSCUT").upper()
            try:
                risk_level = RiskLevel(risk_str)
            except ValueError:
                if "RIDICAT" in risk_str:
                    risk_level = RiskLevel.RIDICAT
                elif "MEDIU" in risk_str:
                    risk_level = RiskLevel.MEDIU
                elif "SCAZUT" in risk_str or "SCĂZUT" in risk_str:
                    risk_level = RiskLevel.SCAZUT
                elif "CONFORM" in risk_str:
                    risk_level = RiskLevel.CONFORM
                else:
                    risk_level = RiskLevel.NECUNOSCUT
                    
            return RiskAssessmentDTO(
                clause_id=clause.id,
                risk_level=risk_level,
                issues=data.get("issues", []),
                references=data.get("references", []),
                context_was_empty=False
            )
            
        except Exception as e:
            print(f"Error assessing risk for clause {clause.id}: {e}")
            return RiskAssessmentDTO(
                clause_id=clause.id,
                risk_level=RiskLevel.NECUNOSCUT,
                issues=[f"Eroare tehnica la evaluarea riscului: {str(e)}"],
                references=[],
                context_was_empty=False
            )
