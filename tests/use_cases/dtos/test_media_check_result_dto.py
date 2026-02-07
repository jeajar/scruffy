"""Tests for MediaCheckResultDTO and RetentionResultDTO."""

import dataclasses

import pytest

from scruffy.use_cases.dtos.media_check_result_dto import (
    MediaCheckResultDTO,
    RetentionResultDTO,
)


def test_retention_result_dto_creation():
    """Test RetentionResultDTO can be created."""
    dto = RetentionResultDTO(remind=True, delete=False, days_left=7)

    assert dto.remind is True
    assert dto.delete is False
    assert dto.days_left == 7


def test_retention_result_dto_is_immutable():
    """Test RetentionResultDTO is immutable (frozen dataclass)."""
    dto = RetentionResultDTO(remind=True, delete=False, days_left=7)

    with pytest.raises(dataclasses.FrozenInstanceError):
        dto.remind = False  # ty: ignore[invalid-assignment]


def test_retention_result_dto_default_days_left():
    """Test RetentionResultDTO defaults days_left to 0."""
    dto = RetentionResultDTO(remind=True, delete=False)

    assert dto.days_left == 0


def test_media_check_result_dto_creation(sample_request_dto_movie, sample_media_info_dto):
    """Test MediaCheckResultDTO can be created."""
    retention = RetentionResultDTO(remind=True, delete=False, days_left=7)
    result = MediaCheckResultDTO(
        request=sample_request_dto_movie,
        media=sample_media_info_dto,
        retention=retention,
    )

    assert result.request == sample_request_dto_movie
    assert result.media == sample_media_info_dto
    assert result.retention == retention


def test_media_check_result_dto_is_immutable(sample_request_dto_movie, sample_media_info_dto):
    """Test MediaCheckResultDTO is immutable (frozen dataclass)."""
    retention = RetentionResultDTO(remind=True, delete=False, days_left=7)
    result = MediaCheckResultDTO(
        request=sample_request_dto_movie,
        media=sample_media_info_dto,
        retention=retention,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.retention = RetentionResultDTO(remind=False, delete=True)  # ty: ignore[invalid-assignment]


def test_media_check_result_dto_with_delete_retention(sample_request_dto_movie, sample_media_info_dto):
    """Test MediaCheckResultDTO with delete retention."""
    retention = RetentionResultDTO(remind=True, delete=True, days_left=-5)
    result = MediaCheckResultDTO(
        request=sample_request_dto_movie,
        media=sample_media_info_dto,
        retention=retention,
    )

    assert result.retention.delete is True
    assert result.retention.days_left == -5
