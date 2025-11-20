# [NEXUS IDENTITY] ID: -5858402278412248907 | DATE: 2025-11-19

"""
Tests for 1C Code Graph Builder (OneCCodeGraphBuilder).
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, NodeKind
from src.ai.code_graph_1c_builder import OneCCodeGraphBuilder


@pytest.mark.asyncio
async def test_build_from_simple_module() -> None:
    """Тест построения графа из простого BSL модуля."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    module_code = """
    // Общий модуль для работы с заказами

    Функция СоздатьЗаказ(ПараметрыЗаказа) Экспорт
        // Создание нового заказа
        Возврат НовыйЗаказ;
    КонецФункции

    Процедура ОбновитьЗаказ(Заказ, НовыеДанные) Экспорт
        // Обновление заказа
        Заказ.Обновить(НовыеДанные);
    КонецПроцедуры

    Функция ПолучитьЗаказ(Идентификатор)
        // Получение заказа по ID
        Возврат НайтиЗаказ(Идентификатор);
    КонецФункции
    """

    stats = await builder.build_from_module(
        "ОбщийМодуль.УправлениеЗаказами",
        module_code,
        module_metadata={"owner": "test-team"},
    )

    assert stats["nodes_created"] > 0
    assert stats["edges_created"] > 0
    assert stats["functions"] >= 2  # СоздатьЗаказ, ПолучитьЗаказ
    assert stats["procedures"] >= 1  # ОбновитьЗаказ

    # Проверяем, что модуль создан
    module_node = await backend.get_node("module:ОбщийМодуль.УправлениеЗаказами")
    assert module_node is not None
    assert module_node.kind == NodeKind.MODULE
    assert "bsl" in module_node.labels

    # Проверяем, что функции созданы
    func_node = await backend.get_node(
        "function:ОбщийМодуль.УправлениеЗаказами:СоздатьЗаказ"
    )
    assert func_node is not None
    assert func_node.kind == NodeKind.FUNCTION
    assert func_node.props.get("exported") is True

    proc_node = await backend.get_node(
        "procedure:ОбщийМодуль.УправлениеЗаказами:ОбновитьЗаказ"
    )
    assert proc_node is not None


@pytest.mark.asyncio
async def test_build_from_module_with_dependencies() -> None:
    """Тест построения графа с зависимостями между функциями."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    module_code = """
    Функция ФункцияА() Экспорт
        Результат = ФункцияБ();
        Возврат Результат;
    КонецФункции

    Функция ФункцияБ()
        Результат = ФункцияВ();
        Возврат Результат;
    КонецФункции

    Функция ФункцияВ()
        Возврат Истина;
    КонецФункции
    """

    stats = await builder.build_from_module("Модуль.Тест", module_code)

    # Проверяем наличие зависимостей
    func_a = await backend.get_node("function:Модуль.Тест:ФункцияА")
    func_b = await backend.get_node("function:Модуль.Тест:ФункцияБ")

    assert func_a is not None
    assert func_b is not None

    # Проверяем, что есть рёбра зависимостей
    neighbors_a = await backend.neighbors(func_a.id)
    neighbor_ids = {n.id for n in neighbors_a}
    # ФункцияА должна зависеть от ФункцияБ (через DEPENDS_ON)
    assert any("ФункцияБ" in n.id for n in neighbors_a) or any(
        "ФункцияВ" in n.id for n in neighbors_a
    )


@pytest.mark.asyncio
async def test_build_from_module_with_query() -> None:
    """Тест построения графа с SQL-запросами."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    module_code = """
    Функция ПолучитьНоменклатуру() Экспорт
        Запрос = Новый Запрос;
        Запрос.Текст = "
            ВЫБРАТЬ
                Номенклатура.Ссылка,
                Номенклатура.Наименование
            ИЗ
                Справочник.Номенклатура КАК Номенклатура";
        Возврат Запрос.Выполнить();
    КонецФункции
    """

    stats = await builder.build_from_module("Модуль.Запросы", module_code)

    # Проверяем, что создан узел таблицы
    table_node = await backend.get_node("db_table:1c:Справочник.Номенклатура")
    assert table_node is not None
    assert table_node.kind == NodeKind.DB_TABLE


@pytest.mark.asyncio
async def test_export_graph() -> None:
    """Тест экспорта графа в JSON."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    module_code = """
    Функция Тест() Экспорт
        Возврат Истина;
    КонецФункции
    """

    await builder.build_from_module("Модуль.Тест", module_code)
    graph_export = await builder.export_graph()

    assert "nodes" in graph_export
    assert "edges" in graph_export
    assert len(graph_export["nodes"]) > 0

    # Проверяем формат узлов
    node = graph_export["nodes"][0]
    assert "id" in node
    assert "kind" in node
    assert "display_name" in node
    assert "labels" in node
    assert "props" in node


@pytest.mark.asyncio
async def test_build_from_directory(tmp_path) -> None:
    """Тест построения графа из директории с несколькими файлами."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    # Создаём тестовые BSL файлы
    module1 = tmp_path / "module1.bsl"
    module1.write_text(
        """
        Функция Функция1() Экспорт
            Возврат Истина;
        КонецФункции
        """,
        encoding="utf-8",
    )

    module2 = tmp_path / "module2.bsl"
    module2.write_text(
        """
        Функция Функция2() Экспорт
            Возврат Истина;
        КонецФункции
        """,
        encoding="utf-8",
    )

    stats = await builder.build_from_directory(
        str(tmp_path), pattern="*.bsl", recursive=False
    )

    assert stats["total_modules"] == 2
    assert stats["total_nodes"] > 0
    assert stats["total_edges"] > 0
    assert len(stats["modules"]) == 2


@pytest.mark.asyncio
async def test_build_from_empty_module() -> None:
    """Тест построения графа из пустого модуля."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    stats = await builder.build_from_module("Модуль.Пустой", "")

    # Должен быть создан хотя бы узел модуля
    assert stats["nodes_created"] >= 1
    module_node = await backend.get_node("module:Модуль.Пустой")
    assert module_node is not None


@pytest.mark.asyncio
async def test_build_from_module_with_invalid_syntax() -> None:
    """Тест построения графа из модуля с синтаксическими ошибками."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    # Модуль с незакрытой функцией
    invalid_code = """
    Функция Тест()
        Возврат Истина;
    // КонецФункции пропущен
    """

    # Должен обработать хотя бы частично
    stats = await builder.build_from_module("Модуль.Ошибка", invalid_code)

    # Должен создать хотя бы узел модуля
    assert stats["nodes_created"] >= 1
    module_node = await backend.get_node("module:Модуль.Ошибка")
    assert module_node is not None


@pytest.mark.asyncio
async def test_build_from_module_with_special_characters() -> None:
    """Тест построения графа из модуля со специальными символами."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    module_code = """
    Функция ТестИмяФункции_123() Экспорт
        Перем ИмяПеременной123;
        ИмяПеременной123 = "Тестовая строка с \"кавычками\" и \\n\\t";
        Возврат Истина;
    КонецФункции
    """

    stats = await builder.build_from_module("Модуль.СпецСимволы", module_code)

    assert stats["nodes_created"] > 0
    func_node = await backend.get_node("function:Модуль.СпецСимволы:ТестИмяФункции_123")
    assert func_node is not None


@pytest.mark.asyncio
async def test_build_from_module_with_unicode() -> None:
    """Тест построения графа из модуля с Unicode символами."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    module_code = """
    Функция СоздатьЗаказ(ПараметрыЗаказа) Экспорт
        // Создание нового заказа с Unicode комментарием
        // Товар: 🛒, Цена: €100, Статус: ✅
        Возврат НовыйЗаказ;
    КонецФункции
    """

    stats = await builder.build_from_module("Модуль.Unicode", module_code)

    assert stats["nodes_created"] > 0
    func_node = await backend.get_node("function:Модуль.Unicode:СоздатьЗаказ")
    assert func_node is not None


@pytest.mark.asyncio
async def test_export_graph_with_no_nodes() -> None:
    """Тест экспорта пустого графа."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    graph_export = await builder.export_graph()

    assert "nodes" in graph_export
    assert "edges" in graph_export
    assert isinstance(graph_export["nodes"], list)
    assert isinstance(graph_export["edges"], list)


@pytest.mark.asyncio
async def test_build_from_directory_with_no_files(tmp_path) -> None:
    """Тест построения графа из пустой директории."""
    backend = InMemoryCodeGraphBackend()
    builder = OneCCodeGraphBuilder(backend, use_ast_parser=False)

    stats = await builder.build_from_directory(
        str(tmp_path), pattern="*.bsl", recursive=False
    )

    assert stats["total_modules"] == 0
    assert stats["total_nodes"] == 0
    assert stats["total_edges"] == 0
    assert len(stats["modules"]) == 0
