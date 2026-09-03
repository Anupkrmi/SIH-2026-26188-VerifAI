# VerifAI

### AI-Assisted Identity & Document Screening System

**Smart India Hackathon 2026**  
**Problem Statement: 26188**

VerifAI is an AI-assisted identity and document screening platform designed to support faster, more structured, and explainable document verification.

The system combines document analysis, text extraction, document consistency checks, forgery detection, biometric verification, evidence analysis, and risk assessment into a single screening workflow.

> **VerifAI assists authorized personnel in identifying suspicious documents and presenting the evidence behind a screening decision. It does not autonomously declare a person fraudulent.**

---

## Project Team

### Authors

- Anup Kumar Mishra
- Ishaan
- Harshwardhan
- Divya
- Prathamesh
- Varad

---

## Key Capabilities

### 1. OCR Extraction

Extracts readable information from uploaded identity and document images.

### 2. Document Validation

Checks extracted information for consistency and validates structured document information where applicable.

### 3. Tampering Detection

Analyzes documents for visual and forensic indicators associated with editing, alteration, or recapture.

### 4. Face Verification

Compares a document portrait with a presented face image when a suitable portrait is available.

### 5. Risk Assessment

Combines available evidence into a structured screening result such as:

- Low Risk
- Review Required
- High Risk
- Critical

The system distinguishes between strong evidence, advisory evidence, and insufficient evidence.

### 6. Evidence & Findings

The system presents the factors contributing to a screening result so that an authorized reviewer can understand **why** a document was flagged.

### 7. Screening History

Stores screening-session information required for reviewing previous cases within the application.

---

## System Philosophy

VerifAI follows a **human-in-the-loop** approach.

The system is designed around three questions:

    OBSERVE
       ↓
    What information can be extracted?

    VERIFY
       ↓
    What can be checked or validated?

    ASSESS
       ↓
    What does the available evidence indicate?

An uncertain result is not automatically treated as fraud.

A low-confidence signal is not treated as conclusive evidence.

The purpose of the system is to support investigation and verification, not replace authorized decision-makers.

---

## Application Modules

    VerifAI
    │
    ├── Document Screening
    │   ├── Document Upload
    │   ├── Text Extraction
    │   ├── Field Extraction
    │   ├── Validation
    │   └── Risk Assessment
    │
    ├── Case Analysis
    │   ├── Document
    │   ├── Evidence
    │   └── Decision
    │
    ├── Security Test Lab
    │   └── Controlled document attack scenarios
    │
    ├── Screening History
    │   └── Previous screening records
    │
    └── Settings

---

## Current Prototype

The current prototype contains a controlled synthetic-document workflow as well as a separate real-document screening workflow.

### Controlled Document Mode

The controlled workflow uses a synthetic demonstration document to test the complete screening pipeline.

It supports scenarios such as:

- Genuine document
- Modified date of birth
- Modified portrait
- Screen recapture
- Signature manipulation
- Biometric mismatch testing

Each scenario is designed to exercise a different part of the screening pipeline.

### Real Document Mode

The real-document workflow accepts uploaded documents at their native resolution.

Depending on the document and image quality, VerifAI can attempt:

- Text extraction
- Document-type classification
- Field extraction
- MRZ detection
- Portrait detection
- Face comparison
- Forensic analysis
- Risk assessment

Capabilities are reported explicitly. A check that cannot be reliably performed is not represented as a successful verification.

---

## Risk Assessment

VerifAI uses evidence from multiple layers rather than relying on a single model.

Conceptually:

    Cryptographic / Deterministic Evidence
                    ↓
            Strong Verification
                    ↓
          Forensic / Biometric Signals
                    ↓
              Risk Assessment
                    ↓
          Reviewer Action Required

Different evidence types have different levels of confidence.

This prevents an individual weak signal from automatically producing the strongest possible fraud verdict.

---

## Explainability

Every important screening result should answer:

> **Why was this document flagged?**

The interface presents the relevant findings and the evidence contributing to the result.

Examples include:

- inconsistent document information
- MRZ validation failure
- suspected visual modification
- suspicious recapture characteristics
- biometric mismatch
- insufficient evidence for a reliable conclusion

---

## Project Structure

    VerifAI/
    │
    ├── app.py
    ├── config.py
    ├── requirements.txt
    │
    ├── core/
    │   ├── document processing
    │   ├── MRZ processing
    │   ├── validation
    │   ├── forensics
    │   ├── face verification
    │   ├── risk assessment
    │   └── supporting utilities
    │
    ├── core/realdoc/
    │   └── real-document processing
    │
    ├── synth/
    │   └── synthetic document generation
    │
    ├── ui/
    │   └── application interface
    │
    ├── tests/
    │   └── automated tests
    │
    ├── data/
    │   ├── documents/
    │   ├── forged/
    │   └── portraits/
    │
    ├── models/
    │   └── model and template files
    │
    └── docs/
        └── project documentation

---

## Installation

### 1. Clone the repository

    git clone https://github.com/Anupkrmi/SIH-2026-26188-VerifAI.git
    cd SIH-2026-26188-VerifAI

### 2. Create the virtual environment

    python -m venv venv

### 3. Activate the environment

    .\venv\Scripts\Activate.ps1

### 4. Install dependencies

    pip install -r requirements.txt

### 5. Run the application

    python -m streamlit run app.py

The application will open locally in the browser.

---

## Running Tests

Run the complete automated test suite:

    python -m pytest tests/ -q

The current prototype contains **108 automated tests** covering the major screening components.

---

## Important Limitations

VerifAI is a research and hackathon prototype.

The current implementation should not be interpreted as a production-grade identity verification authority.

Important limitations include:

- Screening performance depends heavily on image quality.
- Some document types may provide insufficient information for every verification layer.
- OCR and field extraction are not equally reliable for every document format.
- Biometric verification depends on the quality and visibility of the available portrait.
- Some forensic checks are advisory rather than conclusive.
- Real-document screening may return `REVIEW` or insufficient-evidence results when reliable verification is not possible.
- Synthetic demonstration documents are used for controlled attack testing.

These limitations are reported explicitly instead of being hidden behind an apparently confident score.

---

## Privacy

Real identity documents and personal photographs should not be committed to the repository.

Test data containing personal information should remain local and should be handled only with appropriate consent and authorization.

---

## Development Principles

    1. Evidence before conclusions
    2. Explainable screening
    3. Human review for uncertain cases
    4. No unsupported claims

---

## Project Status

**Current Status: Working Prototype**

The prototype currently includes:

- Document screening
- Document validation
- Tampering detection
- Biometric verification
- Evidence analysis
- Risk assessment
- Controlled security testing
- Screening history
- Automated testing

Further development will focus on improving robustness, accuracy, document coverage, explainability, and real-world evaluation.

---

## Authors

### VerifAI Development Team

- Anup Kumar Mishra
- Ishaan
- Harshwardhan
- Divya
- Prathamesh
- Varad

---

**Project:** VerifAI  
**SIH 2026 Problem Statement:** 26188
