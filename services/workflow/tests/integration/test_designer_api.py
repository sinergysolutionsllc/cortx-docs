"""Integration tests for Designer compilation API endpoints."""



class TestDesignerCompileAPI:
    """Test Designer compilation API endpoints."""

    def test_compile_designer_output_success(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test successful Designer output compilation."""
        # Mock successful compilation and orchestrator submission
        mock_cortx_client.post_json.return_value = {
            "pack_id": "pack_abc123",
            "status": "compiled",
            "job_id": "job_xyz789",
        }

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"
        assert "pack_id" in data
        assert data["pack_id"] is not None
        assert "correlation_id" in data

    def test_compile_designer_output_with_validation(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test Designer compilation with schema validation enabled."""
        designer_compile_request["validate_schema"] = True

        # Mock schema validation success
        call_count = [0]

        def mock_post_json(path, *args, **kwargs):
            call_count[0] += 1
            if "validate" in path:
                return {"valid": True, "errors": []}
            elif "compile" in path:
                return {"pack_id": "pack_123", "status": "compiled"}
            elif "submit" in path:
                return {"job_id": "job_456"}
            return {}

        mock_cortx_client.post_json.side_effect = mock_post_json

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"
        assert len(data["validation_errors"]) == 0

    def test_compile_designer_output_validation_failure(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test Designer compilation with validation errors."""
        designer_compile_request["validate_schema"] = True

        # Mock schema validation failure
        validation_errors = [
            "Missing required field: workflow_id",
            "Invalid step type: unknown_type",
        ]

        mock_cortx_client.post_json.return_value = {"valid": False, "errors": validation_errors}

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "validation_error"
        assert len(data["validation_errors"]) == 2
        assert data["pack_id"] is None

    def test_compile_designer_output_without_validation(
        self, client, auth_headers, mock_cortx_client
    ):
        """Test Designer compilation with validation disabled."""
        request = {
            "designer_output": {"type": "workflow", "steps": []},
            "output_format": "json",
            "validate_schema": False,
        }

        # Mock successful compilation
        mock_cortx_client.post_json.return_value = {"pack_id": "pack_123", "job_id": "job_456"}

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"

    def test_compile_designer_output_bpmn_format(self, client, auth_headers, mock_cortx_client):
        """Test Designer compilation with BPMN output format."""
        request = {
            "designer_output": {"type": "workflow", "steps": []},
            "output_format": "bpmn",
            "validate_schema": True,
        }

        mock_cortx_client.post_json.return_value = {
            "pack_id": "pack_123",
            "format": "bpmn",
            "job_id": "job_456",
        }

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        assert response.status_code == 200

    def test_compile_designer_output_compilation_failure(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test Designer compilation when compilation fails."""
        # Mock compilation failure
        mock_cortx_client.post_json.side_effect = Exception("Compilation service unavailable")

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "failed"
        assert len(data["validation_errors"]) > 0

    def test_compile_designer_output_orchestrator_failure(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test Designer compilation when orchestrator submission fails."""
        call_count = [0]

        def mock_post_json(path, *args, **kwargs):
            call_count[0] += 1
            if "compile" in path:
                return {"pack_id": "pack_123"}
            elif "submit" in path:
                raise Exception("Orchestrator unavailable")
            return {}

        mock_cortx_client.post_json.side_effect = mock_post_json

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"
        assert data["pack_id"] == "pack_123"
        assert data["orchestrator_job_id"] is None

    def test_compile_designer_output_with_metadata(self, client, auth_headers, mock_cortx_client):
        """Test Designer compilation with metadata."""
        request = {
            "designer_output": {"type": "workflow", "steps": []},
            "output_format": "json",
            "validate_schema": True,
            "metadata": {
                "designer_version": "2.1.0",
                "author": "test@example.com",
                "organization": "Test Org",
            },
        }

        mock_cortx_client.post_json.return_value = {"pack_id": "pack_123", "job_id": "job_456"}

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        assert response.status_code == 200

    def test_compile_designer_output_missing_required_fields(self, client, auth_headers):
        """Test Designer compilation with missing required fields."""
        incomplete_request = {
            "output_format": "json"
            # Missing designer_output
        }

        response = client.post("/designer/compile", json=incomplete_request, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_compile_designer_output_without_auth(self, client, designer_compile_request):
        """Test Designer compilation without authentication."""
        response = client.post("/designer/compile", json=designer_compile_request)

        # Should succeed in test mode (REQUIRE_AUTH=false)
        assert response.status_code in [200, 401, 500]


class TestDesignerCompileComplexWorkflows:
    """Test Designer compilation with complex workflow structures."""

    def test_compile_multi_step_workflow(self, client, auth_headers, mock_cortx_client):
        """Test compilation of multi-step workflow."""
        request = {
            "designer_output": {
                "type": "workflow",
                "id": "complex_workflow",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "type": "validation",
                        "config": {"rule_pack": "input.validation"},
                    },
                    {
                        "id": "step2",
                        "type": "transformation",
                        "config": {"transformer": "data.transform"},
                    },
                    {"id": "step3", "type": "enrichment", "config": {"enricher": "data.enrich"}},
                    {"id": "step4", "type": "action", "config": {"action": "send_notification"}},
                ],
                "transitions": [
                    {"from": "step1", "to": "step2", "condition": "success"},
                    {"from": "step2", "to": "step3", "condition": "success"},
                    {"from": "step3", "to": "step4", "condition": "success"},
                ],
            },
            "output_format": "json",
            "validate_schema": False,
        }

        mock_cortx_client.post_json.return_value = {
            "pack_id": "pack_complex_123",
            "job_id": "job_456",
        }

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"

    def test_compile_workflow_with_conditional_branches(
        self, client, auth_headers, mock_cortx_client
    ):
        """Test compilation of workflow with conditional branches."""
        request = {
            "designer_output": {
                "type": "workflow",
                "id": "branching_workflow",
                "steps": [
                    {"id": "decision", "type": "condition"},
                    {"id": "branch_a", "type": "action"},
                    {"id": "branch_b", "type": "action"},
                ],
                "transitions": [
                    {"from": "decision", "to": "branch_a", "condition": "value > 100"},
                    {"from": "decision", "to": "branch_b", "condition": "value <= 100"},
                ],
            },
            "output_format": "json",
        }

        mock_cortx_client.post_json.return_value = {
            "pack_id": "pack_branch_123",
            "job_id": "job_456",
        }

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        assert response.status_code == 200

    def test_compile_workflow_with_parallel_steps(self, client, auth_headers, mock_cortx_client):
        """Test compilation of workflow with parallel execution steps."""
        request = {
            "designer_output": {
                "type": "workflow",
                "id": "parallel_workflow",
                "steps": [
                    {"id": "start", "type": "trigger"},
                    {"id": "parallel_1", "type": "action", "execution": "parallel"},
                    {"id": "parallel_2", "type": "action", "execution": "parallel"},
                    {"id": "parallel_3", "type": "action", "execution": "parallel"},
                    {"id": "merge", "type": "merge"},
                ],
            },
            "output_format": "json",
        }

        mock_cortx_client.post_json.return_value = {
            "pack_id": "pack_parallel_123",
            "job_id": "job_456",
        }

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        assert response.status_code == 200


class TestDesignerCompileErrorScenarios:
    """Test Designer compilation error scenarios."""

    def test_compile_with_invalid_json(self, client, auth_headers):
        """Test compilation with invalid JSON."""
        response = client.post(
            "/designer/compile",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_compile_with_empty_workflow(self, client, auth_headers, mock_cortx_client):
        """Test compilation with empty workflow."""
        request = {"designer_output": {}, "output_format": "json"}

        mock_cortx_client.post_json.return_value = {
            "pack_id": "pack_empty_123",
            "job_id": "job_456",
        }

        response = client.post("/designer/compile", json=request, headers=auth_headers)

        # Should attempt to compile even with empty workflow
        assert response.status_code in [200, 500]

    def test_compile_missing_pack_id_in_response(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test compilation when pack compiler doesn't return pack_id."""
        # Mock response without pack_id
        mock_cortx_client.post_json.return_value = {
            "status": "compiled"
            # Missing pack_id
        }

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "failed"

    def test_compile_schema_validation_service_unavailable(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test compilation when schema validation service is unavailable."""
        designer_compile_request["validate_schema"] = True

        call_count = [0]

        def mock_post_json(path, *args, **kwargs):
            call_count[0] += 1
            if "validate" in path:
                raise Exception("Schema service unavailable")
            elif "compile" in path:
                return {"pack_id": "pack_123"}
            elif "submit" in path:
                return {"job_id": "job_456"}
            return {}

        mock_cortx_client.post_json.side_effect = mock_post_json

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        # Should continue without schema validation
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"


class TestDesignerCompileAuditLogging:
    """Test that Designer compilation actions are audited."""

    def test_compile_creates_audit_log(
        self, client, designer_compile_request, auth_headers, mock_cortx_client, mock_cortex_client
    ):
        """Test that compilation creates audit log entry."""
        mock_cortx_client.post_json.return_value = {"pack_id": "pack_123", "job_id": "job_456"}

        # Clear previous calls
        mock_cortex_client.log_compliance_event.reset_mock()

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200

        # Verify audit logging was called
        assert mock_cortex_client.log_compliance_event.called

    def test_compile_failure_creates_audit_log(
        self, client, designer_compile_request, auth_headers, mock_cortx_client, mock_cortex_client
    ):
        """Test that compilation failure is logged to audit."""
        mock_cortx_client.post_json.side_effect = Exception("Compilation failed")

        # Clear previous calls
        mock_cortex_client.log_compliance_event.reset_mock()

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 500

        # Verify audit logging was called
        assert mock_cortex_client.log_compliance_event.called


class TestDesignerCompileOrchestratorIntegration:
    """Test Designer compilation and orchestrator integration."""

    def test_compile_with_orchestrator_job_submission(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test that successful compilation submits job to orchestrator."""
        call_count = [0]

        def mock_post_json(path, *args, **kwargs):
            call_count[0] += 1
            if "compile" in path:
                return {"pack_id": "pack_123"}
            elif "submit" in path:
                return {"job_id": "job_orchestrator_456"}
            return {}

        mock_cortx_client.post_json.side_effect = mock_post_json

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"
        assert data["pack_id"] == "pack_123"
        assert data["orchestrator_job_id"] == "job_orchestrator_456"

    def test_compile_success_orchestrator_failure_still_returns_pack(
        self, client, designer_compile_request, auth_headers, mock_cortx_client
    ):
        """Test that pack is returned even if orchestrator submission fails."""
        call_count = [0]

        def mock_post_json(path, *args, **kwargs):
            call_count[0] += 1
            if "compile" in path:
                return {"pack_id": "pack_123"}
            elif "submit" in path:
                raise Exception("Orchestrator down")
            return {}

        mock_cortx_client.post_json.side_effect = mock_post_json

        response = client.post(
            "/designer/compile", json=designer_compile_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compiled"
        assert data["pack_id"] == "pack_123"
        assert data["orchestrator_job_id"] is None
        assert "Orchestrator submission failed" in data["message"]
