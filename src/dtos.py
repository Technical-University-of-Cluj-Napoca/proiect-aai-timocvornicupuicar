from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ClauseType(str, Enum):
    PENALITATE = "penalitate"
    OBLIGATIE = "obligatie"
    DREPT = "drept"
    FORTA_MAJORA = "forta_majora"
    CONFIDENTIALITATE = "confidentialitate"
    REZILIERE = "reziliere"
    DATE_PERSONALE = "date_personale"
    ALTELE = "altele"

class RiskLevel(str, Enum):
    RIDICAT = "RIDICAT"
    MEDIU = "MEDIU"
    SCAZUT = "SCAZUT"
    CONFORM = "CONFORM"
    NECUNOSCUT = "NECUNOSCUT"

class PartyDTO(BaseModel):
    name: str = Field(description="Numele/Denumirea completă a părții contractante")
    cui_cnp: str = Field(description="Codul Unic de Înregistrare (CUI) sau Codul Numeric Personal (CNP)")
    address: str = Field(description="Adresa sediului social sau a domiciliului părții")

class SectionDTO(BaseModel):
    title: str = Field(description="Titlul secțiunii sau al articolului din contract")
    start_page: int = Field(description="Pagina la care începe secțiunea (1-indexed)")

class ClauseDTO(BaseModel):
    id: str = Field(description="Identificator unic al clauzei (ex: 'art_5_clz_2')")
    section: str = Field(description="Secțiunea/Articolul din care face parte clauza")
    text: str = Field(description="Textul integral al clauzei")
    page: int = Field(description="Pagina la care se află clauza (1-indexed)")
    type: ClauseType = Field(description="Tipul clauzei contractuale")

class DocumentMetadataDTO(BaseModel):
    title: str = Field(description="Titlul contractului")
    page_count: int = Field(description="Numărul total de pagini")
    parties: List[PartyDTO] = Field(default_factory=list, description="Lista părților contractante")
    signing_date: Optional[str] = Field(None, description="Data semnării contractului")
    effective_date: Optional[str] = Field(None, description="Data intrării în vigoare")
    value: str = Field(description="Valoarea contractului cu monedă (sau 'Nespecificată')")
    duration: str = Field(description="Durata contractului (sau 'Nedeterminată')")

class ParsedDocumentDTO(BaseModel):
    metadata: DocumentMetadataDTO = Field(description="Metadatele extrase din document")
    sections: List[SectionDTO] = Field(default_factory=list, description="Lista secțiunilor identificate")
    clauses: List[ClauseDTO] = Field(default_factory=list, description="Lista clauzelor extrase și clasificate")

class RetrievalResultDTO(BaseModel):
    text: str = Field(description="Fragmentul de text juridic recuperat")
    source: str = Field(description="Sursa fragmentului (numele fișierului/documentului)")
    score: float = Field(description="Scorul de similaritate cosinus normalizat")

class RiskAssessmentDTO(BaseModel):
    clause_id: str = Field(description="Identificatorul unic al clauzei analizate")
    risk_level: RiskLevel = Field(description="Nivelul de risc asociat clauzei")
    issues: List[str] = Field(default_factory=list, description="Lista problemelor sau non-conformităților identificate")
    references: List[str] = Field(default_factory=list, description="Referințele din corpus care susțin evaluarea")
    context_was_empty: bool = Field(False, description="True dacă nu a fost recuperat niciun context relevant")

class RecommendationDTO(BaseModel):
    clause_id: str = Field(description="Identificatorul unic al clauzei corelate")
    original_text: str = Field(description="Textul original al clauzei contractuale")
    reformulated_text: str = Field(description="Textul reformulat propus, conform cu legislația")
    explanation: str = Field(description="Explicația/Justificarea juridică a reformulării")
    sources: List[str] = Field(default_factory=list, description="Sursele legislative utilizate ca fundamentare")
    candidates: Optional[List[str]] = Field(None, description="Opțiunile candidate generate (pentru risc RIDICAT, în sistemul self-consistency)")
