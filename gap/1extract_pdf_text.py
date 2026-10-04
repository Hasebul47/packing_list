"""
Extracts raw text from a PO PDF using pdfplumber, page by page.

Install requirement:
    pip install pdfplumber

Usage:
    python extract_pdf_text.py your_po.pdf
"""
import sys
import pdfplumber


def extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages_text.append(f"===== PAGE {i} =====\n{text}\n")
        return "\n".join(pages_text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_text.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    full_text = extract_text(pdf_path)

    # Print to console
    print(full_text)

    # Also save to a .txt file next to the PDF
    out_path = pdf_path.rsplit(".", 1)[0] + "_raw_text.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"\nSaved to: {out_path}")