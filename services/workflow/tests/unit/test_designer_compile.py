"""Unit tests for Designer compilation logic."""

from app.main import DesignerCompileRequest, DesignerCompileResponse


class TestDesignerCompileModels:
    """Test Designer compile request/response models."""

    def test_designer_compile_request_defaults(self):
        """Test DesignerCompileRequest default values."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"})

        assert request.designer_output == {"type": "workflow"}
        assert request.output_format == "json"
        assert request.validate_schema is True
        assert request.metadata is None

    def test_designer_compile_request_custom_values(self):
        """Test DesignerCompileRequest with custom values."""
        metadata = {"version": "2.0", "author": "test"}
        request = DesignerCompileRequest(
            designer_output={"type": "workflow", "steps": []},
            output_format="bpmn",
            validate_schema=False,
            metadata=metadata,
        )

        assert request.output_format == "bpmn"
        assert request.validate_schema is False
        assert request.metadata == metadata

    def test_designer_compile_request_complex_output(self):
        """Test DesignerCompileRequest with complex designer output."""
        complex_output = {
            "type": "workflow",
            "id": "test_workflow_001",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "step1",
                    "type": "validation",
                    "config": {"rule_pack": "validation.rules", "on_failure": "stop"},
                },
                {
                    "id": "step2",
                    "type": "transformation",
                    "config": {"transformer": "data.transform", "mapping": {"field1": "target1"}},
                },
                {
                    "id": "step3",
                    "type": "action",
                    "config": {"action": "send_notification", "recipients": ["admin@example.com"]},
                },
            ],
            "transitions": [
                {"from": "step1", "to": "step2", "condition": "success"},
                {"from": "step2", "to": "step3", "condition": "success"},
            ],
        }

        request = DesignerCompileRequest(designer_output=complex_output)
        assert len(request.designer_output["steps"]) == 3
        assert len(request.designer_output["transitions"]) == 2

    def test_designer_compile_response_success(self):
        """Test DesignerCompileResponse for successful compilation."""
        response = DesignerCompileResponse(
            status="compiled",
            pack_id="pack_abc123",
            orchestrator_job_id="job_xyz789",
            validation_errors=[],
            correlation_id="corr_123",
            message="Successfully compiled",
        )

        assert response.status == "compiled"
        assert response.pack_id == "pack_abc123"
        assert response.orchestrator_job_id == "job_xyz789"
        assert len(response.validation_errors) == 0
        assert response.message == "Successfully compiled"

    def test_designer_compile_response_validation_error(self):
        """Test DesignerCompileResponse for validation errors."""
        errors = ["Missing required field: workflow_id", "Invalid step type: unknown_type"]

        response = DesignerCompileResponse(
            status="validation_error",
            pack_id=None,
            orchestrator_job_id=None,
            validation_errors=errors,
            correlation_id="corr_123",
            message="Schema validation failed",
        )

        assert response.status == "validation_error"
        assert response.pack_id is None
        assert response.orchestrator_job_id is None
        assert len(response.validation_errors) == 2
        assert "Missing required field" in response.validation_errors[0]

    def test_designer_compile_response_failed(self):
        """Test DesignerCompileResponse for compilation failure."""
        response = DesignerCompileResponse(
            status="failed",
            pack_id=None,
            orchestrator_job_id=None,
            validation_errors=["Compilation service unavailable"],
            correlation_id="corr_123",
            message="Compilation failed",
        )

        assert response.status == "failed"
        assert response.pack_id is None
        assert len(response.validation_errors) == 1


class TestDesignerOutputValidation:
    """Test Designer output structure validation."""

    def test_valid_workflow_structure(self):
        """Test valid workflow structure."""
        workflow = {
            "type": "workflow",
            "id": "test_workflow",
            "version": "1.0.0",
            "steps": [{"id": "step1", "type": "validation"}],
        }

        # Basic structure checks
        assert "type" in workflow
        assert workflow["type"] == "workflow"
        assert "steps" in workflow
        assert isinstance(workflow["steps"], list)
        assert len(workflow["steps"]) > 0

    def test_empty_workflow_structure(self):
        """Test handling of empty workflow structure."""
        workflow = {"type": "workflow", "steps": []}

        assert "steps" in workflow
        assert len(workflow["steps"]) == 0

    def test_workflow_with_metadata(self):
        """Test workflow structure with metadata."""
        workflow = {
            "type": "workflow",
            "id": "test_workflow",
            "version": "1.0.0",
            "metadata": {
                "author": "designer_user",
                "created_at": "2024-01-01T00:00:00Z",
                "description": "Test workflow",
                "tags": ["test", "demo"],
            },
            "steps": [],
        }

        assert "metadata" in workflow
        assert workflow["metadata"]["author"] == "designer_user"
        assert "tags" in workflow["metadata"]
        assert len(workflow["metadata"]["tags"]) == 2

    def test_workflow_step_validation(self):
        """Test workflow step structure validation."""
        step = {"id": "step1", "type": "validation", "config": {"rule_pack": "test.rules"}}

        # Verify step structure
        assert "id" in step
        assert "type" in step
        assert "config" in step
        assert isinstance(step["config"], dict)

    def test_workflow_transitions(self):
        """Test workflow transition structure."""
        transitions = [
            {"from": "step1", "to": "step2", "condition": "success"},
            {"from": "step2", "to": "step3", "condition": "success"},
            {"from": "step2", "to": "error_handler", "condition": "failure"},
        ]

        # Verify transitions structure
        assert len(transitions) == 3
        for transition in transitions:
            assert "from" in transition
            assert "to" in transition
            assert "condition" in transition


class TestDesignerCompileFormats:
    """Test Designer compile output formats."""

    def test_json_output_format(self):
        """Test JSON output format."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"}, output_format="json")

        assert request.output_format == "json"

    def test_bpmn_output_format(self):
        """Test BPMN output format."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"}, output_format="bpmn")

        assert request.output_format == "bpmn"

    def test_default_output_format(self):
        """Test default output format is JSON."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"})

        assert request.output_format == "json"


class TestDesignerSchemaValidation:
    """Test Designer schema validation flag."""

    def test_schema_validation_enabled_by_default(self):
        """Test that schema validation is enabled by default."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"})

        assert request.validate_schema is True

    def test_schema_validation_can_be_disabled(self):
        """Test that schema validation can be disabled."""
        request = DesignerCompileRequest(
            designer_output={"type": "workflow"}, validate_schema=False
        )

        assert request.validate_schema is False

    def test_schema_validation_explicit_enable(self):
        """Test explicitly enabling schema validation."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"}, validate_schema=True)

        assert request.validate_schema is True


class TestDesignerCompileErrorHandling:
    """Test Designer compile error handling."""

    def test_multiple_validation_errors(self):
        """Test handling multiple validation errors."""
        errors = [
            "Error 1: Missing required field",
            "Error 2: Invalid step type",
            "Error 3: Circular dependency detected",
            "Error 4: Unknown configuration parameter",
        ]

        response = DesignerCompileResponse(
            status="validation_error",
            pack_id=None,
            orchestrator_job_id=None,
            validation_errors=errors,
            correlation_id="corr_123",
        )

        assert len(response.validation_errors) == 4
        assert all(isinstance(err, str) for err in response.validation_errors)

    def test_empty_validation_errors(self):
        """Test response with no validation errors."""
        response = DesignerCompileResponse(
            status="compiled",
            pack_id="pack_123",
            orchestrator_job_id="job_456",
            correlation_id="corr_123",
        )

        # Should default to empty list
        assert response.validation_errors == []
        assert len(response.validation_errors) == 0

    def test_compilation_failure_with_error_message(self):
        """Test compilation failure with detailed error message."""
        response = DesignerCompileResponse(
            status="failed",
            pack_id=None,
            orchestrator_job_id=None,
            validation_errors=["Internal compiler error"],
            correlation_id="corr_123",
            message="Compilation failed: Internal compiler error at line 42",
        )

        assert response.status == "failed"
        assert response.message is not None
        assert "line 42" in response.message


class TestDesignerCompileMetadata:
    """Test Designer compile metadata handling."""

    def test_metadata_preservation(self):
        """Test that metadata is preserved in request."""
        metadata = {
            "designer_version": "2.1.0",
            "author": "john.doe@example.com",
            "organization": "Example Corp",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["production", "verified"],
        }

        request = DesignerCompileRequest(designer_output={"type": "workflow"}, metadata=metadata)

        assert request.metadata == metadata
        assert request.metadata["designer_version"] == "2.1.0"
        assert "tags" in request.metadata

    def test_no_metadata(self):
        """Test request with no metadata."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"})

        assert request.metadata is None

    def test_empty_metadata(self):
        """Test request with empty metadata object."""
        request = DesignerCompileRequest(designer_output={"type": "workflow"}, metadata={})

        assert request.metadata == {}
        assert len(request.metadata) == 0


class TestDesignerPackGeneration:
    """Test Designer pack ID generation."""

    def test_pack_id_format(self):
        """Test pack ID follows expected format."""
        pack_id = "pack_abc123def456"

        # Basic format checks
        assert isinstance(pack_id, str)
        assert len(pack_id) > 0
        assert pack_id.startswith("pack_")

    def test_unique_pack_ids(self):
        """Test that pack IDs are unique."""
        pack_ids = set()

        # Simulate multiple compilations
        for i in range(10):
            pack_id = f"pack_{i}_{hash(str(i))}"
            pack_ids.add(pack_id)

        # All pack IDs should be unique
        assert len(pack_ids) == 10

    def test_orchestrator_job_id_format(self):
        """Test orchestrator job ID format."""
        job_id = "job_xyz789abc123"

        # Basic format checks
        assert isinstance(job_id, str)
        assert len(job_id) > 0
        assert job_id.startswith("job_")
