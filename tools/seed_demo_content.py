#!/usr/bin/env python3
"""
Seed demo content for RAG service

This script seeds minimal demo content to showcase hierarchical RAG capabilities.
The RAG service remains fully functional for real queries.

Usage:
    python tools/seed_demo_content.py
"""

import httpx
import asyncio
from pathlib import Path

RAG_SERVICE_URL = "http://localhost:8138"

DEMO_DOCUMENTS = [
    # Platform Level - General CORTX knowledge
    {
        "title": "CORTX Platform Overview",
        "level": "platform",
        "suite_id": None,
        "module_id": None,
        "content": """
CORTX Platform is a compliance-first, policy-driven automation platform for federal,
healthcare, and corporate sectors.

Key Capabilities:
- Hierarchical RAG (Platform → Suite → Module → Entity knowledge)
- AI Broker with provider policy and PII redaction
- Validation Service with safe RulePack execution
- Workflow Service with saga patterns
- Ledger Service for tamper-evident audit trails
- OCR Service for document extraction

All services are multi-tenant and follow NIST 800-53 controls.
"""
    },
    {
        "title": "ThinkTank AI Assistant Guide",
        "level": "platform",
        "suite_id": None,
        "module_id": None,
        "content": """
ThinkTank is the AI assistant integrated throughout the CORTX platform.

Features:
- Context-aware help based on current suite/module
- Floating action button (FAB) on every page
- Full-page assistant at /thinktank
- Automatic URL-based context detection
- Citation-backed answers from hierarchical RAG
- Document upload and knowledge base management

Access ThinkTank by clicking the assistant icon in the bottom-right corner of any page.
"""
    },

    # Suite Level - FedSuite
    {
        "title": "FedSuite Overview",
        "level": "suite",
        "suite_id": "fedsuite",
        "module_id": None,
        "content": """
FedSuite provides federal compliance and financial management tools designed specifically for government agencies.

Key Modules:
- FedReconcile: Automates GTAS trial balance reconciliation with Treasury ATB reports, ensuring accurate financial reporting for federal agencies
- FedTransform: Enables legacy data transformation to Oracle Cloud FBDI format, supporting financial system modernization

Compliance Framework:
All FedSuite modules follow OMB Circular A-136 requirements for federal financial reporting and support FedRAMP compliance standards. The suite integrates with agency financial systems and Treasury reporting systems to streamline compliance workflows.

Target Users:
Federal financial managers, accountants, and CFO offices responsible for financial reporting and compliance.
"""
    },

    # Module Level - FedReconcile
    {
        "title": "FedReconcile User Guide",
        "level": "module",
        "suite_id": "fedsuite",
        "module_id": "fedreconcile",
        "content": """
FedReconcile automates GTAS trial balance reconciliation.

Workflow:
1. Upload GTAS trial balance report
2. Upload Treasury ATB report
3. System performs automatic reconciliation
4. Review diagnostics and variances
5. Generate correcting entries
6. Export reconciliation report

Common Issues:
- Variance thresholds: Configure in Settings > Reconciliation
- Account mapping: Update mappings in Configuration > Account Map
- ATB format changes: System auto-detects format versions

For urgent support, contact your agency's CORTX administrator.
"""
    },
    {
        "title": "FedReconcile Diagnostic Rules",
        "level": "module",
        "suite_id": "fedsuite",
        "module_id": "fedreconcile",
        "content": """
FedReconcile uses intelligent diagnostic rules to identify reconciliation issues.

Rule Categories:
- Balance Checks: Verify debit/credit equality
- Account Validation: Check account codes against USSGL
- Variance Analysis: Flag differences exceeding thresholds
- Format Validation: Ensure ATB/GTAS format compliance

Rule Packs:
- Standard Federal: OMB A-136 compliant rules
- Agency Specific: Custom rules per agency policy
- Treasury ATB: Treasury-specific validation rules

To add custom rules, use the Validation Service RulePack API.
"""
    },

    # Module Level - FedTransform
    {
        "title": "FedTransform Overview",
        "level": "module",
        "suite_id": "fedsuite",
        "module_id": "fedtransform",
        "content": """
FedTransform converts legacy financial data to Oracle Cloud FBDI format.

Supported Sources:
- Legacy mainframe extracts (fixed-width, EBCDIC)
- Excel templates
- CSV exports
- Database dumps

Output Formats:
- Oracle Cloud FBDI (default)
- Universal journal entry format
- Reconciliation-ready format

AI Features:
- Auto-detect source format
- Intelligent field mapping
- Data quality suggestions
- Variance detection

FedTransform integrates with FedReconcile for end-to-end financial migration.
"""
    },
]


async def upload_document(doc: dict):
    """Upload a document to RAG service"""
    async with httpx.AsyncClient() as client:
        # Create a simple text file
        files = {
            "file": (f"{doc['title']}.txt", doc["content"].encode(), "text/plain")
        }

        data = {
            "title": doc["title"],
            "level": doc["level"],
            "access_level": "internal"
        }

        if doc["suite_id"]:
            data["suite_id"] = doc["suite_id"]
        if doc["module_id"]:
            data["module_id"] = doc["module_id"]

        try:
            response = await client.post(
                f"{RAG_SERVICE_URL}/documents/upload",
                files=files,
                data=data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Uploaded: {doc['title']} (level={doc['level']}, chunks={result.get('chunks_count', 0)})")
            return result
        except Exception as e:
            print(f"❌ Failed to upload {doc['title']}: {e}")
            return None


async def check_service():
    """Check if RAG service is running"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RAG_SERVICE_URL}/readyz", timeout=5.0)
            response.raise_for_status()
            status = response.json()
            print(f"✅ RAG Service is ready")
            print(f"   Database: {status.get('database', 'unknown')}")
            print(f"   Documents: {status.get('documents', 0)}")
            print(f"   Chunks: {status.get('chunks', 0)}")
            print(f"   Model: {status.get('embedding_model', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ RAG Service not available: {e}")
            print(f"   Make sure the service is running on {RAG_SERVICE_URL}")
            return False


async def main():
    print("=" * 60)
    print("CORTX RAG Service - Demo Content Seeder")
    print("=" * 60)
    print()

    # Check service
    if not await check_service():
        print("\nPlease start the RAG service first:")
        print("  cd /Users/michael/Development/sinergysolutionsllc")
        print("  PYTHONPATH=packages/cortx_backend:services/rag \\")
        print("  PORT=8138 \\")
        print("  POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx \\")
        print("  /opt/homebrew/bin/python3.11 -m uvicorn services.rag.app.main:app --host 0.0.0.0 --port 8138 --reload")
        return

    print()
    print("Uploading demo documents...")
    print("-" * 60)

    # Upload documents
    results = []
    for doc in DEMO_DOCUMENTS:
        result = await upload_document(doc)
        if result:
            results.append(result)
        await asyncio.sleep(0.5)  # Small delay between uploads

    print()
    print("=" * 60)
    print(f"✅ Seeding complete: {len(results)}/{len(DEMO_DOCUMENTS)} documents uploaded")
    print("=" * 60)
    print()
    print("Demo Queries to Try:")
    print("-" * 60)
    print("1. Platform Level:")
    print("   'What is CORTX Platform?'")
    print("   'How do I use ThinkTank?'")
    print()
    print("2. Suite Level (FedSuite):")
    print("   'What modules are in FedSuite?'")
    print("   'What compliance standards does FedSuite follow?'")
    print()
    print("3. Module Level (FedReconcile):")
    print("   'How do I reconcile GTAS and Treasury ATB?'")
    print("   'What diagnostic rules does FedReconcile use?'")
    print()
    print("4. Module Level (FedTransform):")
    print("   'What data sources does FedTransform support?'")
    print("   'How do I convert legacy data to FBDI format?'")
    print()
    print("The RAG service is now ready for both demo queries and real usage!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
