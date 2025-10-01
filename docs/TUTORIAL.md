# Hello CORTX Tutorial

This tutorial will guide you through an end-to-end demonstration of the CORTX platform.

## Prerequisites

- Docker and docker-compose are installed.
- You have cloned the `cortx-platform` repository.

## 1. Spin up the dev stack

From the root of the `cortx-platform` repository, run:

```bash
docker-compose up -d
```

This will start all the CORTX platform services.

## 2. Upload a document

We will use the OCR service to extract text from a scanned document.

```bash
curl -X POST -F 'file=@/path/to/your/document.pdf' http://localhost:8137/api/ocr/extract
```

This will return a job ID. You can use this job ID to check the status of the OCR job and retrieve the extracted text.

## 3. Ingest to RAG

Once the text has been extracted, you can ingest it into the RAG service.

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "doc_id": "my-document",
  "content": "<the extracted text>",
  "scope": "entity",
  "entity_id": "my-entity"
}' http://localhost:8138/api/rag/index
```

## 4. Query hierarchical context

Now you can query the RAG service to retrieve contextual information.

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "query": "What is the main topic of my document?",
  "scope": "entity",
  "entity_id": "my-entity"
}' http://localhost:8138/api/rag/query
```

## 5. Execute a WorkflowPack

Now we will execute a WorkflowPack that uses the information from the document.

```bash
curl -X POST -H "Content-Tye: application/json" -d '{
  "workflow_id": "example-workflow",
  "input_data": {
    "doc_id": "my-document"
  }
}' http://localhost:8130/api/workflows/execute
```

## 6. Export ledger evidence

Finally, you can export the ledger evidence for the workflow execution.

```bash
curl http://localhost:8136/api/ledger/events?since=YYYY-MM-DD
```

This will return a list of all the events that have been recorded in the ledger since the specified date.
