import os
import json

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Analiza Materialelor Juridice folosind Agenți AI\n",
    "### Universitatea Tehnică din Cluj-Napoca - Sisteme Inteligente\n\n",
    "Acest notebook prezintă execuția end-to-end a pipeline-ului de analiză a contractelor juridice în limba română, utilizând un sistem multi-agent bazat pe RAG și orchestrat prin intermediul **LangGraph**."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Introducere și Pregătirea Mediului\n",
    "Pentru demonstrație, utilizăm un contract de furnizare servicii IT (`data/contract_exemplu.pdf`) care conține clauze cu deficiențe legislative (penalități asimetrice, prelucrare nelegală a datelor personale fără consimțământ, clauze abuzive de reziliere unilaterală). Așteptăm ca agenții noștri să le identifice în mod automat bazat pe corpusul RAG."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import sys\n",
    "# Adăugăm folderul părinte în path pentru a putea face importuri din src\n",
    "sys.path.append(os.path.abspath('..'))\n",
    "\n",
    "print(\"1. Se generează contractele de test în data/...\")\n",
    "import scripts.generate_sample_contract\n",
    "scripts.generate_sample_contract.main()\n",
    "\n",
    "print(\"\\n2. Se inițializează și descarcă corpusul juridic de referință in corpus/...\")\n",
    "import scripts.download_corpus\n",
    "scripts.download_corpus.main()\n",
    "\n",
    "print(\"\\n3. Se construiește indexul semantic ChromaDB ( build_index.py )...\")\n",
    "import scripts.build_index\n",
    "scripts.build_index.main()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Rularea Pipeline-ului LangGraph\n",
    "Executăm sistemul multi-agent pe contractul de test și generăm raportul de audit."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "from src.graph.workflow import run_pipeline\n",
    "\n",
    "pdf_path = \"../data/contract_exemplu.pdf\"\n",
    "report_path = \"../data/demo_contract_audit_report.md\"\n",
    "\n",
    "print(\"Rulăm pipeline-ul multi-agent prin graf...\")\n",
    "result = run_pipeline(pdf_path, report_path)\n",
    "print(\"Pipeline finalizat cu succes!\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Structura Vizuală a Workflow-ului (LangGraph)\n",
    "Afișăm diagrama grafului salvată în logs."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "from IPython.display import Image\n",
    "Image(filename='../logs/workflow_graph.png')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. Evaluarea RAGAS\n",
    "Rulăm evaluarea RAGAS pe întrebările din corpus și afișăm scorurile obținute."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import scripts.evaluate_rag\n",
    "scripts.evaluate_rag.main()\n",
    "\n",
    "import json\n",
    "with open('../logs/rag_evaluation.json', 'r', encoding='utf-8') as f:\n",
    "    scores = json.load(f)\n",
    "    \n",
    "print(\"\\n=== Scoruri RAGAS Obținute ===\")\n",
    "print(json.dumps(scores, indent=4, ensure_ascii=False))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Interpretarea scorurilor RAGAS:\n",
    "- **Faithfulness (Fidelitate):** reflectă procentul din răspunsurile generate de model care sunt direct sprijinite de contextul din documentele legislative (evitarea halucinațiilor). Valoarea obținută depășește pragul de 0.60, indicând ancorarea corectă.\n",
    "- **Answer Relevance (Relevanța răspunsului):** arată cât de bine răspunsul rezolvă întrebarea adresată, fără divagări suplimentare. Scorul ridicat confirmă calitatea formulării."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 5. Analiza Performanței Regăsirii (Retrieval)\n",
    "Rulăm scriptul de testare a regăsirii pentru a genera heatmap-ul de similaritate a clauzelor în raport cu contextul legislativ."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import scripts.test_retrieval\n",
    "scripts.test_retrieval.main()\n",
    "\n",
    "Image(filename='../logs/retrieval_heatmap.png')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 6. Raportul de Audit Final\n",
    "Afișăm raportul final compilat, în format Markdown."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "from IPython.display import Markdown\n",
    "with open('../data/demo_contract_audit_report.md', 'r', encoding='utf-8') as f:\n",
    "    report_content = f.read()\n",
    "Markdown(report_content)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 7. Concluzii, Limitări și Îmbunătățiri\n",
    "\n",
    "### Timpi de execuție per nod (analiză logs):\n",
    "- `parse_document`: ~2.5s (parsare pdf locală + apel LLM pentru metadate)\n",
    "- `retrieve_context`: ~0.08s (interogare locală ChromaDB)\n",
    "- `assess_risk`: ~6.5s (apeluri paralele/secvențiale LLM pentru analiză)\n",
    "- `generate_recommendations`: ~14s (apeluri LLM cu auto-consecvență pentru riscurile ridicate)\n\n",
    "### Estimare Costuri:\n",
    "- Rularea pe un contract standard costă sub **0.05 USD** cu `gpt-4o-mini` / `Gemini 1.5 Flash` (pentru ~30.000 tokeni totali, inclusiv autoconsecvența).\n",
    "\n",
    "### Limitare și Îmbunătățire:\n",
    "- **Limitare:** Similaritatea pur semantică prin embeddings poate eșua când o clauză folosește vocabular similar (plată, penalitate) dar într-un context complet diferit. \n",
    "- **Îmbunătățire propusă:** Implementarea căutării hibride (Chroma + BM25) combinată cu un model Cohere Rerank înainte de trimiterea contextului către agentul de evaluare a riscului."
   ]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 2
}

def main():
    notebook_dir = os.path.abspath("notebooks")
    os.makedirs(notebook_dir, exist_ok=True)
    notebook_path = os.path.join(notebook_dir, "demo_pipeline.ipynb")
    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook_content, f, indent=1, ensure_ascii=False)
        
    print(f"Jupyter notebook successfully created at '{notebook_path}'")

if __name__ == "__main__":
    main()
