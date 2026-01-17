"""Tests for RequestStatus value object."""

from scruffy.domain.value_objects.request_status import RequestStatus


def test_request_status_enum_values():
    """Test RequestStatus enum has expected values."""
    assert RequestStatus.PENDING_APPROVAL.value == 1
    assert RequestStatus.APPROVED.value == 2
    assert RequestStatus.DECLINED.value == 3


def test_request_status_enum_names():
    """Test RequestStatus enum has expected names."""
    assert RequestStatus.PENDING_APPROVAL.name == "PENDING_APPROVAL"
    assert RequestStatus.APPROVED.name == "APPROVED"
    assert RequestStatus.DECLINED.name == "DECLINED"
