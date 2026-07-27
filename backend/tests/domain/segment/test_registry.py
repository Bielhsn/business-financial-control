from app.domain.blueprint.integration_registry import INTEGRATION_REGISTRY
from app.domain.blueprint.module_registry import MODULE_IDS
from app.domain.dashboard.kpi_registry import KPI_METRIC_IDS
from app.domain.segment.profile import Capability
from app.domain.segment.registry import (
    GENERIC_PROFILE,
    SEGMENT_PROFILES,
    get_profile_by_id,
    resolve_segment_profile,
)

_INTEGRATION_IDS = frozenset(item.id for item in INTEGRATION_REGISTRY)
_ALL_PROFILES = (*SEGMENT_PROFILES, GENERIC_PROFILE)


class TestProfileIntegrity:
    """Um perfil só pode referenciar módulos, KPIs e integrações que existem —
    é o que impede a arquitetura por metadados de apontar para o vazio."""

    def test_modules_exist_in_registry(self) -> None:
        for profile in _ALL_PROFILES:
            unknown = set(profile.modules) - MODULE_IDS
            assert not unknown, f"{profile.id} referencia módulos inexistentes: {unknown}"

    def test_kpis_exist_in_registry(self) -> None:
        for profile in _ALL_PROFILES:
            unknown = {metric.value for metric in profile.kpis} - KPI_METRIC_IDS
            assert not unknown, f"{profile.id} referencia KPIs inexistentes: {unknown}"

    def test_integrations_exist_in_registry(self) -> None:
        for profile in _ALL_PROFILES:
            unknown = set(profile.integrations) - _INTEGRATION_IDS
            assert not unknown, f"{profile.id} referencia integrações inexistentes: {unknown}"

    def test_ids_are_unique(self) -> None:
        ids = [profile.id for profile in _ALL_PROFILES]
        assert len(ids) == len(set(ids))

    def test_every_profile_seeds_financial_categories(self) -> None:
        for profile in _ALL_PROFILES:
            assert profile.income_categories, f"{profile.id} sem categorias de receita"
            assert profile.expense_categories, f"{profile.id} sem categorias de despesa"

    def test_service_segments_do_not_ask_for_stock_fields(self) -> None:
        # Uma clínica não deve pedir SKU/código de barras para um exame.
        clinic = get_profile_by_id("health_clinic")
        assert clinic is not None
        assert clinic.catalog_fields.sku is False
        assert clinic.catalog_fields.barcode is False
        assert clinic.catalog_fields.inventory is False


class TestResolveSegmentProfile:
    def test_barbershop_from_free_text(self) -> None:
        assert resolve_segment_profile("Barbearia").id == "barbershop"
        assert resolve_segment_profile("SALÃO de beleza").id == "barbershop"

    def test_lab_resolves_to_health(self) -> None:
        profile = resolve_segment_profile("Laboratório de imunologia e hematologia")
        assert profile.id == "health_clinic"
        assert profile.terminology.clients == "Pacientes"

    def test_beverage_store_is_product_oriented(self) -> None:
        profile = resolve_segment_profile("Loja de bebidas")
        assert profile.id == "beverage_store"
        assert profile.sells_products is True
        assert profile.sells_services is False
        assert "appointments" not in profile.modules

    def test_subsegment_wins_over_generic_segment(self) -> None:
        # "Saúde" já casaria com clínica, mas o subsegmento é quem manda quando
        # o segmento é amplo — ex.: "Comércio" + "Loja de bebidas".
        profile = resolve_segment_profile("Comércio", "Loja de bebidas")
        assert profile.id == "beverage_store"

    def test_unknown_segment_falls_back_to_generic(self) -> None:
        profile = resolve_segment_profile("Algo totalmente novo")
        assert profile.id == GENERIC_PROFILE.id
        assert profile.income_categories  # continua utilizável

    def test_empty_segment_falls_back_to_generic(self) -> None:
        assert resolve_segment_profile(None).id == GENERIC_PROFILE.id
        assert resolve_segment_profile("").id == GENERIC_PROFILE.id

    def test_get_profile_by_id(self) -> None:
        assert get_profile_by_id("restaurant") is not None
        assert get_profile_by_id("generic") is GENERIC_PROFILE
        assert get_profile_by_id("nao-existe") is None


class TestCapabilities:
    """Capacidade responde "que recurso do produto faz sentido aqui" — é o que
    impede a aba de reconvite por WhatsApp aparecer numa loja de bebidas."""

    def test_retention_only_where_recurrence_matters(self) -> None:
        assert resolve_segment_profile("Barbearia").has(Capability.CLIENT_RETENTION)
        assert resolve_segment_profile("Clínica").has(Capability.CLIENT_RETENTION)
        # Delivery de bebidas vive de canal de venda, não de reconvite individual.
        assert not resolve_segment_profile("Loja de bebidas").has(Capability.CLIENT_RETENTION)
        assert not resolve_segment_profile("Loja de roupas").has(Capability.CLIENT_RETENTION)

    def test_inventory_only_for_who_holds_stock(self) -> None:
        assert resolve_segment_profile("Loja de bebidas").has(Capability.INVENTORY)
        assert not resolve_segment_profile("Clínica").has(Capability.INVENTORY)

    def test_sales_channels_only_for_multichannel_retail(self) -> None:
        assert resolve_segment_profile("Loja de bebidas").has(Capability.SALES_CHANNELS)
        assert not resolve_segment_profile("Barbearia").has(Capability.SALES_CHANNELS)

    def test_generic_profile_claims_no_capability(self) -> None:
        # Sem saber o negócio, não inventa recurso — melhor neutro que errado.
        assert resolve_segment_profile("Algo novo").capabilities == frozenset()


class TestSpecificSegmentsWinOverBroadOnes:
    """A ordem do catálogo é regra de negócio: o perfil mais específico precisa
    casar antes do mais amplo, senão "agência de viagens" cai em consultoria."""

    def test_travel_agency_beats_professional_services(self) -> None:
        assert resolve_segment_profile("Agência de viagens").id == "travel_agency"
        # E o caso amplo continua indo para consultoria.
        assert resolve_segment_profile("Agência de marketing digital").id == "professional_services"

    def test_online_course_beats_marketing_keyword(self) -> None:
        assert resolve_segment_profile("Curso online de marketing").id == "online_education"

    def test_infoproduct_segment_recommends_infoproduct_platforms(self) -> None:
        profile = resolve_segment_profile("Infoprodutos")
        assert "hotmart" in profile.integrations
        # Nada de delivery para quem vende curso.
        assert "ifood" not in profile.integrations
