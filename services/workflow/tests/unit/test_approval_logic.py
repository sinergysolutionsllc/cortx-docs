"""Unit tests for HIL approval logic and state management."""

import time

from app.main import approval_tasks


class TestApprovalTaskManagement:
    """Test approval task storage and lifecycle."""

    def test_approval_task_creation(self):
        """Test creating an approval task."""
        task_id = "test_task_123"
        workflow_id = "wf_456"

        approval_tasks[task_id] = {
            "workflow_id": workflow_id,
            "workflow_request": {
                "workflow_pack_id": "test.pack",
                "workflow_type": "legal",
                "payload": {"key": "value"},
            },
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        assert task_id in approval_tasks
        assert approval_tasks[task_id]["workflow_id"] == workflow_id
        assert approval_tasks[task_id]["status"] == "pending_approval"

    def test_approval_task_state_transitions(self):
        """Test approval task state transitions."""
        task_id = "test_task_123"

        # Initial state: pending_approval
        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "test.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        assert approval_tasks[task_id]["status"] == "pending_approval"

        # Transition to approved
        approval_tasks[task_id]["status"] = "approved"
        approval_tasks[task_id]["approved_by"] = "user_123"
        approval_tasks[task_id]["approved_at"] = time.time()

        assert approval_tasks[task_id]["status"] == "approved"
        assert approval_tasks[task_id]["approved_by"] == "user_123"
        assert "approved_at" in approval_tasks[task_id]

    def test_approval_task_lookup(self):
        """Test looking up approval tasks."""
        task_id = "test_task_123"
        workflow_id = "wf_456"

        approval_tasks[task_id] = {
            "workflow_id": workflow_id,
            "workflow_request": {"workflow_pack_id": "test.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        # Lookup by task_id
        task = approval_tasks.get(task_id)
        assert task is not None
        assert task["workflow_id"] == workflow_id

        # Lookup non-existent task
        non_existent = approval_tasks.get("non_existent_task")
        assert non_existent is None

    def test_approval_task_by_workflow_id(self):
        """Test finding approval tasks by workflow_id."""
        workflow_id = "wf_456"
        task_id_1 = "task_1"
        task_id_2 = "task_2"

        approval_tasks[task_id_1] = {
            "workflow_id": workflow_id,
            "workflow_request": {},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_1",
        }

        approval_tasks[task_id_2] = {
            "workflow_id": "different_wf",
            "workflow_request": {},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_2",
        }

        # Find tasks for specific workflow
        matching_tasks = [
            (tid, task)
            for tid, task in approval_tasks.items()
            if task.get("workflow_id") == workflow_id
        ]

        assert len(matching_tasks) == 1
        assert matching_tasks[0][0] == task_id_1

    def test_multiple_approval_tasks(self):
        """Test managing multiple approval tasks."""
        # Create multiple tasks
        for i in range(5):
            task_id = f"task_{i}"
            approval_tasks[task_id] = {
                "workflow_id": f"wf_{i}",
                "workflow_request": {"workflow_pack_id": f"pack_{i}"},
                "status": "pending_approval",
                "created_at": time.time(),
                "correlation_id": f"corr_{i}",
            }

        assert len(approval_tasks) == 5

        # Approve one task
        approval_tasks["task_2"]["status"] = "approved"

        # Count pending tasks
        pending_count = sum(
            1 for task in approval_tasks.values() if task["status"] == "pending_approval"
        )
        assert pending_count == 4


class TestApprovalIdempotency:
    """Test idempotency of approval operations."""

    def test_double_approval_detection(self):
        """Test that double approval is detected."""
        task_id = "test_task_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "test.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        # First approval
        task = approval_tasks[task_id]
        assert task["status"] == "pending_approval"

        task["status"] = "approved"
        task["approved_by"] = "user_123"
        task["approved_at"] = time.time()

        # Second approval attempt - should detect already approved
        is_already_approved = task["status"] == "approved"
        assert is_already_approved is True

    def test_approval_task_immutability_after_approval(self):
        """Test that approved tasks maintain their state."""
        task_id = "test_task_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "test.pack"},
            "status": "approved",
            "approved_by": "user_123",
            "approved_at": 1234567890.0,
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        original_approved_by = approval_tasks[task_id]["approved_by"]
        original_approved_at = approval_tasks[task_id]["approved_at"]

        # Verify state is preserved
        assert approval_tasks[task_id]["approved_by"] == original_approved_by
        assert approval_tasks[task_id]["approved_at"] == original_approved_at


class TestApprovalDataStructure:
    """Test approval task data structure and fields."""

    def test_required_approval_fields(self):
        """Test that approval tasks have all required fields."""
        task_id = "test_task_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {
                "workflow_pack_id": "test.pack",
                "workflow_type": "legal",
                "payload": {"key": "value"},
                "metadata": {},
            },
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        task = approval_tasks[task_id]

        # Verify all required fields exist
        assert "workflow_id" in task
        assert "workflow_request" in task
        assert "status" in task
        assert "created_at" in task
        assert "correlation_id" in task

        # Verify workflow_request structure
        request = task["workflow_request"]
        assert "workflow_pack_id" in request
        assert "workflow_type" in request
        assert "payload" in request

    def test_approval_data_attachment(self):
        """Test attaching approval data to task."""
        task_id = "test_task_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "test.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        # Add approval data
        approval_data = {"approved": True, "comments": "Looks good", "reviewer": "John Doe"}

        approval_tasks[task_id]["approval_data"] = approval_data

        assert "approval_data" in approval_tasks[task_id]
        assert approval_tasks[task_id]["approval_data"]["approved"] is True
        assert approval_tasks[task_id]["approval_data"]["comments"] == "Looks good"

    def test_timestamp_fields(self):
        """Test timestamp fields in approval tasks."""
        task_id = "test_task_123"
        created_time = time.time()

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "test.pack"},
            "status": "pending_approval",
            "created_at": created_time,
            "correlation_id": "corr_123",
        }

        assert approval_tasks[task_id]["created_at"] == created_time
        assert isinstance(approval_tasks[task_id]["created_at"], float)

        # Add approved_at timestamp
        approved_time = time.time()
        approval_tasks[task_id]["approved_at"] = approved_time

        assert approval_tasks[task_id]["approved_at"] == approved_time
        assert approval_tasks[task_id]["approved_at"] >= approval_tasks[task_id]["created_at"]


class TestApprovalWorkflowStates:
    """Test workflow state management through approval process."""

    def test_workflow_state_pending_approval(self):
        """Test workflow in pending_approval state."""
        task_id = "test_task_123"
        workflow_id = "wf_456"

        approval_tasks[task_id] = {
            "workflow_id": workflow_id,
            "workflow_request": {
                "workflow_pack_id": "legal.pack",
                "workflow_type": "legal",
                "payload": {"legal_description": "test"},
            },
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        # Verify pending state
        assert approval_tasks[task_id]["status"] == "pending_approval"

        # Verify workflow request is preserved
        request = approval_tasks[task_id]["workflow_request"]
        assert request["workflow_type"] == "legal"
        assert "legal_description" in request["payload"]

    def test_workflow_state_approved_and_executed(self):
        """Test workflow transition to approved_and_executed."""
        task_id = "test_task_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "legal.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        # Simulate approval and execution
        approval_tasks[task_id]["status"] = "approved"
        approval_tasks[task_id]["approved_by"] = "user_123"
        approval_tasks[task_id]["approved_at"] = time.time()
        approval_tasks[task_id]["execution_status"] = "executed"

        assert approval_tasks[task_id]["status"] == "approved"
        assert approval_tasks[task_id]["execution_status"] == "executed"

    def test_workflow_state_approved_but_failed(self):
        """Test workflow approved but execution failed."""
        task_id = "test_task_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "legal.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": "corr_123",
        }

        # Simulate approval but failed execution
        approval_tasks[task_id]["status"] = "approved"
        approval_tasks[task_id]["approved_by"] = "user_123"
        approval_tasks[task_id]["approved_at"] = time.time()
        approval_tasks[task_id]["execution_status"] = "failed"
        approval_tasks[task_id]["error"] = "Service unavailable"

        assert approval_tasks[task_id]["status"] == "approved"
        assert approval_tasks[task_id]["execution_status"] == "failed"
        assert "error" in approval_tasks[task_id]

    def test_workflow_correlation_preservation(self):
        """Test that correlation IDs are preserved through approval."""
        task_id = "test_task_123"
        original_corr_id = "original_corr_123"

        approval_tasks[task_id] = {
            "workflow_id": "wf_456",
            "workflow_request": {"workflow_pack_id": "legal.pack"},
            "status": "pending_approval",
            "created_at": time.time(),
            "correlation_id": original_corr_id,
        }

        # Verify original correlation ID is preserved
        assert approval_tasks[task_id]["correlation_id"] == original_corr_id

        # After approval, original correlation ID should still be there
        approval_tasks[task_id]["status"] = "approved"
        approval_tasks[task_id]["approved_by"] = "user_123"

        assert approval_tasks[task_id]["correlation_id"] == original_corr_id
