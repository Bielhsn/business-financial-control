from app.domain.blueprint.module_registry import MODULE_IDS, MODULE_REGISTRY, get_module


def test_module_ids_matches_registry_entries() -> None:
    assert {module.id for module in MODULE_REGISTRY} == MODULE_IDS


def test_get_module_returns_definition_for_known_id() -> None:
    module = get_module("financial_core")

    assert module is not None
    assert module.name == "Financeiro"


def test_get_module_returns_none_for_unknown_id() -> None:
    assert get_module("does-not-exist") is None
