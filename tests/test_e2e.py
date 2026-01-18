"""
End-to-End Tests mit Playwright für Streamlit.

Setup:
    pip install playwright pytest-playwright
    playwright install chromium

Run:
    pytest tests/test_e2e.py -v --headed  # Mit Browser-Fenster
    pytest tests/test_e2e.py -v           # Headless
"""
import pytest
import subprocess
import time
import os
from pathlib import Path


@pytest.fixture(scope="module")
def streamlit_app():
    """Startet die Streamlit-App als Hintergrundprozess."""
    app_path = Path(__file__).parent.parent / "app.py"
    
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = "8599"
    
    process = subprocess.Popen(
        ["streamlit", "run", str(app_path), "--server.port=8599"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(5)
    
    yield "http://localhost:8599"
    
    process.terminate()
    process.wait()


@pytest.fixture
def pdf_path():
    return Path(__file__).parent / "example_offer.pdf"


def navigate_to_new_request(page, streamlit_app):
    """Navigiert zur New Request Seite."""
    page.goto(streamlit_app)
    page.wait_for_load_state("networkidle")
    page.locator("text=New Request").click()
    page.wait_for_timeout(1000)


def fill_form_manually(page, data: dict):
    """Füllt das Formular manuell aus."""
    page.locator('input[aria-label="Requestor Name *"]').fill(data["requestor_name"])
    page.locator('input[aria-label="Title / Short Description *"]').fill(data["title"])
    page.locator('input[aria-label="Vendor Name *"]').fill(data["vendor_name"])
    page.locator('input[aria-label="VAT ID (USt-IdNr.) *"]').fill(data["vat_id"])
    page.locator('input[aria-label="Department *"]').fill(data["department"])
    
    for i, line in enumerate(data.get("order_lines", [])):
        if i > 0:
            page.locator('button:has-text("Add Line")').click()
            page.wait_for_timeout(500)
        
        desc_inputs = page.locator('input[aria-label="Description"]')
        desc_inputs.nth(i).fill(line["description"])
        
        price_inputs = page.locator('input[aria-label*="Unit Price"]')
        price_inputs.nth(i).fill(str(line["unit_price"]))
        
        qty_inputs = page.locator('input[aria-label="Qty"]')
        qty_inputs.nth(i).fill(str(line["quantity"]))


def upload_pdf_and_extract(page, pdf_path: Path):
    """Lädt PDF hoch und extrahiert Daten."""
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(str(pdf_path))
    page.wait_for_timeout(1000)
    
    extract_button = page.locator('button:has-text("Extract Data")')
    extract_button.click()
    
    vendor_input = page.locator('input[aria-label="Vendor Name *"]')
    for _ in range(30):
        page.wait_for_timeout(1000)
        if vendor_input.input_value() != "":
            break
    
    page.wait_for_timeout(1000)


def auto_classify_and_submit(page):
    """Klassifiziert automatisch und submittet."""
    auto_classify = page.locator('button:has-text("Auto-classify")')
    auto_classify.click()
    page.wait_for_timeout(5000)
    
    submit_button = page.locator('button:has-text("Submit Request")')
    submit_button.click()
    page.wait_for_timeout(2000)
    
    success_message = page.locator("text=submitted successfully")
    assert success_message.is_visible(), "Request submission failed"


def verify_request_in_overview(page, search_text: str):
    """Prüft ob Request in Overview erscheint."""
    page.locator("text=Request Overview").click()
    page.wait_for_timeout(1000)
    
    search_input = page.locator('input[aria-label="Search (vendor/title)"]')
    search_input.fill(search_text)
    page.wait_for_timeout(500)
    
    matching_elements = page.locator(f"text={search_text}")
    assert matching_elements.count() >= 1, f"Request with '{search_text}' not found in overview"


def verify_request_details_in_overview(page, expected: dict):
    """Prüft Details des Requests in Overview."""
    page.locator("text=Request Overview").click()
    page.wait_for_timeout(1000)
    
    expanders = page.locator('[data-testid="stExpander"]')
    expanders.first.click()
    page.wait_for_timeout(500)
    
    page_content = page.content()
    
    for key, value in expected.items():
        assert value in page_content, f"Expected '{value}' not found in request details"


@pytest.mark.e2e
class TestManualEntry:
    """Test 1: Manuell alle Felder eingeben ohne PDF."""
    
    def test_manual_entry_complete_workflow(self, streamlit_app, page):
        test_data = {
            "requestor_name": "Max Mustermann",
            "title": "Büromaterial Bestellung",
            "vendor_name": "Office Supplies GmbH",
            "vat_id": "DE111222333",
            "department": "Verwaltung",
            "order_lines": [
                {"description": "Kugelschreiber", "unit_price": 2.50, "quantity": 100},
                {"description": "Notizblöcke", "unit_price": 5.00, "quantity": 50}
            ]
        }
        
        navigate_to_new_request(page, streamlit_app)
        
        fill_form_manually(page, test_data)
        
        auto_classify_and_submit(page)
        
        verify_request_in_overview(page, "Büromaterial Bestellung")
        
        verify_request_details_in_overview(page, {
            "requestor": "Max Mustermann",
            "vendor": "Office Supplies GmbH",
            "vat": "DE111222333",
            "department": "Verwaltung"
        })


@pytest.mark.e2e
class TestPdfAutoExtraction:
    """Test 2: PDF hochladen, alles automatisch, ohne manuelle Eingaben."""
    
    def test_pdf_extraction_automatic_workflow(self, streamlit_app, page, pdf_path):
        if not pdf_path.exists():
            pytest.skip("example_offer.pdf not found")
        
        navigate_to_new_request(page, streamlit_app)
        
        upload_pdf_and_extract(page, pdf_path)
        
        page.wait_for_timeout(1000)
        
        vendor_input = page.locator('input[aria-label="Vendor Name *"]')
        vendor_value = vendor_input.input_value()
        assert vendor_value != "", f"Vendor not extracted: field is empty"
        assert "Nimbus" in vendor_value or "nimbus" in vendor_value.lower(), \
            f"Vendor not extracted correctly: {vendor_value}"
        
        vat_input = page.locator('input[aria-label="VAT ID (USt-IdNr.) *"]')
        vat_value = vat_input.input_value()
        assert vat_value == "DE289456123", f"VAT ID not extracted correctly: {vat_value}"
        
        requestor_input = page.locator('input[aria-label="Requestor Name *"]')
        if requestor_input.input_value() == "":
            requestor_input.fill("Auto Extracted User")
        
        auto_classify_and_submit(page)
        
        verify_request_in_overview(page, "Nimbus")
        
        page.locator('[data-testid="stExpander"]').first.click()
        page.wait_for_timeout(500)
        
        page_content = page.content()
        assert "Cloud Storage" in page_content or "cloud" in page_content.lower(), \
            "Order lines not correctly extracted"


@pytest.mark.e2e
class TestPdfWithManualAdjustments:
    """Test 3: PDF hochladen, dann einige Felder manuell anpassen."""
    
    def test_pdf_extraction_with_adjustments(self, streamlit_app, page, pdf_path):
        if not pdf_path.exists():
            pytest.skip("example_offer.pdf not found")
        
        navigate_to_new_request(page, streamlit_app)
        
        upload_pdf_and_extract(page, pdf_path)
        
        page.wait_for_timeout(1000)
        
        adjusted_title = "Angepasste IT Services Bestellung"
        title_input = page.locator('input[aria-label="Title / Short Description *"]')
        title_input.fill(adjusted_title)
        
        adjusted_department = "Finanzen"
        dept_input = page.locator('input[aria-label="Department *"]')
        dept_input.fill(adjusted_department)
        
        adjusted_requestor = "Klaus Schmidt"
        requestor_input = page.locator('input[aria-label="Requestor Name *"]')
        requestor_input.fill(adjusted_requestor)
        
        price_inputs = page.locator('input[aria-label*="Unit Price"]')
        if price_inputs.count() > 0:
            price_inputs.first.fill("150")
        
        auto_classify_and_submit(page)
        
        verify_request_in_overview(page, "Angepasste IT Services")
        
        page.locator('[data-testid="stExpander"]').first.click()
        page.wait_for_timeout(500)
        
        page_content = page.content()
        
        assert "Klaus Schmidt" in page_content, "Adjusted requestor not saved"
        assert "Finanzen" in page_content, "Adjusted department not saved"
        assert "Nimbus" in page_content, "Original vendor should be preserved"
        assert "DE289456123" in page_content, "Original VAT ID should be preserved"
