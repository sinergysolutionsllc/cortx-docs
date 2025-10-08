"""Unit tests for workflow execution logic."""

import pytest
from app.main import requires_hil_approval


class TestHILApprovalLogic:
    """Test Human-in-the-Loop approval decision logic."""

    def test_requires_hil_for_legal_workflow(self):
        """Test that legal workflows require HIL approval."""
        workflow_type = "legal"
        payload = {"document": "test"}

        assert requires_hil_approval(workflow_type, payload) is True

    def test_requires_hil_for_financial_workflow(self):
        """Test that financial workflows require HIL approval."""
        workflow_type = "financial"
        payload = {"transaction": "test"}

        assert requires_hil_approval(workflow_type, payload) is True

    def test_requires_hil_for_title_workflow(self):
        """Test that title workflows require HIL approval."""
        workflow_type = "title"
        payload = {"property": "test"}

        assert requires_hil_approval(workflow_type, payload) is True

    def test_requires_hil_for_ownership_workflow(self):
        """Test that ownership workflows require HIL approval."""
        workflow_type = "ownership"
        payload = {"owner": "test"}

        assert requires_hil_approval(workflow_type, payload) is True

    def test_requires_hil_for_lien_workflow(self):
        """Test that lien workflows require HIL approval."""
        workflow_type = "lien"
        payload = {"lien_id": "test"}

        assert requires_hil_approval(workflow_type, payload) is True

    def test_no_hil_for_operational_workflow(self):
        """Test that operational workflows don't require HIL approval."""
        workflow_type = "operational"
        payload = {"action": "process"}

        assert requires_hil_approval(workflow_type, payload) is False

    def test_requires_hil_for_sensitive_payload_keys(self):
        """Test that workflows with sensitive payload keys require HIL approval."""
        workflow_type = "operational"

        # Test various sensitive keys
        sensitive_payloads = [
            {"legal_description": "Lot 1, Block 2"},
            {"ownership_chain": ["Owner A", "Owner B"]},
            {"lien_data": {"amount": 10000}},
            {"judgment": "Court judgment"},
            {"title_commitment": "TC-001"},
            {"deed": "Deed document"},
            {"mortgage": "Mortgage details"},
            {"encumbrance": "Encumbrance data"},
        ]

        for payload in sensitive_payloads:
            assert (
                requires_hil_approval(workflow_type, payload) is True
            ), f"Failed for payload: {payload}"

    def test_requires_hil_for_high_amount(self):
        """Test that workflows with amounts >$10,000 require HIL approval."""
        workflow_type = "operational"

        # High amount - requires approval
        payload = {"payment_amount": 15000}
        assert requires_hil_approval(workflow_type, payload) is True

        # Very high amount - requires approval
        payload = {"total_amount": 100000}
        assert requires_hil_approval(workflow_type, payload) is True

    def test_no_hil_for_low_amount(self):
        """Test that workflows with amounts <=$10,000 don't require HIL approval."""
        workflow_type = "operational"

        # Low amount - no approval needed
        payload = {"amount": 5000}
        assert requires_hil_approval(workflow_type, payload) is False

        # Exactly at threshold - no approval needed
        payload = {"amount": 10000}
        assert requires_hil_approval(workflow_type, payload) is False

    def test_no_hil_for_non_sensitive_operational_workflow(self):
        """Test that normal operational workflows don't require HIL approval."""
        workflow_type = "operational"
        payload = {
            "action": "generate_report",
            "report_type": "monthly",
            "parameters": {"format": "pdf"},
        }

        assert requires_hil_approval(workflow_type, payload) is False

    def test_case_insensitive_workflow_type(self):
        """Test that workflow type checking is case-insensitive."""
        # Test uppercase
        assert requires_hil_approval("LEGAL", {}) is True
        assert requires_hil_approval("FINANCIAL", {}) is True

        # Test mixed case
        assert requires_hil_approval("Legal", {}) is True
        assert requires_hil_approval("Financial", {}) is True

    def test_case_insensitive_payload_keys(self):
        """Test that payload key checking is case-insensitive."""
        workflow_type = "operational"

        # Test uppercase keys
        payload = {"LEGAL_DESCRIPTION": "test"}
        assert requires_hil_approval(workflow_type, payload) is True

        # Test mixed case keys
        payload = {"Legal_Description": "test"}
        assert requires_hil_approval(workflow_type, payload) is True

    def test_amount_in_various_key_names(self):
        """Test that amount threshold works with various key names."""
        workflow_type = "operational"

        # Various amount key names
        amount_keys = [
            "amount",
            "total_amount",
            "payment_amount",
            "transaction_amount",
            "loan_amount",
        ]

        for key in amount_keys:
            # High amount
            payload = {key: 15000}
            assert (
                requires_hil_approval(workflow_type, payload) is True
            ), f"Failed for high amount with key: {key}"

            # Low amount
            payload = {key: 5000}
            assert (
                requires_hil_approval(workflow_type, payload) is False
            ), f"Failed for low amount with key: {key}"

    def test_non_numeric_amount_values(self):
        """Test that non-numeric amount values don't cause errors."""
        workflow_type = "operational"

        # String amount value
        payload = {"amount": "not a number"}
        assert requires_hil_approval(workflow_type, payload) is False

        # None amount value
        payload = {"amount": None}
        assert requires_hil_approval(workflow_type, payload) is False

        # List amount value
        payload = {"amount": [1, 2, 3]}
        assert requires_hil_approval(workflow_type, payload) is False

    def test_multiple_conditions_requiring_hil(self):
        """Test that multiple conditions requiring HIL all return True."""
        # Both legal type AND sensitive key
        workflow_type = "legal"
        payload = {"legal_description": "test"}
        assert requires_hil_approval(workflow_type, payload) is True

        # Both financial type AND high amount
        workflow_type = "financial"
        payload = {"amount": 50000}
        assert requires_hil_approval(workflow_type, payload) is True

        # Operational type with BOTH sensitive key AND high amount
        workflow_type = "operational"
        payload = {"legal_description": "test", "amount": 50000}
        assert requires_hil_approval(workflow_type, payload) is True

    def test_empty_payload(self):
        """Test with empty payload."""
        # Legal type with empty payload - still requires approval
        assert requires_hil_approval("legal", {}) is True

        # Operational type with empty payload - no approval needed
        assert requires_hil_approval("operational", {}) is False

    def test_complex_nested_payload(self):
        """Test that nested structures are handled correctly."""
        workflow_type = "operational"

        # Nested structure with sensitive key at top level
        payload = {"data": {"nested": "value"}, "legal_description": "test"}
        assert requires_hil_approval(workflow_type, payload) is True

        # Nested structure with amount at top level
        payload = {"data": {"nested": "value"}, "total_amount": 50000}
        assert requires_hil_approval(workflow_type, payload) is True


class TestWorkflowModels:
    """Test Pydantic models for workflow requests/responses."""

    def test_workflow_execution_request_validation(self):
        """Test WorkflowExecutionRequest model validation."""
        from app.main import WorkflowExecutionRequest

        # Valid request
        request = WorkflowExecutionRequest(
            workflow_pack_id="test.pack", workflow_type="operational", payload={"key": "value"}
        )
        assert request.workflow_pack_id == "test.pack"
        assert request.workflow_type == "operational"
        assert request.payload == {"key": "value"}
        assert request.metadata is None

        # With metadata
        request = WorkflowExecutionRequest(
            workflow_pack_id="test.pack",
            workflow_type="operational",
            payload={"key": "value"},
            metadata={"source": "api"},
        )
        assert request.metadata == {"source": "api"}

    def test_workflow_execution_request_missing_fields(self):
        """Test WorkflowExecutionRequest with missing required fields."""
        from app.main import WorkflowExecutionRequest
        from pydantic import ValidationError

        # Missing workflow_pack_id
        with pytest.raises(ValidationError):
            WorkflowExecutionRequest(workflow_type="operational", payload={"key": "value"})

        # Missing workflow_type
        with pytest.raises(ValidationError):
            WorkflowExecutionRequest(workflow_pack_id="test.pack", payload={"key": "value"})

        # Missing payload
        with pytest.raises(ValidationError):
            WorkflowExecutionRequest(workflow_pack_id="test.pack", workflow_type="operational")

    def test_workflow_execution_response_validation(self):
        """Test WorkflowExecutionResponse model validation."""
        from app.main import WorkflowExecutionResponse

        # Executed response
        response = WorkflowExecutionResponse(
            status="executed",
            workflow_id="wf_123",
            approval_task_id=None,
            requires_human_approval=False,
            correlation_id="corr_123",
        )
        assert response.status == "executed"
        assert response.requires_human_approval is False
        assert response.approval_task_id is None

        # Pending approval response
        response = WorkflowExecutionResponse(
            status="pending_approval",
            workflow_id="wf_123",
            approval_task_id="task_456",
            requires_human_approval=True,
            correlation_id="corr_123",
            message="Requires approval",
        )
        assert response.status == "pending_approval"
        assert response.requires_human_approval is True
        assert response.approval_task_id == "task_456"
        assert response.message == "Requires approval"

    def test_designer_compile_request_validation(self):
        """Test DesignerCompileRequest model validation."""
        from app.main import DesignerCompileRequest

        # Valid request with defaults
        request = DesignerCompileRequest(designer_output={"type": "workflow", "steps": []})
        assert request.designer_output == {"type": "workflow", "steps": []}
        assert request.output_format == "json"
        assert request.validate_schema is True
        assert request.metadata is None

        # With custom values
        request = DesignerCompileRequest(
            designer_output={"type": "workflow"},
            output_format="bpmn",
            validate_schema=False,
            metadata={"version": "2.0"},
        )
        assert request.output_format == "bpmn"
        assert request.validate_schema is False
        assert request.metadata == {"version": "2.0"}

    def test_designer_compile_response_validation(self):
        """Test DesignerCompileResponse model validation."""
        from app.main import DesignerCompileResponse

        # Successful compilation
        response = DesignerCompileResponse(
            status="compiled",
            pack_id="pack_123",
            orchestrator_job_id="job_456",
            correlation_id="corr_123",
        )
        assert response.status == "compiled"
        assert response.pack_id == "pack_123"
        assert response.orchestrator_job_id == "job_456"
        assert response.validation_errors == []

        # Failed with validation errors
        response = DesignerCompileResponse(
            status="validation_error",
            pack_id=None,
            orchestrator_job_id=None,
            validation_errors=["Error 1", "Error 2"],
            correlation_id="corr_123",
            message="Validation failed",
        )
        assert response.status == "validation_error"
        assert response.pack_id is None
        assert len(response.validation_errors) == 2
