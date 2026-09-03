from app.core.recusal import RecusalAdmin, RecusalReport, check_recusal

ADMIN_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ADMIN_ID = "22222222-2222-2222-2222-222222222222"


def test_check_recusal_blocked_when_linked_to_same_admin() -> None:
    admin = RecusalAdmin(
        id=ADMIN_ID,
        full_name="Ada Okonkwo",
        aliases=("Ada",),
    )
    report = RecusalReport(
        reported_member_name="Ada Okonkwo",
        reported_member_admin_id=ADMIN_ID,
    )
    assert check_recusal(admin, report) == "blocked"


def test_check_recusal_warns_on_unlinked_fuzzy_name_match() -> None:
    admin = RecusalAdmin(
        id=ADMIN_ID,
        full_name="Ada Okonkwo",
        aliases=("Ada",),
    )
    report = RecusalReport(
        reported_member_name="Complaint about ada during hall meeting",
        reported_member_admin_id=None,
    )
    assert check_recusal(admin, report) == "warn"


def test_check_recusal_clear_when_unrelated() -> None:
    admin = RecusalAdmin(
        id=ADMIN_ID,
        full_name="Ada Okonkwo",
        aliases=("Ada",),
    )
    report = RecusalReport(
        reported_member_name="Someone else entirely",
        reported_member_admin_id=OTHER_ADMIN_ID,
    )
    assert check_recusal(admin, report) == "clear"
