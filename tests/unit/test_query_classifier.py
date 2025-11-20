# [NEXUS IDENTITY] ID: 8012280499333434021 | DATE: 2025-11-19


from src.ai.orchestrator import AIService, QueryClassifier, QueryType


def test_classify_standard_1c_query():
    classifier = QueryClassifier()
    intent = classifier.classify("Как сделано в УТ типовая реализация?")

    assert intent.query_type == QueryType.STANDARD_1C
    assert intent.confidence > 0
    assert AIService.NAPARNIK in intent.preferred_services
    # Для стандартных 1С-вопросов должен предлагаться BA requirements extractor
    assert "ba_requirements_extract" in intent.suggested_tools


def test_classify_graph_query():
    classifier = QueryClassifier()
    intent = classifier.classify(
        "Где используется этот метод и какие есть зависимости?"
    )

    assert intent.query_type == QueryType.GRAPH_QUERY
    assert AIService.NEO4J in intent.preferred_services
    # Для графовых запросов ожидаем сценарный инструмент BA→Dev→QA
    assert "scenario_ba_dev_qa" in intent.suggested_tools


def test_classify_code_generation():
    classifier = QueryClassifier()
    intent = classifier.classify("Создай функцию для проведения документа")

    assert intent.query_type == QueryType.CODE_GENERATION
    assert AIService.QWEN_CODER in intent.preferred_services
    # Для кодогенерации должен предлагаться хотя бы один non-prod инструмент
    assert intent.suggested_tools


def test_classify_semantic_search():
    classifier = QueryClassifier()
    intent = classifier.classify("Найди похожий код обработки ошибок")

    assert intent.query_type == QueryType.SEMANTIC_SEARCH
    assert AIService.QDRANT in intent.preferred_services


def test_invalid_query_returns_unknown():
    classifier = QueryClassifier()
    intent = classifier.classify("")  # пустая строка

    assert intent.query_type == QueryType.UNKNOWN
    assert intent.confidence == 0.0
    assert intent.preferred_services  # есть хотя бы naparnik по умолчанию
    assert intent.suggested_tools == []
