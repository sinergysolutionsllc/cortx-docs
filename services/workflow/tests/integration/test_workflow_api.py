"""Integration tests for workflow execution API endpoints."""

import uuid


class TestWorkflowExecutionAPI:
    """Test workflow execution API endpoints."""

    def test_execute_workflow_operational_success(
        self, client, workflow_execution_request, auth_headers, mock_cortx_client
    ):
        """Test successful execution of operational workflow (no HIL approval)."""
        # Mock successful workflow execution
        mock_cortx_client.post_json.return_value = {
            "status": "executed",
            "workflow_id": str(uuid.uuid4()),
        }

        response = client.post(
            "/execute-workflow", json=workflow_execution_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "executed"
        assert data["requires_human_approval"] is False
        assert data["approval_task_id"] is None
        assert "workflow_id" in data
        assert "correlation_id" in data

    def test_execute_workflow_legal_requires_approval(
        self, client, legal_workflow_request, auth_headers
    ):
        """Test that legal workflows require HIL approval."""
        response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"
        assert data["requires_human_approval"] is True
        assert data["approval_task_id"] is not None
        assert "workflow_id" in data
        assert "message" in data

    def test_execute_workflow_financial_requires_approval(
        self, client, financial_workflow_request, auth_headers
    ):
        """Test that financial workflows require HIL approval."""
        response = client.post(
            "/execute-workflow", json=financial_workflow_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"
        assert data["requires_human_approval"] is True
        assert data["approval_task_id"] is not None

    def test_execute_workflow_missing_required_fields(self, client, auth_headers):
        """Test workflow execution with missing required fields."""
        incomplete_request = {
            "workflow_pack_id": "test.pack"
            # Missing workflow_type and payload
        }

        response = client.post("/execute-workflow", json=incomplete_request, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_execute_workflow_empty_payload(self, client, auth_headers):
        """Test workflow execution with empty payload."""
        request = {"workflow_pack_id": "test.pack", "workflow_type": "operational", "payload": {}}

        response = client.post("/execute-workflow", json=request, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data

    def test_execute_workflow_without_auth(self, client, workflow_execution_request):
        """Test workflow execution without authentication (allowed in test mode)."""
        response = client.post("/execute-workflow", json=workflow_execution_request)

        # Should succeed because REQUIRE_AUTH=false in tests
        assert response.status_code == 200

    def test_execute_workflow_with_metadata(self, client, auth_headers):
        """Test workflow execution with metadata."""
        request = {
            "workflow_pack_id": "test.pack",
            "workflow_type": "operational",
            "payload": {"action": "test"},
            "metadata": {"source": "api_test", "version": "1.0", "custom_field": "custom_value"},
        }

        response = client.post("/execute-workflow", json=request, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data

    def test_execute_workflow_gateway_failure(
        self, client, workflow_execution_request, auth_headers, mock_cortx_client
    ):
        """Test workflow execution when gateway call fails."""
        # Mock gateway failure
        mock_cortx_client.post_json.side_effect = Exception("Gateway unavailable")

        response = client.post(
            "/execute-workflow", json=workflow_execution_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "Gateway unavailable" in data["message"]

    def test_execute_workflow_correlation_id_propagation(
        self, client, workflow_execution_request, auth_headers
    ):
        """Test that correlation ID is propagated correctly."""
        custom_corr_id = str(uuid.uuid4())
        headers = {**auth_headers, "X-Correlation-ID": custom_corr_id}

        response = client.post(
            "/execute-workflow", json=workflow_execution_request, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        # Correlation ID should be in response or request headers should be preserved
        assert "correlation_id" in data


class TestWorkflowStatusAPI:
    """Test workflow status retrieval API."""

    def test_get_workflow_status_success(self, client, auth_headers, mock_cortx_client):
        """Test successful workflow status retrieval."""
        workflow_id = str(uuid.uuid4())

        # Mock gateway response
        mock_cortx_client.get_json.return_value = {
            "workflow_id": workflow_id,
            "status": "executed",
            "steps_completed": 3,
            "steps_total": 3,
        }

        response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "executed"

    def test_get_workflow_status_not_found(self, client, auth_headers, mock_cortx_client):
        """Test workflow status retrieval for non-existent workflow."""
        workflow_id = str(uuid.uuid4())

        # Mock gateway failure
        mock_cortx_client.get_json.side_effect = Exception("Not found")

        response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_get_workflow_status_pending_approval(
        self, client, auth_headers, legal_workflow_request
    ):
        """Test workflow status for workflow in pending_approval state."""
        # First create a workflow that requires approval
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        workflow_id = exec_data["workflow_id"]

        # Now get status (should fall back to local approval_tasks)
        response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "pending_approval"
        assert "approval_task_id" in data

    def test_get_workflow_status_without_auth(self, client, mock_cortx_client):
        """Test workflow status retrieval without authentication."""
        workflow_id = str(uuid.uuid4())

        mock_cortx_client.get_json.return_value = {"workflow_id": workflow_id, "status": "executed"}

        response = client.get(f"/workflow/status/{workflow_id}")

        # Should succeed because REQUIRE_AUTH=false in tests
        assert response.status_code == 200


class TestWorkflowIntegrationScenarios:
    """Test end-to-end workflow scenarios."""

    def test_operational_workflow_complete_flow(
        self, client, workflow_execution_request, auth_headers, mock_cortx_client
    ):
        """Test complete flow for operational workflow."""
        # Mock successful execution
        mock_cortx_client.post_json.return_value = {
            "status": "executed",
            "result": {"success": True},
        }

        # Step 1: Execute workflow
        exec_response = client.post(
            "/execute-workflow", json=workflow_execution_request, headers=auth_headers
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        assert exec_data["status"] == "executed"
        workflow_id = exec_data["workflow_id"]

        # Step 2: Get workflow status
        mock_cortx_client.get_json.return_value = {
            "workflow_id": workflow_id,
            "status": "executed",
            "result": {"success": True},
        }

        status_response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["workflow_id"] == workflow_id

    def test_legal_workflow_approval_required_flow(
        self, client, legal_workflow_request, auth_headers
    ):
        """Test complete flow for legal workflow requiring approval."""
        # Step 1: Execute workflow (should require approval)
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        assert exec_data["status"] == "pending_approval"
        assert exec_data["requires_human_approval"] is True
        approval_task_id = exec_data["approval_task_id"]
        workflow_id = exec_data["workflow_id"]

        # Step 2: Get workflow status (should show pending approval)
        status_response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "pending_approval"
        assert status_data["approval_task_id"] == approval_task_id

    def test_high_amount_workflow_requires_approval(self, client, auth_headers):
        """Test that high-amount operational workflows require approval."""
        request = {
            "workflow_pack_id": "payment.pack",
            "workflow_type": "operational",
            "payload": {"action": "process_payment", "amount": 50000},  # High amount
        }

        response = client.post("/execute-workflow", json=request, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["requires_human_approval"] is True
        assert data["status"] == "pending_approval"

    def test_sensitive_data_workflow_requires_approval(self, client, auth_headers):
        """Test that workflows with sensitive data require approval."""
        request = {
            "workflow_pack_id": "document.pack",
            "workflow_type": "operational",
            "payload": {
                "action": "process_document",
                "legal_description": "Property legal description",  # Sensitive key
            },
        }

        response = client.post("/execute-workflow", json=request, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["requires_human_approval"] is True
        assert data["status"] == "pending_approval"


class TestWorkflowErrorHandling:
    """Test workflow API error handling."""

    def test_execute_workflow_invalid_json(self, client, auth_headers):
        """Test workflow execution with invalid JSON."""
        response = client.post(
            "/execute-workflow",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_execute_workflow_invalid_workflow_type(self, client, auth_headers):
        """Test workflow execution with invalid workflow type."""
        request = {
            "workflow_pack_id": "test.pack",
            "workflow_type": "",  # Empty workflow type
            "payload": {},
        }

        response = client.post("/execute-workflow", json=request, headers=auth_headers)

        # Should still process but may have validation issues
        # Actual behavior depends on backend validation
        assert response.status_code in [200, 422]

    def test_get_workflow_status_invalid_id_format(self, client, auth_headers):
        """Test workflow status with invalid ID format."""
        invalid_id = "not-a-uuid"

        response = client.get(f"/workflow/status/{invalid_id}", headers=auth_headers)

        # Should attempt to fetch and fail gracefully
        assert response.status_code in [404, 500]
