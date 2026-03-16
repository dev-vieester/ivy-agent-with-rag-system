from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from pathlib import Path


def process_documents(pdf_directory, doc_directory, csv_directory):
    """Process all files in the given directories"""
    all_documents = []
    pdf_dir = Path(pdf_directory)
    doc_dir = Path(doc_directory)
    csv_dir = Path(csv_directory)

    for directory in [pdf_dir, doc_dir, csv_dir]:
        if not directory.exists():
            print(f"Warning: directory not found — {directory}")

    all_files = (list(pdf_dir.glob('**/*.pdf')) + list(doc_dir.glob('**/*.txt')) + list(csv_dir.glob('**/*.csv')))

    print(f"Found {len(all_files)} files to process")

    suffix_to_type = {".pdf": "pdf", ".txt": "txt", ".csv": "csv"}

    for file in all_files:
        print(f'\nProcessing: {file.name}')
        try:
            file_type = suffix_to_type.get(file.suffix)
            if file.suffix == ".pdf":
                loader = PyPDFLoader(str(file))
            elif file.suffix == ".txt":
                loader = TextLoader(str(file))
            elif file.suffix == ".csv":
                loader = CSVLoader(str(file))
            else:
                print(f"  Skipping unsupported file type: {file.suffix}")
                continue

            documents = loader.load()

            for doc in documents:
                doc.metadata['source_file'] = file.name
                doc.metadata['file_type'] = file_type

            all_documents.extend(documents)
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\nTotal documents loaded: {len(all_documents)}")
    return all_documents


process_documents("../data/pdf_file", "../data/text_files", "../data/csv_files")






