import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Define output path
DATA_DIR = os.path.abspath("data")
os.makedirs(DATA_DIR, exist_ok=True)

CONTRACT_1 = {
    "title": "CONTRACT DE FURNIZARE SI PRESTARI SERVICII IT - NR. 412 / 2026",
    "paragraphs": [
        "Preambul: Prezentul contract s-a incheiat astazi, 04.06.2026, intre SC TECH SOLUTIONS SRL (Prestator) cu sediul in Cluj-Napoca, CUI RO123456, si SC RETAIL GRUP SRL (Beneficiar) cu sediul in Bucuresti, CUI RO789101.",
        "Articolul 1. Obiectul contractului: Furnizarea de echipamente IT si dezvoltarea unei platforme software de e-commerce pentru Beneficiar conform Anexei 1.",
        "Articolul 2. Durata contractului: Contractul intra in vigoare la data semnarii de catre ambele parti si este valabil pentru o perioada de 12 luni.",
        "Articolul 3. Valoarea contractului: Valoarea totala a contractului este de 50.000 EUR plus TVA, platibila conform graficului de plati.",
        "Articolul 4. Penalitati de intarziere: In caz de neexecutare sau executare cu intarziere a obligatiilor de livrare, Prestatorul datoreaza Beneficiarului o penalitate de 1% pe zi din valoarea contractului. Beneficiarul nu va fi tinut sa plateasca nicio penalitate pentru intarzieri la plata facturilor primite.",
        "Articolul 5. Prelucrarea datelor personale: Partile convin ca orice date cu caracter personal colectate in executarea contractului sa fie prelucrate in scopuri de marketing direct si transmise catre parteneri terti din afara UE fara obligatia de a solicita consimtamantul persoanelor vizate.",
        "Articolul 6. Forta majora: Forta majora inlatura raspunderea partilor. Prin forta majora se intelege orice imprejurare greu de evitat sau controlat de catre partile contractante.",
        "Articolul 7. Reziliere unilaterala: Beneficiarul poate rezilia unilateral contractul in orice moment, cu un preaviz scris de doar 24 de ore, fara a datora nicio despagubire Prestatorului. Prestatorul nu are dreptul de a rezilia unilateral contractul sub nicio forma.",
        "Articolul 8. Cesiunea contractului: Prestatorul are dreptul de a ceda integral sau partial obligatiile si drepturile sale din acest contract catre orice alta entitate, fara a fi necesar acordul Beneficiarului.",
        "Articolul 9. Limitarea raspunderii: Prestatorul nu raspunde pentru niciun fel de daune directe, indirecte, speciale sau accidentale provocate Beneficiarului, chiar daca acestea sunt rezultatul intentiei sale deliberate sau a unei culpe grave din partea angajatilor sai.",
        "Articolul 10. Confidentialitate: Partile se obliga sa pastreze confidentialitatea informatiilor primite pe parcursul derularii contractului. Aceasta obligatie de confidentialitate se prelungeste pe o perioada de timp nedeterminata si nu inceteaza niciodata dupa terminarea contractului.",
        "Articolul 11. Jurisdictie si arbitraj: Orice neintelegeri aparute vor fi solutionate exclusiv de catre instanta de arbitraj aleasa unilateral de catre Beneficiar, iar decizia va fi definitiva si executorie."
    ]
}

CONTRACT_2 = {
    "title": "CONTRACT CADRU DE PRESTARI SERVICII CONSULTANTA - NR. 89 / 2026",
    "paragraphs": [
        "Preambul: Prezentul contract s-a incheiat la data de 01.05.2026 intre CONSULTING PLUS SRL (Prestator) cu sediul in Cluj-Napoca, CUI RO55555, si GLOBAL LOGISTICS SRL (Beneficiar) cu sediul in Oradea, CUI RO66666.",
        "Articolul 1. Obiectul contractului: Prestarea de servicii de consultanta in management si optimizarea fluxurilor logistice.",
        "Articolul 2. Valoarea si durata: Valoarea contractului este de 12.000 EUR. Contractul este incheiat pe o durata de 6 luni.",
        "Articolul 3. Penalitati contractuale: Daca Prestatorul nu livreaza rapoartele de consultanta la termen, va fi penalizat cu 500 EUR pe zi. Daca Beneficiarul intarzie plata facturilor cu mai mult de 30 de zile, nu se vor aplica penalitati.",
        "Articolul 4. Protectia datelor: Datele cu caracter personal colectate de Prestator vor fi stocate intr-o baza de date comuna si folosite pentru publicitate, fara obligatia de notificare sau consimtamant.",
        "Articolul 5. Reziliere si litigii: Rezilierea se face cu preaviz de 3 zile de catre Beneficiar. Eventualele litigii vor fi trimise spre solutionare instantei arbitrale alese de Beneficiar."
    ]
}

def generate_contract_pdf(file_path, contract_data):
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, contract_data["title"])
    
    c.setFont("Helvetica", 10)
    y = 700
    for para in contract_data["paragraphs"]:
        words = para.split(" ")
        line = ""
        for word in words:
            if len(line) + len(word) < 95:
                line += " " + word
            else:
                c.drawString(50, y, line.strip())
                y -= 15
                line = word
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = 750
        if line:
            c.drawString(50, y, line.strip())
            y -= 25
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750
    c.save()
    print(f"Generated contract PDF: {file_path}")

def main():
    dest_1 = os.path.join(DATA_DIR, "contract_exemplu.pdf")
    generate_contract_pdf(dest_1, CONTRACT_1)
    
    dest_2 = os.path.join(DATA_DIR, "contract_exemplu_2.pdf")
    generate_contract_pdf(dest_2, CONTRACT_2)
    
    print("Sample contracts generation completed successfully!")

if __name__ == "__main__":
    main()
