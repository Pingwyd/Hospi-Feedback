from app.core.ticket_code import (
    TICKET_CODE_LENGTH,
    generate_ticket_code,
    hash_ticket_code,
    is_valid_ticket_code_format,
    ticket_code_matches_hash,
)


def test_generate_ticket_code_length_and_alphabet() -> None:
    code = generate_ticket_code()
    assert len(code) == TICKET_CODE_LENGTH
    assert is_valid_ticket_code_format(code)


def test_is_valid_ticket_code_format_rejects_bad_shapes() -> None:
    assert not is_valid_ticket_code_format("")
    assert not is_valid_ticket_code_format("SHORT")
    assert not is_valid_ticket_code_format("AAAAAAAO")
    assert not is_valid_ticket_code_format("abcd2345")


def test_hash_and_compare_digest() -> None:
    code = generate_ticket_code()
    digest = hash_ticket_code(code)
    assert len(digest) == 64
    assert ticket_code_matches_hash(code, digest)
    assert not ticket_code_matches_hash(generate_ticket_code(), digest)
