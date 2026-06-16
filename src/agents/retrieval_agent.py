import os
from dotenv import load_dotenv

from src.dtos import ClauseDTO, RetrievalResultDTO
from src.utils import get_embeddings
from langchain_community.vectorstores import Chroma

load_dotenv()


class RAGRetrievalAgent:
    def __init__(self, persist_directory: str = "vectorstore"):
        self.persist_directory = persist_directory
        self.vectorstore = None
        self._initialize_vectorstore()

    def _initialize_vectorstore(self):
        """Loads the existing Chroma vectorstore from disk."""
        if not os.path.exists(self.persist_directory):
            print(
                f"Warning: Persist directory '{self.persist_directory}' does not exist yet. "
                "Retrieval agent initialized, but queries will return empty until the index is built."
            )
            return

        try:
            embeddings = get_embeddings()
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=embeddings
            )
            print(f"RAGRetrievalAgent loaded index from '{self.persist_directory}' successfully.")
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
            self.vectorstore = None

    def _distance_to_similarity(self, distance: float) -> float:
        """
        Chroma poate returna distanta, nu similaritate.
        Pentru distanta: valori mai mici = rezultate mai bune.
        Transformam distanta intr-un scor intre 0 si 1:
            distance = 0   -> similarity = 1
            distance mare  -> similarity se apropie de 0
        """
        try:
            distance = float(distance)
        except Exception:
            return 0.0

        if distance < 0:
            distance = 0.0

        similarity = 1.0 / (1.0 + distance)
        return max(0.0, min(1.0, similarity))

    def retrieve(self, clause: ClauseDTO, k: int = 5, threshold: float = 0.3) -> list[RetrievalResultDTO]:
        """
        Retrieves top-k relevant legal document chunks for a given clause.
        Chroma returns a distance score, so we convert it to similarity.
        """
        if self.vectorstore is None:
            self._initialize_vectorstore()
            if self.vectorstore is None:
                print("Vectorstore is not initialized. Returning empty context.")
                return []

        if not clause.text or not clause.text.strip():
            print(f"Clause {clause.id} has empty text. Returning empty context.")
            return []

        try:
            results = self.vectorstore.similarity_search_with_score(clause.text, k=k)
        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []

        retrieved_results = []

        for doc, distance in results:
            similarity = self._distance_to_similarity(distance)

            if similarity >= threshold:
                source = doc.metadata.get("source", "unknown_source")
                page = doc.metadata.get("page")

                source_str = f"{source} (pag. {page})" if page else source

                retrieved_results.append(
                    RetrievalResultDTO(
                        text=doc.page_content,
                        source=source_str,
                        score=float(similarity)
                    )
                )

        retrieved_results.sort(key=lambda x: x.score, reverse=True)

        if not retrieved_results:
            print(
                f"No chunks passed threshold={threshold} for clause {clause.id}. "
                "Try lowering threshold or checking vectorstore."
            )

        return retrieved_results