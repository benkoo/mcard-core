"""Tests for MCard exceptions and invalid operations."""
import pytest
from mcard.domain.models.card import MCard


def test_mcard_extra_fields():
    """Test that extra fields are not allowed in MCard."""
    with pytest.raises(TypeError):
        MCard(content="extra", extra_field="not allowed")
