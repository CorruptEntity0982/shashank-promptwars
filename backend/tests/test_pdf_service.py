from io import BytesIO

from pypdf import PdfWriter

from app.services.pdf_service import get_pdf_page_count, validate_pdf


def make_pdf_bytes(page_count: int) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)

    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_validate_pdf_accepts_small_valid_pdf() -> None:
    content = make_pdf_bytes(page_count=2)
    is_valid, pages, error = validate_pdf(content, max_pages=40)

    assert is_valid is True
    assert pages == 2
    assert error is None


def test_validate_pdf_rejects_when_page_limit_exceeded() -> None:
    content = make_pdf_bytes(page_count=3)
    is_valid, pages, error = validate_pdf(content, max_pages=2)

    assert is_valid is False
    assert pages == 3
    assert error is not None
    assert "maximum allowed pages" in error


def test_validate_pdf_rejects_invalid_content() -> None:
    is_valid, pages, error = validate_pdf(b"not-a-real-pdf", max_pages=40)

    assert is_valid is False
    assert pages is None
    assert error is not None


def test_get_pdf_page_count_returns_none_for_invalid_pdf() -> None:
    assert get_pdf_page_count(b"not-a-real-pdf") is None
