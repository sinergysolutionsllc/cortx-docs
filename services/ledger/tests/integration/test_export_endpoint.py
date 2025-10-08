"""
Integration tests for GET /export endpoint
"""

import csv
import io


class TestExportEndpoint:
    """Tests for GET /export endpoint"""

    def test_export_empty(self, client, tenant_id):
        """Test exporting when there are no events"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 0

    def test_export_single_event(self, client, ledger_event):
        """Test exporting single event"""
        response = client.get(f"/export?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]

        assert row["id"] == str(ledger_event.id)
        assert row["tenant_id"] == ledger_event.tenant_id
        assert row["event_type"] == ledger_event.event_type

    def test_export_multiple_events(self, client, ledger_chain, tenant_id):
        """Test exporting multiple events"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 5

    def test_export_chronological_order(self, client, ledger_chain, tenant_id):
        """Test that export is in chronological order (oldest first)"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        # Verify order is chronological (oldest first)
        for i in range(len(rows) - 1):
            assert rows[i]["created_at"] <= rows[i + 1]["created_at"]

    def test_export_csv_headers(self, client, tenant_id):
        """Test that CSV has correct headers"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))

        expected_headers = [
            "id",
            "tenant_id",
            "event_type",
            "created_at",
            "content_hash",
            "previous_hash",
            "chain_hash",
            "user_id",
            "correlation_id",
            "description",
        ]

        assert reader.fieldnames == expected_headers

    def test_export_csv_values(self, client, ledger_event):
        """Test that CSV contains correct values"""
        response = client.get(f"/export?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]

        assert row["id"] == str(ledger_event.id)
        assert row["tenant_id"] == ledger_event.tenant_id
        assert row["event_type"] == ledger_event.event_type
        assert row["content_hash"] == ledger_event.content_hash
        assert row["previous_hash"] == ledger_event.previous_hash
        assert row["chain_hash"] == ledger_event.chain_hash

    def test_export_optional_fields(self, client, db_session, tenant_id):
        """Test export with optional fields populated"""
        from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
        from app.models import LedgerEvent

        event_data = {"test": "data"}
        content_hash = compute_content_hash(event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test",
            event_data=event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
            user_id="test-user",
            correlation_id="test-correlation",
            description="Test description",
        )

        db_session.add(event)
        db_session.commit()

        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        row = rows[0]
        assert row["user_id"] == "test-user"
        assert row["correlation_id"] == "test-correlation"
        assert row["description"] == "Test description"

    def test_export_empty_optional_fields(self, client, db_session, tenant_id):
        """Test export with optional fields empty"""
        from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
        from app.models import LedgerEvent

        event_data = {"test": "data"}
        content_hash = compute_content_hash(event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test",
            event_data=event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        db_session.add(event)
        db_session.commit()

        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        row = rows[0]
        assert row["user_id"] == ""
        assert row["correlation_id"] == ""
        assert row["description"] == ""

    def test_export_filter_by_event_type(self, client, ledger_chain, tenant_id):
        """Test exporting with event_type filter"""
        response = client.get(f"/export?tenant_id={tenant_id}&event_type=event_type_0")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["event_type"] == "event_type_0"

    def test_export_filter_no_matches(self, client, ledger_chain, tenant_id):
        """Test exporting with filter that matches no events"""
        response = client.get(f"/export?tenant_id={tenant_id}&event_type=nonexistent")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 0

    def test_export_filename(self, client, tenant_id):
        """Test that export filename includes tenant_id"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        content_disposition = response.headers["content-disposition"]
        assert f"ledger_{tenant_id}.csv" in content_disposition

    def test_export_multi_tenant_isolation(self, client, multi_tenant_events):
        """Test that export is isolated by tenant"""
        # Export for tenant-a
        response = client.get("/export?tenant_id=tenant-a")
        assert response.status_code == 200

        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 3
        assert all(row["tenant_id"] == "tenant-a" for row in rows)

        # Export for tenant-b
        response = client.get("/export?tenant_id=tenant-b")
        assert response.status_code == 200

        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 2
        assert all(row["tenant_id"] == "tenant-b" for row in rows)

    def test_export_missing_tenant_id(self, client):
        """Test export without tenant_id parameter"""
        response = client.get("/export")

        assert response.status_code == 422  # Validation error

    def test_export_nonexistent_tenant(self, client):
        """Test exporting for nonexistent tenant"""
        response = client.get("/export?tenant_id=nonexistent")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 0

    def test_export_csv_format_valid(self, client, ledger_chain, tenant_id):
        """Test that exported CSV is valid format"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Should be able to parse as CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        # Should have rows
        assert len(rows) > 0

        # All rows should have same number of fields
        num_fields = len(rows[0])
        assert all(len(row) == num_fields for row in rows)

    def test_export_special_characters_in_data(self, client, db_session, tenant_id):
        """Test export with special characters in data"""
        from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
        from app.models import LedgerEvent

        event_data = {
            "text": 'Data with "quotes" and commas, and newlines\n',
            "special": "Special chars: !@#$%^&*()",
        }
        content_hash = compute_content_hash(event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test",
            event_data=event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
            description='Description with "quotes" and commas, too',
        )

        db_session.add(event)
        db_session.commit()

        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Should still parse correctly
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 1

    def test_export_large_dataset(self, client, db_session, tenant_id):
        """Test exporting larger dataset"""
        from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
        from app.models import LedgerEvent

        # Create 100 events
        previous_hash = GENESIS_HASH
        for i in range(100):
            event_data = {"sequence": i}
            content_hash = compute_content_hash(event_data)
            chain_hash = compute_chain_hash(content_hash, previous_hash)

            event = LedgerEvent(
                tenant_id=tenant_id,
                event_type="test",
                event_data=event_data,
                content_hash=content_hash,
                previous_hash=previous_hash,
                chain_hash=chain_hash,
            )

            db_session.add(event)
            previous_hash = chain_hash

        db_session.commit()

        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) == 100

    def test_export_content_type(self, client, tenant_id):
        """Test that export returns correct content type"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_disposition_attachment(self, client, tenant_id):
        """Test that export has attachment disposition"""
        response = client.get(f"/export?tenant_id={tenant_id}")

        assert response.status_code == 200
        assert "attachment" in response.headers["content-disposition"]

    def test_export_does_not_include_event_data_json(self, client, ledger_event):
        """Test that export CSV does not include event_data field (it's complex JSON)"""
        response = client.get(f"/export?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))

        # event_data should not be in headers (it's not in the CSV export)
        assert "event_data" not in reader.fieldnames
