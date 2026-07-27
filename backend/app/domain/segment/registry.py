"""Catálogo de perfis de segmento.

Determinístico e fechado: o texto livre do cadastro ("Barbearia", "Loja de
bebidas", "Clínica de imunologia") é normalizado e casado contra os radicais de
cada perfil. Sem correspondência, cai no perfil genérico — nunca em erro.

A IA continua podendo enriquecer o blueprint (categorias e campos extras), mas a
espinha dorsal da experiência sai daqui, então uma empresa nunca fica com um
painel genérico só porque a chave de IA não está configurada.
"""

import unicodedata

from app.domain.dashboard.kpi_registry import KPIMetric
from app.domain.segment.profile import (
    Capability,
    CatalogFieldPolicy,
    OfferingModel,
    SegmentProfile,
    SegmentTerminology,
)

# Varejo usa a ficha completa (SKU, código de barras, marca, fornecedor, estoque).
_RETAIL_FIELDS = CatalogFieldPolicy()

# KPIs mais usados, por tipo de operação.
_SERVICE_KPIS = (
    KPIMetric.TOTAL_REVENUE,
    KPIMetric.TRANSACTION_COUNT,
    KPIMetric.AVERAGE_TICKET,
    KPIMetric.ACTIVE_CLIENTS,
    KPIMetric.PROFIT,
)
_RETAIL_KPIS = (
    KPIMetric.TOTAL_REVENUE,
    KPIMetric.PROFIT,
    KPIMetric.PROFIT_MARGIN,
    KPIMetric.AVERAGE_TICKET,
    KPIMetric.TRANSACTION_COUNT,
)

SEGMENT_PROFILES: tuple[SegmentProfile, ...] = (
    SegmentProfile(
        id="barbershop",
        label="Barbearia e salão",
        keywords=(
            "barbear",
            "barber",
            "cabelele",
            "cabeleire",
            "salao de beleza",
            "salao",
            "beleza",
            "estetic",
            "manicure",
            "pedicure",
            "unha",
            "sobrancelha",
            "depilac",
            "maquiag",
            "spa",
        ),
        offering=OfferingModel.BOTH,
        modules=("clients", "services", "products", "employees", "appointments"),
        terminology=SegmentTerminology(
            catalog="Serviços & Produtos",
            employees="Profissionais",
            employee_singular="profissional",
            agenda="Agenda",
            transactions="Atendimentos",
        ),
        catalog_fields=CatalogFieldPolicy(
            sku=False,
            barcode=True,
            brand=True,
            supplier=True,
            variants=False,
            inventory=True,
            duration=True,
        ),
        service_examples=(
            "Corte de cabelo",
            "Barba",
            "Corte + Barba",
            "Sobrancelha",
            "Luzes",
            "Pintura",
            "Hidratação",
        ),
        product_examples=("Pomada modeladora", "Shampoo", "Óleo para barba", "Minoxidil"),
        catalog_categories=("Cortes", "Barba", "Coloração", "Tratamentos", "Cosméticos"),
        income_categories=("Serviços", "Venda de produtos", "Pacotes e planos"),
        expense_categories=(
            "Comissões",
            "Produtos e insumos",
            "Aluguel",
            "Energia e água",
            "Salários",
            "Marketing",
        ),
        kpis=_SERVICE_KPIS,
        integrations=("google_agenda", "whatsapp"),
        capabilities=frozenset(
            {
                Capability.CLIENT_RETENTION,
                Capability.COMMISSIONS,
                Capability.SCHEDULE_ANALYTICS,
                Capability.INVENTORY,
                Capability.PRODUCT_MARGIN,
            }
        ),
    ),
    SegmentProfile(
        id="health_clinic",
        label="Clínica, consultório e laboratório",
        keywords=(
            "clinic",
            "laborator",
            "imuno",
            "hemato",
            "medic",
            "saude",
            "odonto",
            "dentist",
            "fisioter",
            "psicolog",
            "psiquiatr",
            "nutric",
            "veterinar",
            "exame",
            "diagnostic",
            "consultorio",
            "fonoaudio",
        ),
        offering=OfferingModel.SERVICES,
        modules=("clients", "services", "employees", "appointments"),
        terminology=SegmentTerminology(
            clients="Pacientes",
            client_singular="paciente",
            catalog="Procedimentos & Exames",
            services="Procedimentos",
            employees="Profissionais",
            employee_singular="profissional",
            agenda="Consultas",
            appointment_singular="consulta",
            transactions="Atendimentos",
        ),
        catalog_fields=CatalogFieldPolicy(
            sku=False,
            barcode=False,
            brand=False,
            supplier=False,
            variants=False,
            inventory=False,
            duration=True,
        ),
        service_examples=(
            "Consulta",
            "Retorno",
            "Hemograma completo",
            "Sorologia",
            "Imunofenotipagem",
            "Coleta domiciliar",
        ),
        catalog_categories=("Consultas", "Exames laboratoriais", "Procedimentos", "Retornos"),
        income_categories=("Consultas", "Exames", "Procedimentos", "Convênios", "Particular"),
        expense_categories=(
            "Honorários profissionais",
            "Insumos e reagentes",
            "Aluguel",
            "Equipamentos e manutenção",
            "Salários",
            "Licenças e taxas",
        ),
        kpis=_SERVICE_KPIS,
        integrations=("google_agenda", "whatsapp"),
        capabilities=frozenset(
            {
                Capability.CLIENT_RETENTION,
                Capability.SCHEDULE_ANALYTICS,
                Capability.RECURRING_REVENUE,
            }
        ),
    ),
    SegmentProfile(
        id="beverage_store",
        label="Loja de bebidas e adega",
        keywords=(
            "bebida",
            "adega",
            "distribuidora de bebida",
            "cervej",
            "vinho",
            "destilado",
            "conveniencia",
            "tabacar",
        ),
        offering=OfferingModel.PRODUCTS,
        modules=("clients", "products", "inventory"),
        terminology=SegmentTerminology(
            catalog="Produtos", employees="Equipe", transactions="Vendas"
        ),
        catalog_fields=_RETAIL_FIELDS,
        product_examples=(
            "Cerveja long neck",
            "Vinho tinto seco",
            "Whisky 1L",
            "Energético lata",
            "Água mineral 500ml",
        ),
        catalog_categories=(
            "Cervejas",
            "Vinhos",
            "Destilados",
            "Refrigerantes",
            "Energéticos",
            "Águas",
            "Gelo e descartáveis",
        ),
        income_categories=("Vendas no balcão", "Delivery", "Vendas por aplicativo"),
        expense_categories=(
            "Compra de mercadorias",
            "Fornecedores",
            "Aluguel",
            "Energia (refrigeração)",
            "Salários",
            "Taxas de aplicativos",
        ),
        kpis=_RETAIL_KPIS,
        integrations=("ifood", "rappi", "mercado_livre"),
        capabilities=frozenset(
            {Capability.INVENTORY, Capability.SALES_CHANNELS, Capability.PRODUCT_MARGIN}
        ),
    ),
    SegmentProfile(
        id="restaurant",
        label="Restaurante e food service",
        keywords=(
            "restaurant",
            "lanchon",
            "pizzar",
            "hamburg",
            "hambur",
            "cafeter",
            "padaria",
            "confeitar",
            "acai",
            "sorveter",
            "food",
            "gastro",
            "marmit",
            "bar e ",
            "pub",
        ),
        offering=OfferingModel.PRODUCTS,
        modules=("clients", "products", "inventory", "employees"),
        terminology=SegmentTerminology(
            catalog="Cardápio",
            products="Itens do cardápio",
            employees="Equipe",
            transactions="Pedidos",
        ),
        catalog_fields=CatalogFieldPolicy(
            sku=False, barcode=False, brand=False, supplier=True, variants=True, inventory=True
        ),
        product_examples=("X-Salada", "Pizza calabresa", "Refrigerante lata", "Marmita executiva"),
        catalog_categories=("Entradas", "Pratos principais", "Lanches", "Bebidas", "Sobremesas"),
        income_categories=("Salão", "Delivery", "Balcão", "Aplicativos"),
        expense_categories=(
            "Insumos e ingredientes",
            "Fornecedores",
            "Aluguel",
            "Gás e energia",
            "Salários",
            "Taxas de aplicativos",
            "Embalagens",
        ),
        kpis=_RETAIL_KPIS,
        integrations=("ifood", "rappi", "uber_eats", "anota_ai"),
        capabilities=frozenset(
            {Capability.INVENTORY, Capability.SALES_CHANNELS, Capability.PRODUCT_MARGIN}
        ),
    ),
    SegmentProfile(
        id="fashion_retail",
        label="Loja de roupas e calçados",
        keywords=(
            "roupa",
            "vestuar",
            "moda",
            "boutique",
            "calcad",
            "sapat",
            "confecc",
            "loja de roupas",
            "brecho",
        ),
        offering=OfferingModel.PRODUCTS,
        modules=("clients", "products", "inventory"),
        terminology=SegmentTerminology(
            catalog="Produtos", employees="Equipe", transactions="Vendas"
        ),
        catalog_fields=_RETAIL_FIELDS,
        product_examples=("Camiseta básica", "Calça jeans", "Vestido midi", "Tênis casual"),
        catalog_categories=("Camisetas", "Calças", "Vestidos", "Calçados", "Acessórios"),
        income_categories=("Vendas na loja", "Vendas online", "Marketplaces"),
        expense_categories=(
            "Compra de mercadorias",
            "Fornecedores",
            "Aluguel",
            "Salários",
            "Marketing",
            "Frete e logística",
        ),
        kpis=_RETAIL_KPIS,
        integrations=("shopify", "nuvemshop", "mercado_livre", "shopee"),
        capabilities=frozenset(
            {Capability.INVENTORY, Capability.SALES_CHANNELS, Capability.PRODUCT_MARGIN}
        ),
    ),
    SegmentProfile(
        id="gym",
        label="Academia e estúdio",
        keywords=(
            "academia",
            "fitness",
            "crossfit",
            "pilates",
            "yoga",
            "musculac",
            "personal train",
            "estudio de danca",
            "danca",
            "luta",
            "natac",
        ),
        offering=OfferingModel.SERVICES,
        modules=("clients", "services", "employees", "appointments"),
        terminology=SegmentTerminology(
            clients="Alunos",
            client_singular="aluno",
            catalog="Planos & Aulas",
            services="Planos e aulas",
            employees="Instrutores",
            employee_singular="instrutor",
            agenda="Aulas",
            appointment_singular="aula",
            transactions="Check-ins",
        ),
        catalog_fields=CatalogFieldPolicy(
            sku=False,
            barcode=False,
            brand=False,
            supplier=False,
            variants=False,
            inventory=False,
            duration=True,
        ),
        service_examples=("Plano mensal", "Plano trimestral", "Aula avulsa", "Personal"),
        catalog_categories=("Planos", "Aulas coletivas", "Personal", "Avaliações"),
        income_categories=("Mensalidades", "Aulas avulsas", "Personal", "Venda de produtos"),
        expense_categories=(
            "Salários e instrutores",
            "Aluguel",
            "Equipamentos e manutenção",
            "Energia e água",
            "Marketing",
        ),
        kpis=_SERVICE_KPIS,
        integrations=("google_agenda", "whatsapp"),
        capabilities=frozenset(
            {
                Capability.CLIENT_RETENTION,
                Capability.SCHEDULE_ANALYTICS,
                Capability.RECURRING_REVENUE,
            }
        ),
    ),
    SegmentProfile(
        id="auto_shop",
        label="Oficina e serviços automotivos",
        keywords=(
            "oficina",
            "mecanic",
            "automotiv",
            "auto center",
            "funilar",
            "borrachar",
            "lava rapido",
            "lava-rapido",
            "estetica automotiv",
        ),
        offering=OfferingModel.BOTH,
        modules=("clients", "services", "products", "inventory", "employees", "appointments"),
        terminology=SegmentTerminology(
            catalog="Serviços & Peças",
            products="Peças",
            employees="Mecânicos",
            employee_singular="mecânico",
            agenda="Ordens de serviço",
            appointment_singular="ordem de serviço",
            transactions="Ordens de serviço",
        ),
        catalog_fields=CatalogFieldPolicy(
            sku=True,
            barcode=True,
            brand=True,
            supplier=True,
            variants=False,
            inventory=True,
            duration=True,
        ),
        service_examples=("Troca de óleo", "Alinhamento", "Revisão completa", "Troca de pastilhas"),
        product_examples=("Óleo 5W30", "Filtro de ar", "Pastilha de freio", "Bateria"),
        catalog_categories=("Serviços", "Peças", "Lubrificantes", "Pneus"),
        income_categories=("Mão de obra", "Venda de peças", "Serviços rápidos"),
        expense_categories=(
            "Compra de peças",
            "Fornecedores",
            "Aluguel",
            "Ferramentas e equipamentos",
            "Salários",
        ),
        kpis=_SERVICE_KPIS,
        integrations=("whatsapp",),
        capabilities=frozenset(
            {
                Capability.CLIENT_RETENTION,
                Capability.COMMISSIONS,
                Capability.SCHEDULE_ANALYTICS,
                Capability.INVENTORY,
                Capability.PRODUCT_MARGIN,
            }
        ),
    ),
    SegmentProfile(
        id="professional_services",
        label="Serviços profissionais e consultorias",
        keywords=(
            "consultor",
            "advocacia",
            "advogad",
            "juridic",
            "contabil",
            "assessoria",
            "agencia",
            "marketing",
            "arquitet",
            "engenhar",
            "design",
            "software",
            "tecnologia",
            "desenvolviment",
        ),
        offering=OfferingModel.SERVICES,
        modules=("clients", "services", "employees", "contracts"),
        terminology=SegmentTerminology(
            catalog="Serviços",
            employees="Equipe",
            employee_singular="membro da equipe",
            agenda="Compromissos",
            appointment_singular="compromisso",
            transactions="Serviços prestados",
        ),
        catalog_fields=CatalogFieldPolicy(
            sku=False,
            barcode=False,
            brand=False,
            supplier=False,
            variants=False,
            inventory=False,
            duration=True,
        ),
        service_examples=("Consultoria mensal", "Projeto pontual", "Hora técnica", "Assessoria"),
        catalog_categories=("Consultoria", "Projetos", "Retainer", "Treinamentos"),
        income_categories=("Honorários", "Projetos", "Contratos recorrentes"),
        expense_categories=(
            "Salários e pró-labore",
            "Ferramentas e assinaturas",
            "Aluguel",
            "Impostos",
            "Marketing",
        ),
        kpis=_SERVICE_KPIS,
        integrations=("whatsapp",),
        capabilities=frozenset({Capability.CLIENT_RETENTION, Capability.RECURRING_REVENUE}),
    ),
    SegmentProfile(
        id="ecommerce",
        label="E-commerce e marketplaces",
        keywords=("e-commerce", "ecommerce", "loja virtual", "marketplace", "dropship"),
        offering=OfferingModel.PRODUCTS,
        modules=("clients", "products", "inventory"),
        terminology=SegmentTerminology(
            catalog="Produtos", employees="Equipe", transactions="Pedidos"
        ),
        catalog_fields=_RETAIL_FIELDS,
        product_examples=("Produto principal", "Kit promocional"),
        catalog_categories=("Mais vendidos", "Lançamentos", "Promoções"),
        income_categories=("Vendas na loja virtual", "Marketplaces", "Social commerce"),
        expense_categories=(
            "Compra de mercadorias",
            "Taxas de marketplace",
            "Frete e logística",
            "Marketing e anúncios",
            "Embalagens",
        ),
        kpis=_RETAIL_KPIS,
        integrations=("shopify", "nuvemshop", "mercado_livre", "shopee", "melhor_envio"),
        capabilities=frozenset(
            {Capability.INVENTORY, Capability.SALES_CHANNELS, Capability.PRODUCT_MARGIN}
        ),
    ),
    SegmentProfile(
        id="general_retail",
        label="Comércio e varejo",
        keywords=(
            "loja",
            "varejo",
            "comercio",
            "mercad",
            "mercear",
            "supermercad",
            "papelaria",
            "petshop",
            "pet shop",
            "farmacia",
            "drogaria",
            "otica",
            "distribuidora",
            "materiais de construc",
        ),
        offering=OfferingModel.PRODUCTS,
        modules=("clients", "products", "inventory"),
        terminology=SegmentTerminology(
            catalog="Produtos", employees="Equipe", transactions="Vendas"
        ),
        catalog_fields=_RETAIL_FIELDS,
        product_examples=("Produto de maior giro", "Item promocional"),
        catalog_categories=("Geral", "Promoções", "Mais vendidos"),
        income_categories=("Vendas", "Delivery"),
        expense_categories=(
            "Compra de mercadorias",
            "Fornecedores",
            "Aluguel",
            "Energia",
            "Salários",
        ),
        kpis=_RETAIL_KPIS,
        integrations=("mercado_livre", "shopee"),
        capabilities=frozenset({Capability.INVENTORY, Capability.PRODUCT_MARGIN}),
    ),
)

# Perfil neutro: usado quando o texto do segmento não casa com nenhum radical.
# Mantém a experiência funcional (não trava o produto) sem fingir especialização.
GENERIC_PROFILE = SegmentProfile(
    id="generic",
    label="Negócio",
    keywords=(),
    offering=OfferingModel.BOTH,
    modules=("clients", "services", "products", "employees"),
    catalog_categories=("Geral",),
    income_categories=("Vendas", "Serviços"),
    expense_categories=("Fornecedores", "Aluguel", "Salários", "Impostos", "Marketing"),
    kpis=(
        KPIMetric.TOTAL_REVENUE,
        KPIMetric.TOTAL_EXPENSES,
        KPIMetric.PROFIT,
        KPIMetric.ACTIVE_CLIENTS,
    ),
)


def normalize(text: str) -> str:
    """Minúsculas e sem acento — o segmento é digitado livremente pelo dono."""
    decomposed = unicodedata.normalize("NFD", text)
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return without_marks.lower().strip()


def resolve_segment_profile(segment: str | None, subsegment: str | None = None) -> SegmentProfile:
    """Resolve o perfil a partir do texto livre do cadastro.

    O subsegmento tem prioridade quando presente por ser mais específico
    (ex.: segmento "Saúde" + subsegmento "Laboratório de análises clínicas").
    """
    for text in (subsegment, segment):
        if not text:
            continue
        normalized = normalize(text)
        for profile in SEGMENT_PROFILES:
            if any(keyword in normalized for keyword in profile.keywords):
                return profile
    return GENERIC_PROFILE


def get_profile_by_id(profile_id: str) -> SegmentProfile | None:
    if profile_id == GENERIC_PROFILE.id:
        return GENERIC_PROFILE
    return next((profile for profile in SEGMENT_PROFILES if profile.id == profile_id), None)
