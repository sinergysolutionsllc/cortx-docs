# OCR Service Architecture

**Version**: 1.0
**Status**: Implemented

This document outlines the architecture of the OCR Service (`svc-ocr`).

## Purpose

The OCR Service provides a centralized capability for extracting text and structured data from documents, such as PDFs and images. It is used by other services, like the RAG service, to make documents searchable.

## Architecture

The service is designed as a multi-engine platform to provide flexibility in terms of cost, performance, and accuracy.

### Key Features

- **Multi-Engine Support**:
  - **Tesseract**: A powerful, open-source OCR engine that runs locally. It is the default for most documents.
  - **Google Document AI**: An optional, high-accuracy engine available via the AI Broker for complex documents.
- **Normalized Output**: The service produces a standardized JSON output (`DocumentExtraction` schema) regardless of the engine used.
- **Async Processing**: For large documents, OCR can be run as a background job.

### High-Level Flow

1. A client submits a document (e.g., PDF) to the `/extract` endpoint.
2. The service determines the best engine to use (`tesseract` or `google_doc_ai`) based on the request options.
3. The document is processed, and the extracted text and metadata are returned.
4. For large jobs, a `job_id` is returned, and the client can poll the `/results/{job_id}` endpoint.

## API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/extract` | POST | Extracts text from a document. |
| `/results/{job_id}` | GET | Retrieves the results of an asynchronous OCR job. |
| `/healthz` | GET | Kubernetes liveness and readiness probe. |
