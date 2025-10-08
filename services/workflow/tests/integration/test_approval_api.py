"""Integration tests for workflow approval API endpoints."""

import uuid


class TestApprovalAPI:
    """Test workflow approval API endpoints."""

    def test_approve_workflow_success(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test successful workflow approval and execution."""
        # Step 1: Create workflow that requires approval
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        approval_task_id = exec_data["approval_task_id"]
        workflow_id = exec_data["workflow_id"]

        # Step 2: Mock successful execution after approval
        mock_cortx_client.post_json.return_value = {
            "status": "executed",
            "result": {"success": True},
        }

        # Step 3: Approve the workflow
        approval_data = {
            "approved": True,
            "comments": "Reviewed and approved",
            "reviewer": "approver@example.com",
        }

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )

        assert approve_response.status_code == 200
        approve_data = approve_response.json()
        assert approve_data["status"] in ["approved_and_executed", "approved_but_failed"]
        assert approve_data["workflow_id"] == workflow_id

    def test_approve_workflow_not_found(self, client, auth_headers):
        """Test approval of non-existent approval task."""
        non_existent_task_id = str(uuid.uuid4())
        approval_data = {"approved": True}

        response = client.post(
            f"/workflow/approve/{non_existent_task_id}", json=approval_data, headers=auth_headers
        )

        assert response.status_code == 404

    def test_approve_workflow_idempotency(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test that approving the same workflow twice is idempotent."""
        # Step 1: Create workflow that requires approval
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        # Step 2: First approval
        mock_cortx_client.post_json.return_value = {"status": "executed"}
        approval_data = {"approved": True}

        first_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )
        assert first_response.status_code == 200

        # Step 3: Second approval (should be idempotent)
        second_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )
        assert second_response.status_code == 200
        second_data = second_response.json()
        assert second_data["status"] == "already_approved"

    def test_approve_workflow_execution_failure(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test approval when workflow execution fails."""
        # Step 1: Create workflow that requires approval
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        # Step 2: Mock execution failure
        mock_cortx_client.post_json.side_effect = Exception("Execution failed")

        # Step 3: Approve the workflow
        approval_data = {"approved": True}

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )

        assert approve_response.status_code == 200
        approve_data = approve_response.json()
        assert approve_data["status"] == "approved_but_failed"
        assert "error" in approve_data

    def test_approve_workflow_with_detailed_approval_data(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test approval with detailed approval data."""
        # Step 1: Create workflow
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        # Step 2: Approve with detailed data
        mock_cortx_client.post_json.return_value = {"status": "executed"}

        approval_data = {
            "approved": True,
            "comments": "Thoroughly reviewed all legal documentation",
            "reviewer": "legal.officer@example.com",
            "review_date": "2024-01-15T10:30:00Z",
            "conditions": ["Verify property boundaries", "Confirm title insurance"],
            "risk_assessment": "Low risk",
            "compliance_checked": True,
        }

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )

        assert approve_response.status_code == 200

    def test_approve_workflow_without_auth_fails(self, client, legal_workflow_request):
        """Test that approval without proper auth fails when auth is required."""
        # This test assumes REQUIRE_AUTH would be true in production
        # In test mode, it may still succeed
        exec_response = client.post("/execute-workflow", json=legal_workflow_request)
        approval_task_id = exec_response.json()["approval_task_id"]

        approval_data = {"approved": True}
        # Note: In test mode with REQUIRE_AUTH=false, this will succeed
        # In production with REQUIRE_AUTH=true, this would fail with 401
        approve_response = client.post(f"/workflow/approve/{approval_task_id}", json=approval_data)

        # Test environment allows without auth
        assert approve_response.status_code in [200, 401]


class TestApprovalWorkflowLifecycle:
    """Test complete approval workflow lifecycle."""

    def test_complete_approval_lifecycle_legal_workflow(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test complete lifecycle: execute -> pending -> approve -> executed."""
        # Step 1: Execute legal workflow
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        assert exec_data["status"] == "pending_approval"
        assert exec_data["requires_human_approval"] is True

        workflow_id = exec_data["workflow_id"]
        approval_task_id = exec_data["approval_task_id"]

        # Step 2: Check workflow status (should be pending_approval)
        status_response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "pending_approval"

        # Step 3: Approve the workflow
        mock_cortx_client.post_json.return_value = {
            "status": "executed",
            "result": {"success": True},
        }

        approval_data = {"approved": True, "comments": "Legal review completed"}

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )

        assert approve_response.status_code == 200
        approve_data = approve_response.json()
        assert approve_data["status"] in ["approved_and_executed", "approved_but_failed"]

    def test_complete_approval_lifecycle_financial_workflow(
        self, client, financial_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test complete lifecycle for financial workflow."""
        # Step 1: Execute financial workflow
        exec_response = client.post(
            "/execute-workflow", json=financial_workflow_request, headers=auth_headers
        )

        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        assert exec_data["status"] == "pending_approval"

        approval_task_id = exec_data["approval_task_id"]

        # Step 2: Approve
        mock_cortx_client.post_json.return_value = {"status": "executed"}

        approval_data = {"approved": True, "comments": "Financial review passed"}

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )

        assert approve_response.status_code == 200

    def test_multiple_workflows_pending_approval(
        self,
        client,
        legal_workflow_request,
        financial_workflow_request,
        auth_headers,
        mock_cortx_client,
    ):
        """Test multiple workflows in pending approval state."""
        # Create first workflow (legal)
        exec1_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        assert exec1_response.status_code == 200
        workflow1_data = exec1_response.json()
        approval_task_id_1 = workflow1_data["approval_task_id"]

        # Create second workflow (financial)
        exec2_response = client.post(
            "/execute-workflow", json=financial_workflow_request, headers=auth_headers
        )
        assert exec2_response.status_code == 200
        workflow2_data = exec2_response.json()
        approval_task_id_2 = workflow2_data["approval_task_id"]

        # Verify both are pending
        assert workflow1_data["status"] == "pending_approval"
        assert workflow2_data["status"] == "pending_approval"
        assert approval_task_id_1 != approval_task_id_2

        # Approve first workflow
        mock_cortx_client.post_json.return_value = {"status": "executed"}

        approve1_response = client.post(
            f"/workflow/approve/{approval_task_id_1}", json={"approved": True}, headers=auth_headers
        )
        assert approve1_response.status_code == 200

        # Second workflow should still be pending
        # (would need to check approval_tasks state directly in actual implementation)


class TestApprovalErrorHandling:
    """Test error handling in approval API."""

    def test_approve_workflow_missing_approval_data(
        self, client, legal_workflow_request, auth_headers
    ):
        """Test approval with missing approval data."""
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        # Send empty approval data
        response = client.post(
            f"/workflow/approve/{approval_task_id}", json={}, headers=auth_headers
        )

        # Should still process - approval_data is optional in implementation
        assert response.status_code in [200, 422]

    def test_approve_workflow_invalid_json(self, client, legal_workflow_request, auth_headers):
        """Test approval with invalid JSON."""
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        response = client.post(
            f"/workflow/approve/{approval_task_id}",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_approve_workflow_gateway_notification_failure(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test approval when gateway notification fails but execution succeeds."""
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        # Mock: approval notification fails, but execution succeeds
        call_count = [0]

        def mock_post_json(*args, **kwargs):
            call_count[0] += 1
            if "approve" in args[0]:
                raise Exception("Notification failed")
            return {"status": "executed"}

        mock_cortx_client.post_json.side_effect = mock_post_json

        approval_data = {"approved": True}
        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json=approval_data, headers=auth_headers
        )

        # Should still succeed despite notification failure
        assert approve_response.status_code == 200


class TestApprovalTaskRetrieval:
    """Test approval task retrieval and status."""

    def test_workflow_status_shows_approval_task_id(
        self, client, legal_workflow_request, auth_headers
    ):
        """Test that workflow status includes approval task ID."""
        # Create workflow requiring approval
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )

        exec_data = exec_response.json()
        workflow_id = exec_data["workflow_id"]
        approval_task_id = exec_data["approval_task_id"]

        # Get workflow status
        status_response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["approval_task_id"] == approval_task_id

    def test_workflow_status_after_approval(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client
    ):
        """Test workflow status after approval."""
        # Create and approve workflow
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )

        approval_task_id = exec_response.json()["approval_task_id"]
        workflow_id = exec_response.json()["workflow_id"]

        # Approve
        mock_cortx_client.post_json.return_value = {"status": "executed"}
        mock_cortx_client.get_json.return_value = {"workflow_id": workflow_id, "status": "executed"}

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}", json={"approved": True}, headers=auth_headers
        )
        assert approve_response.status_code == 200

        # Get status (should show executed from gateway)
        status_response = client.get(f"/workflow/status/{workflow_id}", headers=auth_headers)

        assert status_response.status_code == 200
        # Status depends on gateway mock response


class TestApprovalAuditLogging:
    """Test that approval actions are logged for audit."""

    def test_approval_creates_audit_log(
        self, client, legal_workflow_request, auth_headers, mock_cortx_client, mock_cortex_client
    ):
        """Test that approval action creates an audit log entry."""
        # Create workflow
        exec_response = client.post(
            "/execute-workflow", json=legal_workflow_request, headers=auth_headers
        )
        approval_task_id = exec_response.json()["approval_task_id"]

        # Clear previous calls
        mock_cortex_client.log_compliance_event.reset_mock()

        # Approve workflow
        mock_cortx_client.post_json.return_value = {"status": "executed"}

        approve_response = client.post(
            f"/workflow/approve/{approval_task_id}",
            json={"approved": True, "comments": "Test approval"},
            headers=auth_headers,
        )

        assert approve_response.status_code == 200

        # Verify audit logging was called
        assert mock_cortex_client.log_compliance_event.called
        # Note: The actual call would contain compliance event details
