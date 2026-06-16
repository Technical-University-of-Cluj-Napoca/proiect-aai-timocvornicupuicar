import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.parser_agent import ClauseType
from src.dtos import ClauseDTO
from src.agents.retrieval_agent import RAGRetrievalAgent

load_dotenv()

TEST_CLAUSES = [
    ClauseDTO(
        id="test_penalități",
        section="Articolul 4. Penalitati",
        text="In caz de intarziere in livrarea bunurilor, Prestatorul datoreaza Beneficiarului o penalitate de 1% pe zi din valoarea contractului.",
        page=1,
        type=ClauseType.PENALITATE
    ),
    ClauseDTO(
        id="test_date_personale",
        section="Articolul 5. Prelucrarea datelor",
        text="Partile convin ca orice date cu caracter personal colectate sa fie prelucrate in scopuri de marketing direct si transmise catre parteneri terti din afara UE fara consimtamant.",
        page=1,
        type=ClauseType.DATE_PERSONALE
    ),
    ClauseDTO(
        id="test_forta_majora",
        section="Articolul 6. Forta majora",
        text="Forta majora inlatura raspunderea partilor. Prin forta majora se intelege orice imprejurare greu de evitat sau controlat de catre partile contractante.",
        page=1,
        type=ClauseType.FORTA_MAJORA
    ),
    ClauseDTO(
        id="test_reziliere",
        section="Articolul 7. Reziliere unilaterala",
        text="Beneficiarul poate rezilia unilateral contractul in orice moment, cu un preaviz scris de doar 24 de ore, fara a datora nicio despagubire.",
        page=1,
        type=ClauseType.REZILIERE
    ),
    ClauseDTO(
        id="test_confidențialitate",
        section="Articolul 10. Confidentialitate",
        text="Obligatia de confidentialitate se prelungeste pe o perioada de timp nedeterminata si nu inceteaza niciodata dupa terminarea contractului.",
        page=1,
        type=ClauseType.CONFIDENTIALITATE
    )
]

def main():
    print("Starting RAG Retrieval Agent Test...")
    
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    retriever = RAGRetrievalAgent()

    scores_matrix = []
    clause_labels = ["Penalități", "GDPR", "Forță Majoră", "Reziliere", "Confidențialitate"]
    

    print("\nRetrieving chunks for representative clauses...")
    for idx, clause in enumerate(TEST_CLAUSES):
        print(f"Retrieving context for {clause_labels[idx]}...")
        chunks = retriever.retrieve(clause, k=3, threshold=0.1)

        scores = [chunk.score for chunk in chunks]

        while len(scores) < 3:
            scores.append(0.0)
            
        scores_matrix.append(scores[:3])
        print(f"Top 3 scores: {scores[:3]}")
        
    scores_array = np.array(scores_matrix)

    plt.figure(figsize=(8, 6))
    im = plt.imshow(scores_array, cmap="YlOrRd", vmin=0.0, vmax=1.0)

    plt.xticks(np.arange(3), ["Chunk 1", "Chunk 2", "Chunk 3"])
    plt.yticks(np.arange(5), clause_labels)

    for i in range(5):
        for j in range(3):
            plt.text(j, i, f"{scores_array[i, j]:.2f}",
                     ha="center", va="center", color="black" if scores_array[i, j] < 0.6 else "white")
                     
    plt.colorbar(im, label="Scor de Similaritate normalizat")
    plt.title("RAG Retrieval Performance Heatmap (Top 3 Chunks)")
    plt.xlabel("Fragmente recuperate (Sorted desc)")
    plt.ylabel("Tip Clauză Contractuală")
    
    heatmap_path = os.path.join(logs_dir, "retrieval_heatmap.png")
    plt.tight_layout()
    plt.savefig(heatmap_path, dpi=150)
    plt.close()
    
    print(f"\nHeatmap successfully generated and saved to {heatmap_path}!")

if __name__ == "__main__":
    main()
