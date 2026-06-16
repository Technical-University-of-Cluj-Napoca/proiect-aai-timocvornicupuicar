import os
import re
import json
import pdfplumber
from dotenv import load_dotenv

from src.dtos import (
    ClauseType,
    ClauseDTO,
    SectionDTO,
    PartyDTO,
    DocumentMetadataDTO,
    ParsedDocumentDTO
)
from src.utils import get_llm

load_dotenv()

SECTION_PATTERN = re.compile(
    r"^\s*(Articolul|Clauza|Art\.|Preambul)\s+(\d+|\b)\.?(.*)",
    re.IGNORECASE
)

METADATA_SYSTEM_PROMPT = (
    "Ești un asistent juridic expert în analiza contractelor românești. Sarcina ta este să extragi metadatele din textul furnizat "
    "(care reprezintă primele pagini ale unui contract) și să le returnezi EXCLUSIV ca un obiect JSON valid, fără alte explicații sau blocuri markdown.\n\n"
    "Formatul JSON trebuie să fie:\n"
    "{\n"
    "  \"title\": \"Titlul oficial al contractului (dacă nu e clar, generează unul reprezentativ)\",\n"
    "  \"parties\": [\n"
    "    {\n"
    "      \"name\": \"Denumirea completă a părții contractante\",\n"
    "      \"cui_cnp\": \"CUI sau CNP (dacă există în text, altfel 'Nespecificat')\",\n"
    "      \"address\": \"Adresa sediului social sau domiciliul (dacă există, altfel 'Nespecificată')\"\n"
    "    }\n"
    "  ],\n"
    "  \"signing_date\": \"Data semnării contractului în format YYYY-MM-DD (dacă există, altfel null)\",\n"
    "  \"effective_date\": \"Data intrării în vigoare în format YYYY-MM-DD (dacă există, altfel null)\",\n"
    "  \"value\": \"Valoarea contractului cu monedă (ex: '50.000 EUR plus TVA', sau 'Nespecificată')\",\n"
    "  \"duration\": \"Durata contractului (ex: '12 luni', sau 'Nedeterminată')\"\n"
    "}"
)

CLASSIFY_SYSTEM_PROMPT = (
    "Ești un expert în drept contractual. Clasifică textul clauzei furnizate într-una dintre următoarele categorii:\n"
    "- 'penalitate': clauze referitoare la penalități de întârziere, daune-interese, dobânzi penalizatoare sau sancțiuni financiare în caz de neexecutare.\n"
    "- 'obligatie': obligații generale ale prestatorului, beneficiarului sau obligații comune de livrare/prestare.\n"
    "- 'drept': drepturi ale părților, opțiuni de suspendare sau compensare, prerogative contractuale.\n"
    "- 'forta_majora': clauze privind forța majoră, cazul fortuit, evenimente imprevizibile și exonerarea de răspundere.\n"
    "- 'confidentialitate': clauze de confidențialitate, acorduri de nedivulgare (NDA), protecția secretului comercial.\n"
    "- 'reziliere': clauze referitoare la încetarea contractului, reziliere, rezoluțiune, denunțare unilaterală sau pacte comisorii.\n"
    "- 'date_personale': clauze privind prelucrarea datelor cu caracter personal, protecția datelor, GDPR.\n"
    "- 'altele': clauze care nu se încadrează clar în categoriile de mai sus (ex: limitarea răspunderii, cesiune, litigii, limbă, notificări).\n\n"
    "Răspunde strict cu unul dintre aceste cuvinte cheie în limba engleză (cum sunt scrise mai sus, cu litere mici): penalitate, obligatie, drept, forta_majora, confidentialitate, reziliere, date_personale, altele."
)

class DocumentParserAgent:
    def __init__(self):
        self._llm = None
        
    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def _extract_metadata_with_llm(self, text: str) -> DocumentMetadataDTO:
        """Calls the LLM to parse structural metadata from the first 2 pages."""
        try:
            prompt = [
                ("system", METADATA_SYSTEM_PROMPT),
                ("human", f"Iată textul de pe primele pagini ale contractului:\n\n{text}")
            ]
            response = self.llm.invoke(prompt)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n", "", content)
                content = re.sub(r"\n```$", "", content)
                
            data = json.loads(content)
            
            parties_dto = []
            for party in data.get("parties", []):
                parties_dto.append(PartyDTO(
                    name=party.get("name", "Nespecificat"),
                    cui_cnp=party.get("cui_cnp", "Nespecificat"),
                    address=party.get("address", "Nespecificată")
                ))
                
            return DocumentMetadataDTO(
                title=data.get("title", "Contract"),
                page_count=0,
                parties=parties_dto,
                signing_date=data.get("signing_date"),
                effective_date=data.get("effective_date"),
                value=data.get("value", "Nespecificată"),
                duration=data.get("duration", "Nedeterminată")
            )
        except Exception as e:
            print(f"Error extracting metadata via LLM: {e}. Falling back to default metadata.")
            return DocumentMetadataDTO(
                title="Contract de Furnizare",
                page_count=0,
                parties=[],
                value="Nespecificată",
                duration="Nedeterminată"
            )

    def _classify_clause(self, text: str) -> ClauseType:
        """Hybrid clause classifier: checks keywords first, then falls back to LLM."""
        text_lower = text.lower()
        

        if any(kw in text_lower for kw in ["penalitat", "penaliz", "daune-interese", "dobanda penalizatoare", "procent pe zi"]):
            return ClauseType.PENALITATE
        elif any(kw in text_lower for kw in ["forta majora", "forță majoră", "caz fortuit", "exonerat de raspundere"]):
            return ClauseType.FORTA_MAJORA
        elif any(kw in text_lower for kw in ["confidential", "confidențial", "secret", "nedivulg", "nda"]):
            return ClauseType.CONFIDENTIALITATE
        elif any(kw in text_lower for kw in ["rezilia", "inceta", "înceta", "preaviz de", "pact comisoriu", "denunta unilateral"]):
            return ClauseType.REZILIERE
        elif any(kw in text_lower for kw in ["date cu caracter personal", "date personale", "gdpr", "prelucrarea datelor", "dpo"]):
            return ClauseType.DATE_PERSONALE
            

        try:
            prompt = [
                ("system", CLASSIFY_SYSTEM_PROMPT),
                ("human", f"Clasifică această clauză contractuală:\n\n{text}")
            ]
            response = self.llm.invoke(prompt)
            content = response.content.strip().lower() if hasattr(response, 'content') else str(response).strip().lower()
            
            for clause_enum in ClauseType:
                if clause_enum.value in content:
                    return clause_enum
        except Exception as e:
            print(f"LLM classification failed for clause: {e}")
            
        return ClauseType.ALTELE

    def parse(self, pdf_path: str) -> ParsedDocumentDTO:
        """Parses a contract PDF and structures it into a ParsedDocumentDTO."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF-ul contractului nu a fost găsit la: {pdf_path}")
            
        print(f"Parsing document: {pdf_path}...")
        
        sections = []
        clauses = []
        first_pages_text = ""
        full_text = ""
        page_count = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)

                for i in range(min(2, page_count)):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        first_pages_text += page_text + "\n"

                current_section_title = "Preambul"
                current_clause_text = ""
                current_clause_page = 1
                clause_index = 1

                sections.append(SectionDTO(title="Preambul", start_page=1))
                
                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                        
                    lines = page_text.split("\n")
                    for line in lines:
                        match = SECTION_PATTERN.match(line)
                        if match:

                            if current_clause_text.strip():
                                clause_id = f"clz_{clause_index}"
                                clause_type = self._classify_clause(current_clause_text)
                                clauses.append(ClauseDTO(
                                    id=clause_id,
                                    section=current_section_title,
                                    text=current_clause_text.strip(),
                                    page=current_clause_page,
                                    type=clause_type
                                ))
                                clause_index += 1

                            header_type = match.group(1).title()
                            header_num = match.group(2)
                            header_rest = match.group(3).strip()
                            
                            new_title = f"{header_type} {header_num} {header_rest}".strip()
                            current_section_title = new_title
                            current_clause_text = line + "\n"
                            current_clause_page = page_num

                            sections.append(SectionDTO(title=new_title, start_page=page_num))
                        else:
                            current_clause_text += line + "\n"

                if current_clause_text.strip():
                    clause_id = f"clz_{clause_index}"
                    clause_type = self._classify_clause(current_clause_text)
                    clauses.append(ClauseDTO(
                        id=clause_id,
                        section=current_section_title,
                        text=current_clause_text.strip(),
                        page=current_clause_page,
                        type=clause_type
                    ))
                    
        except Exception as e:
            print(f"Error opening or reading PDF: {e}")
            return ParsedDocumentDTO(
                metadata=DocumentMetadataDTO(
                    title="Eroare incarcare document",
                    page_count=0,
                    parties=[],
                    value="Nespecificată",
                    duration="Nedeterminată"
                ),
                sections=[],
                clauses=[]
            )

        metadata = self._extract_metadata_with_llm(first_pages_text)
        metadata.page_count = page_count

        unique_sections = []
        seen_titles = set()
        for sec in sections:
            if sec.title not in seen_titles:
                unique_sections.append(sec)
                seen_titles.add(sec.title)
                
        parsed_doc = ParsedDocumentDTO(
            metadata=metadata,
            sections=unique_sections,
            clauses=clauses
        )
        
        print(f"Parsing complete. Extracted {len(unique_sections)} sections and {len(clauses)} clauses.")
        return parsed_doc
