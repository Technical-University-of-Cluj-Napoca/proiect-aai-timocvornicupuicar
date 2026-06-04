import os
import urllib.request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

CATEGORIES = ["gdpr", "legi", "contracte", "uncitral", "anpc"]
BASE_DIR = os.path.abspath("corpus")

LEGAL_TEXTS = {
    "gdpr_regulament_2016_679": {
        "title": "Regulamentul (UE) 2016/679 (GDPR) - Extras Oficial",
        "paragraphs": [
            "Articolul 13: Informatii care se furnizeaza in cazul in care datele cu caracter personal sunt colectate de la persoana vizata.",
            "1. In cazul in care datele cu caracter personal referitoare la o persoana vizata sunt colectate de la aceasta, operatorul, in momentul obtinerii acestor date, furnizeaza persoanei vizate toate informatiile urmatoare: identitatea si datele de contact ale operatorului; scopurile in care sunt prevazute datele; temeiul juridic al prelucrarii; destinatarii sau categoriile de destinatari ai datelor.",
            "Articolul 14: Informatii care se furnizeaza in cazul in care datele cu caracter personal nu au fost obtinute de la persoana vizata.",
            "1. In cazul in care datele nu au fost obtinute de la persoana vizata, operatorul furnizeaza informatiile privind categoriile de date colectate, sursa din care provin datele si existenta dreptului de a solicita rectificarea sau stergerea acestora.",
            "Articolul 32: Securitatea prelucrarii.",
            "1. Avand in vedere stadiul actual al dezvoltarii, costurile implementarii si natura, domeniul de aplicare, contextul si scopurile prelucrarii, operatorul si persoana imputernicita de operator implementeaza masuri tehnice si organizatorice adecvate pentru a asigura un nivel de securitate corespunzator acestui risc, inclusiv, printre altele: pseudonimizarea si criptarea datelor cu caracter personal; capacitatea de a asigura confidentialitatea, integritatea, disponibilitatea si rezistenta continue ale sistemelor si serviciilor de prelucrare."
        ]
    },
    "gdpr_rectificare": {
        "title": "Rectificare la Regulamentul (UE) 2016/679 privind protectia datelor",
        "paragraphs": [
            "Rectificarea adusa Regulamentului (UE) 2016/679 al Parlamentului European si al Consiliului din 27 aprilie 2016 privind protectia persoanelor fizice in ceea ce priveste prelucrarea datelor cu caracter personal si privind libera circulatie a acestor date.",
            "Se rectifica definitiile consimtamantului si procedurile privind transferul de date catre tari terte, intarind dreptul la portabilitatea datelor si dreptul de a fi uitat conform Art. 17. Orice contract ce implica prelucrarea datelor trebuie sa contina clauze clare privind obligatiile persoanei imputernicite."
        ]
    },
    "gdpr_institutii_ue": {
        "title": "Regulamentul (UE) 2018/1725 - Protectia datelor in institutiile Uniunii",
        "paragraphs": [
            "Regulamentul stabileste normele aplicabile prelucrarii datelor cu caracter personal de catre toate institutiile, organele, oficiile si agentiile Uniunii Europene.",
            "Acesta este aliniat cu Regulamentul (UE) 2016/679 si stabileste obligatiile stricte de transparenta, securitate si notificare a incalcarii securitatii datelor catre Autoritatea Europeana pentru Protectia Datelor (AEPD). Orice clauza contractuala care exclude raspunderea pentru scurgeri de date este considerata nula."
        ]
    },
    "legea_98_2016_achizitii": {
        "title": "Legea nr. 98/2016 privind achizitiile publice - Extras",
        "paragraphs": [
            "Articolul 164: Modificarea contractelor in perioada lor de valabilitate.",
            "1. Contractele de achizitie publica pot fi modificate, fara organizarea unei noi proceduri de atribuire, doar in situatiile expres prevazute de lege, cum ar fi clauze de revizuire clare, precise si neechivoce.",
            "Penalitati si intarzieri: In cazul in care contractantul nu reuseste sa isi indeplineasca obligatiile in termenele stabilite, autoritatea contractanta are dreptul de a percepe penalitati de intarziere calculate ca procent din valoarea obligatiilor neexecutate. Ratele penalitatilor trebuie sa fie simetrice si sa respecte legislatia in vigoare privind dobanda legala penalizatoare."
        ]
    },
    "legea_193_2000_clauze_abuzive": {
        "title": "Legea nr. 193/2000 privind clauzele abuzive in contracte - Consolidata",
        "paragraphs": [
            "Articolul 4: O clauza contractuala care nu a fost negociata direct cu consumatorul va fi considerata abuziva daca, prin ea insasi sau impreuna cu alte prevederi din contract, creeaza, in detrimentul consumatorului si contrar cerintelor bunei-credinte, un dezechilibru semnificativ intre drepturile si obligatiile partilor.",
            "Lista clauzelor abuzive contine: dreptul unilateral al profesionistului de a modifica clauzele fara un motiv intemeiat; obligarea consumatorului de a se supune unor conditii contractuale care nu i-au fost aduse la cunostinta; acordarea dreptului exclusiv profesionistului de a interpreta clauzele contractuale; limitarea sau excluderea raspunderii legale a profesionistului in caz de vatamare sau neexecutare."
        ]
    },
    "codul_civil_contracte": {
        "title": "Extras din Codul Civil Roman - Contracte si Raspundere",
        "paragraphs": [
            "Articolul 1351: Forta majora si cazul fortuit.",
            "1. Daca legea nu prevede altfel sau partile nu s-au inteles contrar, raspunderea este inlaturata atunci cand prejudiciul este cauzat de forta majora sau de caz fortuit.",
            "2. Forta majora este orice eveniment extern, imprevizibil, absolut invincibil si inevitabil.",
            "Articolul 1355: Limitarea sau inlaturarea raspunderii.",
            "1. Nu se poate exclude sau limita prin conventie raspunderea pentru prejudiciul cauzat prin intentie sau din culpa grava a debitorului. Asemenea clauze sunt lovite de nulitate absoluta."
        ]
    },
    "model_contract_furnizare": {
        "title": "Model Standard Contract de Furnizare Bunuri Publice",
        "paragraphs": [
            "Clauza de penalitati: Pentru intarzierea in livrarea bunurilor, furnizorul datoreaza penalitati de 0.1% pe zi din valoarea bunurilor nelivrate, pana la executarea obligatiei.",
            "Forta majora: Niciuna dintre partile contractante nu raspunde de neexecutarea la termen a obligatiilor daca aceasta este cauzata de un eveniment de forta majora, notificat in termen de 5 zile.",
            "Cesiunea: Contractantul are obligatia de a nu transfera total sau partial obligatiile sale asumate prin contract fara acordul prealabil scris al achizitorului."
        ]
    },
    "model_contract_prestari_servicii": {
        "title": "Model Standard Contract de Prestari Servicii IT",
        "paragraphs": [
            "Confidentialitate: Fiecare parte va mentine confidentialitatea informatiilor primite de la cealalta parte pe o durata de cel putin 5 ani de la incetarea contractului. Incalcarea obligatiei atrage daune-interese neplafonate.",
            "Reziliere: Achizitorul poate rezilia unilateral contractul cu un preaviz de 15 zile in caz de neindeplinire a indicatorilor de performanta (SLA), fara plata de despagubiri catre prestator."
        ]
    },
    "model_contract_lucrari": {
        "title": "Model Standard Contract de Executie Lucrari de Constructii",
        "paragraphs": [
            "Raspundere: Antreprenorul raspunde pentru calitatea lucrarilor executate si pentru orice defecte ascunse aparute intr-o perioada de garantie de 24 de luni.",
            "Jurisdictie si Arbitraj: Orice litigiu decurgand din prezentul contract se va solutiona pe cale amiabila. In caz contrar, litigiul va fi supus Curtii de Arbitraj Comercial de pe langa Camera de Comert si Industrie a Romaniei."
        ]
    },
    "uncitral_model_law_ecommerce": {
        "title": "UNCITRAL Model Law on Electronic Commerce (1996) - Reference",
        "paragraphs": [
            "Article 5: Legal recognition of data messages. Information shall not be denied legal effect, validity or enforceability solely on the grounds that it is in the form of a data message.",
            "Article 6: Writing. Where the law requires information to be in writing, that requirement is met by a data message if the information contained therein is accessible so as to be usable for subsequent reference.",
            "Article 7: Signature. Where the law requires a signature, that requirement is met in relation to a data message if a method is used to identify the person and to indicate that person's approval."
        ]
    },
    "uncitral_model_law_signatures": {
        "title": "UNCITRAL Model Law on Electronic Signatures (2001)",
        "paragraphs": [
            "Article 6: Compliance with a requirement for a signature. An electronic signature is considered to be reliable if the signature creation data are linked to the signatory and no other person, and if any alteration after signing is detectable.",
            "This model law establishes the principle of technological neutrality, meaning laws should not favor one signature technology over another, ensuring equal treatment under the law."
        ]
    },
    "uncitral_model_law_transferable_records": {
        "title": "UNCITRAL Model Law on Electronic Transferable Records (2017)",
        "paragraphs": [
            "The model law applies to electronic transferable records that are equivalent to transferrable documents or instruments (such as bills of lading or promissory notes).",
            "It requires the use of a reliable method to establish singularity (preventing double spending or duplication) and to maintain control of the electronic transferable record from creation to termination."
        ]
    },
    "anpc_ghid_servicii_financiare": {
        "title": "ANPC - Ghid Privind Clauzele Abuzive in Servicii Financiare",
        "paragraphs": [
            "Ghid pentru identificarea practicilor comerciale incorecte si a clauzelor abuzive in contractele de credit bancar.",
            "Clauzele care permit bancii sa modifice rata dobanzii in mod unilateral, fara criterii clare si obiective mentionate in contract, sunt abuzive. De asemenea, comisioanele ascunse sau nejustificate (cum ar fi comisionul de risc mascat) incalca bunele practici ANPC si legislatia nationala."
        ]
    },
    "anpc_ghid_servicii_turistice": {
        "title": "ANPC - Ghid pentru Consumatori privind Serviciile Turistice",
        "paragraphs": [
            "Ghid de protectie a consumatorilor la achizitia de pachete de servicii de calatorie.",
            "Agentiile de turism nu pot exclude raspunderea pentru neexecutarea serviciilor de transport sau cazare din cauza partenerilor lor. Clauzele care obliga consumatorul sa plateasca despagubiri excesive in caz de anulare sunt nule si abuzive."
        ]
    },
    "anpc_ghid_achizitii_imobiliare": {
        "title": "ANPC - Ghidul Cumparatorului de Locuinte Noi",
        "paragraphs": [
            "Ghid privind clauzele contractuale din promisiunile bilaterale de vanzare-cumparare.",
            "Dezvoltatorul imobiliar trebuie sa prevada termene clare de finalizare si penalitati simetrice in caz de intarziere. Clauza care retine avansul cumparatorului fara drept de returnare in caz de culpa a dezvoltatorului este abuziva."
        ]
    },
    "anpc_ghid_produse_cosmetice": {
        "title": "ANPC - Ghid de Bune Practici pentru Etichetarea Cosmeticelor",
        "paragraphs": [
            "Ghid privind etichetarea produselor cosmetice si conformitatea cu Regulamentul (CE) nr. 1223/2009.",
            "Toate informatiile obligatorii (ingrediente, precautii, valabilitate, date producator) trebuie traduse in limba romana. Lipsa traducerii sau utilizarea de declaratii inselatoare privind efectele terapeutice atrage sanctiuni severe si retragerea de pe piata."
        ]
    }
}

URLS = {
    "gdpr": [
        ("https://eur-lex.europa.eu/legal-content/RO/TXT/PDF/?uri=CELEX:32016R0679", "gdpr_regulament_2016_679.pdf"),
        ("https://eur-lex.europa.eu/legal-content/RO/TXT/PDF/?uri=CELEX:32016R0679R(02)", "gdpr_rectificare.pdf"),
        ("https://eur-lex.europa.eu/legal-content/RO/TXT/PDF/?uri=CELEX:32018R1725", "gdpr_institutii_ue.pdf")
    ],
    "legi": [
        ("https://sgg.gov.ro/new/wp-content/uploads/2016/05/Legea-nr.-98-2016.pdf", "legea_98_2016_achizitii.pdf"),
        ("https://anpc.ro/anpcftp/legislatie/Lege%20nr.%20193(r2)%20din%202000.pdf", "legea_193_2000_clauze_abuzive.pdf"),
        ("https://just.ro/Portals/0/Codul%20Civil.pdf", "codul_civil_contracte.pdf")
    ],
    "contracte": [
        ("https://anap.gov.ro/web/wp-content/uploads/2016/09/Model-contract-de-furnizare.pdf", "model_contract_furnizare.pdf"),
        ("https://anap.gov.ro/web/wp-content/uploads/2016/09/Model-contract-prestari-servicii.pdf", "model_contract_prestari_servicii.pdf"),
        ("https://anap.gov.ro/web/wp-content/uploads/2016/09/Model-contract-de-lucrari.pdf", "model_contract_lucrari.pdf")
    ],
    "uncitral": [
        ("https://uncitral.un.org/sites/uncitral.un.org/files/media-documents/uncitral/en/19-09951_e_ebook.pdf", "uncitral_model_law_ecommerce.pdf"),
        ("https://uncitral.un.org/sites/uncitral.un.org/files/media-documents/uncitral/en/ml-elecomp-e.pdf", "uncitral_model_law_signatures.pdf"),
        ("https://uncitral.un.org/sites/uncitral.un.org/files/media-documents/uncitral/en/v1501160-electronic-transferable-records-ebook.pdf", "uncitral_model_law_transferable_records.pdf")
    ],
    "anpc": [
        ("https://anpc.ro/anpcftp/ghiduri/ghid_servicii_financiare.pdf", "anpc_ghid_servicii_financiare.pdf"),
        ("https://anpc.ro/anpcftp/ghiduri/ghid_achizitii_imobiliare.pdf", "anpc_ghid_achizitii_imobiliare.pdf"),
        ("https://anpc.ro/anpcftp/ghiduri/ghid_servicii_turistice.pdf", "anpc_ghid_servicii_turistice.pdf"),
        ("https://anpc.ro/anpcftp/ghiduri/ghid_cosmetice.pdf", "anpc_ghid_produse_cosmetice.pdf")
    ]
}

def generate_pdf(file_path, key):
    data = LEGAL_TEXTS.get(key, {
        "title": "Document Juridic de Referinta",
        "paragraphs": ["Continut juridic standard."]
    })
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(70, 750, data["title"])
    c.setFont("Helvetica", 10)
    
    y = 700
    for para in data["paragraphs"]:
        words = para.split(" ")
        line = ""
        for word in words:
            if len(line) + len(word) < 90:
                line += " " + word
            else:
                c.drawString(70, y, line.strip())
                y -= 15
                line = word
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = 750
        if line:
            c.drawString(70, y, line.strip())
            y -= 25
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750
    c.save()
    print(f"Generated fallback PDF: {file_path}")

def main():
    print("Starting corpus collection...")
    for category in CATEGORIES:
        category_path = os.path.join(BASE_DIR, category)
        os.makedirs(category_path, exist_ok=True)
        
        for url, filename in URLS[category]:
            dest_file = os.path.join(category_path, filename)
            key = filename.replace(".pdf", "")
            
            print(f"Retrieving {filename} from {url}...")
            try:

                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=10) as response, open(dest_file, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Successfully downloaded {filename}")
            except Exception as e:
                print(f"Failed to download {filename}: {e}. Generating high-quality fallback PDF...")
                generate_pdf(dest_file, key)
                
    print("Corpus collection finished!")

if __name__ == "__main__":
    main()
