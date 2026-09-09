"""Tests for delete-message ownership tracking."""

from bot.delete_targets import owns_delete_target, register_delete_target


def test_register_and_validate_delete_target() -> None:
    user_data: dict = {}
    register_delete_target(user_data, chat_id=100, message_id=42)
    assert owns_delete_target(user_data, chat_id=100, message_id=42)
    assert not owns_delete_target(user_data, chat_id=101, message_id=42)
    assert not owns_delete_target(user_data, chat_id=100, message_id=43)
