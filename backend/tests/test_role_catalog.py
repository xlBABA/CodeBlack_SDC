from app.services.role_catalog import FixtureRoleCatalog


def test_catalog_returns_four_verified_fixture_roles():
    roles = FixtureRoleCatalog().list_roles()
    assert len(roles) == 4
    assert all(role.verified for role in roles)


def test_role_ids_are_unique():
    roles = FixtureRoleCatalog().list_roles()
    role_ids = [role.role_id for role in roles]
    assert len(role_ids) == len(set(role_ids))
