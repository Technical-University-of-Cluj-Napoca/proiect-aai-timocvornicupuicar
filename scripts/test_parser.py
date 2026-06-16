import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.parser_agent import DocumentParserAgent

load_dotenv()

def main():
    print("Starting Parser Agent Test...")
    
    pdf_path = os.path.join("data", "contract_exemplu.pdf")
    

    if not os.path.exists(pdf_path):
        print(f"Sample contract '{pdf_path}' not found. Generating it now...")
        import scripts.generate_sample_contract
        scripts.generate_sample_contract.main()
        
    parser = DocumentParserAgent()
    try:
        parsed_doc = parser.parse(pdf_path)

        meta = parsed_doc.metadata
        print("\n=== Extracted Metadata ===")
        print(f"Title: {meta.title}")
        print(f"Page Count: {meta.page_count}")
        print(f"Value: {meta.value}")
        print(f"Duration: {meta.duration}")
        print(f"Signing Date: {meta.signing_date}")
        print(f"Effective Date: {meta.effective_date}")
        print(f"Parties identified:")
        for party in meta.parties:
            print(f"  - {party.name} (CUI/CNP: {party.cui_cnp}, Adresa: {party.address})")

        print(f"\n=== Document Structure ===")
        print(f"Number of Sections: {len(parsed_doc.sections)}")
        print(f"Number of Clauses: {len(parsed_doc.clauses)}")

        print("\n=== First 3 Clauses ===")
        for i, clause in enumerate(parsed_doc.clauses[:3]):
            print(f"\nClause {i+1} (ID: {clause.id}, Page: {clause.page}):")
            print(f"Section: {clause.section}")
            print(f"Type: {clause.type.value}")
            print("Text:")
            print("-" * 50)
            print(clause.text)
            print("-" * 50)

        output_json = os.path.join("data", "contract_exemplu_parsed.json")
        with open(output_json, 'w', encoding='utf-8') as f:
            f.write(parsed_doc.model_dump_json(indent=4))
        print(f"\nSaved parsed DTO to {output_json}")
        
    except Exception as e:
        print(f"Parser agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
