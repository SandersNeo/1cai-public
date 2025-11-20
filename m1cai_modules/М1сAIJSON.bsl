// [NEXUS IDENTITY] ID: -327824845790449879 | DATE: 2025-11-19

﻿// Модуль: М1сAIJSON
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region М1сAIJSON_ModuleMap
// М1сAIJSON (flags: Server + External connection + Client)
// Requires: -
//
// Regions:
//   М1сAIJSON_ToJSON      – Преобразование значения в JSON
//   М1сAIJSON_FromJSON    – Обратное преобразование из JSON (расширенный парсер)
//   М1сAIJSON_Utils       – Утилиты для отладки JSON (DebugJSON)
//   М1сAIJSON_Aliases     – Русские алиасы к экспортным функциям (ВJSON/ИзJSON/Самотест)
//   М1сAIJSON_JsonEqual   – Сравнение значений через JSON
//   М1сAIJSON_SelfTest    – Юнит-тесты модуля
#EndRegion


#Region М1сAIJSON_ToJSON
// <doc>
//   <summary>Преобразует значение 1C в строку JSON (через XDTOSerializer).</summary>   ✦
//   <param i="1" name="Value"       type="Variant">Любое значение, поддерживаемое XDTO.</param>
//   <param i="2" name="NoSpaces"    type="Boolean" default="True">Истина — компактный JSON без отступов.</param>
//   <param i="3" name="ShowMessage" type="Boolean" default="False">Истина — вывести JSON сообщением.</param>
//   <returns>String — строка JSON.</returns>
//   <locals>
//     <var name="JSONWriter" type="JSONWriter">Писатель JSON в строку</var>
//     <var name="Settings"   type="JSONWriterSettings">Настройки форматирования</var>
//     <var name="JSONText"   type="String">Результат сериализации</var>
//   </locals>
//   <complexity cc="4"/>
//   <example>
//     JSON = М1сAIJSON.ВJSON(Новый Структура("X,Y",10,20));
//   </example>
// </doc>
Функция ToJSON(Value = Undefined, NoSpaces = True, ShowMessage = False) Экспорт //⚙
    ib = "Сериализация значения в JSON-строку"; //✍
    
    JSONWriter = Новый JSONWriter(); //✏
    Если Boolean(NoSpaces) Тогда //⚡
        Settings = Новый JSONWriterSettings(JSONLineBreak.None, ""); //✏
    Иначе
        Settings = Новый JSONWriterSettings(JSONLineBreak.Auto, "  "); //✏
    КонецЕсли;
    JSONWriter.SetString(Settings); //✏
    
    Попытка //✱
        XDTOSerializer.WriteJSON(JSONWriter, Value, XMLTypeAssignment.Explicit);
        JSONText = JSONWriter.Close(); //✏
    Исключение
        JSONText = ""; //✏
    КонецПопытки;
    
    Если Boolean(ShowMessage) Тогда //⚡
        М1сAIСтроки.Print(JSONText, "JSON", ""); //▶️
    КонецЕсли;
    
    Возврат JSONText; //↩
КонецФункции

#Region examples_М1сAIJSON_ToJSON
// Пример 1: массив
//   JSON = М1сAIJSON.ВJSON(Новый Массив(1,2,3));
//   // ожидание: "[1,2,3]"
//
// Пример 2: структура с форматированием
//   Структ = Новый Структура("X,Y",10,20);
//   JSON = М1сAIJSON.ВJSON(Структ, Ложь, Истина);
//   // ожидание: JSON с отступами и ключами "X","Y"
//
// Пример 3: строка
//   JSON = М1сAIJSON.ВJSON("Hello");
//   // ожидание: "\"Hello\""
#EndRegion
#EndRegion

/// <summary>
/// Возвращает JSON-представление объекта по ссылке или самому объекту.
/// </summary>
/// <param name="Ссылка">Ссылка или объект — например, СправочникСсылка, ДокументСсылка или сам объект.</param>
/// <returns>Строка — JSON-представление объекта со всеми реквизитами.</returns>
/// <example>
/// JSON = М1сAIJSON.JSONOfObject(Справочники.Контрагенты.НайтиПоКоду("0001"));
/// JSON = М1сAIJSON.JSONOfObject(ЭтотОбъект);
/// </example>
/// <syntax>
/// JSONOfObject(Ссылка)
/// </syntax>
Функция JSONOfObject(Ссылка) Экспорт
    Если Ссылка = Неопределено Тогда
        Возврат "";
    КонецЕсли;
    Попытка
        // Если у значения есть метод Пустая() — это скорее всего ссылка
        Если Ссылка.Пустая() Тогда
            Возврат "";
        КонецЕсли;
        Объект = Ссылка.ПолучитьОбъект();
    Исключение
        // Если метод Пустая() не существует — значит это не ссылка, а уже объект
        Объект = Ссылка;
    КонецПопытки;
    Возврат М1сAIJSON.ToJSON(Объект);
КонецФункции

#Region М1сAIJSON_Utils
// <doc>
//   <summary>Печатает краткую диагностику JSON-строки (для отладки).</summary>   ✦
//   <param i="1" name="JSONText" type="String">Исходная JSON-строка.</param>
//   <returns>Void — выводит диагностические сообщения.</returns>
//   <complexity cc="1"/>
//   <example>
//     // Вызов из FromJSON при Debug=True
//     DebugJSON(JSONText);
//   </example>
// </doc>
Функция DebugJSON(JSONText) Экспорт //⚙
    ib = "Диагностика JSON-строки: тип, длина, первые символы"; //✍
    
    Message("=== ОТЛАДКА JSON ==="); //▶️
    Message("Тип данных: " + TypeOf(JSONText)); //▶️
    Message("Длина: " + Format(StrLen(JSONText), "ЧГ=")); //▶️
    Message("Первые 200 символов:"); //▶️
    Message(Left(JSONText, 200)); //▶️
    Message("=================="); //▶️
КонецФункции
#EndRegion


#Region М1сAIJSON_FromJSON
// <doc>
//   <summary>Преобразует JSON-строку обратно в значение 1C. Включает диагностику и запасные способы чтения.</summary>   ✦
//   <param i="1" name="JSONText"            type="String">Строка JSON.</param>
//   <param i="2" name="ReplaceSingleQuotes" type="Boolean" default="False">Истина — заменить одинарные кавычки на двойные.</param>
//   <param i="3" name="Debug"               type="Boolean" default="False">Истина — подробный вывод диагностики.</param>
//   <returns>Variant — восстановленное значение или Неопределено при ошибке.</returns>
//   <locals>
//     <var name="JSONReader" type="JSONReader">Читатель JSON</var>
//     <var name="Value"      type="Variant">Результат десериализации</var>
//   </locals>
//   <complexity cc="6"/>
//   <example>
//     Знач = М1сAIJSON.ИзJSON("{""X"":5,""Y"":10}");
//   </example>
// </doc>
Функция FromJSON(JSONText, ReplaceSingleQuotes = False, Debug = False) Экспорт //⚙
    ib = "Десериализация JSON-строки в значение (с отладкой)"; //✍
    
    Если Debug Тогда DebugJSON(JSONText); КонецЕсли; //⚡
    
    Если JSONText = Undefined ИЛИ JSONText = "" Тогда //⚡
        Если Debug Тогда Message("ОШИБКА: Пустой JSON"); КонецЕсли; //▶️
        Возврат Undefined; //↩
    КонецЕсли;
    
    Если TypeOf(JSONText) <> Type("String") Тогда //⚡
        Попытка //✱
            JSONText = String(JSONText); //✏
        Исключение
            Если Debug Тогда Message("ОШИБКА: Невозможно привести к строке"); КонецЕсли; //▶️
            Возврат Undefined; //↩
        КонецПопытки;
    КонецЕсли;
    
    Если Boolean(ReplaceSingleQuotes) Тогда //⚡
        JSONText = StrReplace(JSONText, "'", """"); //✏
    КонецЕсли;
    
    JSONText = TrimAll(JSONText); //✏
    
    // Метод 1: стандартный ReadJSON
    JSONReader = Новый JSONReader; //✏
    Попытка //✱
        JSONReader.SetString(JSONText);
        Value = ReadJSON(JSONReader, False); //✏
        JSONReader.Close();
        Если Debug Тогда Message("Метод 1 (ReadJSON) - УСПЕХ"); КонецЕсли; //▶️
        Возврат Value; //↩
    Исключение
        Если Debug Тогда Message("Метод 1 (ReadJSON) - ОШИБКА: " + ErrorDescription()); КонецЕсли; //▶️
        JSONReader.Close();
    КонецПопытки;
    
    // Метод 2: XDTOSerializer
    JSONReader = Новый JSONReader; //✏
    Попытка //✱
        JSONReader.SetString(JSONText);
        Value = XDTOSerializer.ReadJSON(JSONReader); //✏
        JSONReader.Close();
        Если Debug Тогда Message("Метод 2 (XDTOSerializer) - УСПЕХ"); КонецЕсли; //▶️
        Возврат Value; //↩
    Исключение
        Если Debug Тогда Message("Метод 2 (XDTOSerializer) - ОШИБКА: " + ErrorDescription()); КонецЕсли; //▶️
        JSONReader.Close();
    КонецПопытки;
    
    // Метод 3: через временный файл (иногда помогает на больших строках)
    Попытка //✱
        TempFileName = GetTempFileName("json"); //✏
        TextDocument = Новый TextDocument; //✏
        TextDocument.SetText(JSONText);
        TextDocument.Write(TempFileName, TextEncoding.UTF8);
        
        JSONReader = Новый JSONReader; //✏
        JSONReader.OpenFile(TempFileName, TextEncoding.UTF8);
        Value = ReadJSON(JSONReader, False); //✏
        JSONReader.Close();
        
        DeleteFiles(TempFileName);
        Если Debug Тогда Message("Метод 3 (через файл) - УСПЕХ"); КонецЕсли; //▶️
        Возврат Value; //↩
    Исключение
        Если Debug Тогда Message("Метод 3 (через файл) - ОШИБКА: " + ErrorDescription()); КонецЕсли; //▶️
        Попытка
            JSONReader.Close();
            DeleteFiles(TempFileName);
        Исключение
        КонецПопытки;
    КонецПопытки;
    
    Если Debug Тогда Message("ВСЕ МЕТОДЫ НЕ СРАБОТАЛИ!"); КонецЕсли; //▶️
    Возврат Undefined; //↩
КонецФункции

#Region examples_М1сAIJSON_FromJSON
// Пример 1: массив
//   JSONText = "[1,2,3]";
//   Массив = М1сAIJSON.ИзJSON(JSONText);
//   // ожидание: Массив[0]=1 и Массив[2]=3
//
// Пример 2: структура
//   JSONText = "{\"X\":5,\"Y\":10}";
//   Структ = М1сAIJSON.ИзJSON(JSONText);
//   // ожидание: Структ.X=5 и Структ.Y=10
#EndRegion
#EndRegion


#Region М1сAIJSON_Aliases
// <doc>
//   <summary>Русские формат-явные алиасы экспортных функций.</summary>   ✦
//   <returns>Обёртки вызывают ToJSON/FromJSON/SelfTest без изменения логики.</returns>
//   <complexity cc="1"/>
//   <example>
//     JSON = М1сAIJSON.ВJSON(Структура);
//     Знач = М1сAIJSON.ИзJSON(JSON);
//     Ок   = М1сAIJSON.Самотест();
//   </example>
// </doc>
Функция ВJSON(Значение, БезОтступов = Истина, ПоказатьСообщение = Ложь) Экспорт //⚙
    ib = "Русский алиас ToJSON (формат JSON подчёркнут)"; //✍
    Возврат ToJSON(Значение, БезОтступов, ПоказатьСообщение); //↩
КонецФункции

Функция ИзJSON(JSONСтрока, ЗаменитьОдинарныеКавычки = Ложь, Отладка = Ложь) Экспорт //⚙
    ib = "Русский алиас FromJSON (формат JSON подчёркнут)"; //✍
    Возврат FromJSON(JSONСтрока, ЗаменитьОдинарныеКавычки, Отладка); //↩
КонецФункции

Функция Самотест() Экспорт //⚙
    ib = "Русский алиас SelfTest"; //✍
    Возврат SelfTest(); //↩
КонецФункции
#EndRegion


#Region М1сAIJSON_JsonEqual
// <doc>
//   <summary>Сравнивает несколько значений через JSON-сериализацию.</summary>   ✦
//   <param i="1" name="Value1" type="Variant" optional="True"/>
//   <param i="2" name="Value2" type="Variant" optional="True"/>
//   <param i="3" name="Value3" type="Variant" optional="True"/>
//   <param i="4" name="Value4" type="Variant" optional="True"/>
//   <param i="5" name="Value5" type="Variant" optional="True"/>
//   <param i="6" name="Value6" type="Variant" optional="True"/>
//   <param i="7" name="Value7" type="Variant" optional="True"/>
//   <param i="8" name="Value8" type="Variant" optional="True"/>
//   <returns>Boolean — Истина, если все переданные значения равны.</returns>
//   <complexity cc="4"/>
//   <example>
//     М1сAIJSON.JsonEqual(Новый Структура("A,B",1,2), Новый Структура("A,B",1,2)); // Истина
//   </example>
// </doc>
Функция JsonEqual(Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Экспорт //⚙
    ib = "Проверка равенства значений через сериализацию в JSON"; //✍
    
    Values = Новый Array; //✏
    Если Value1 <> Undefined Тогда Values.Add(Value1); КонецЕсли;
    Если Value2 <> Undefined Тогда Values.Add(Value2); КонецЕсли;
    Если Value3 <> Undefined Тогда Values.Add(Value3); КонецЕсли;
    Если Value4 <> Undefined Тогда Values.Add(Value4); КонецЕсли;
    Если Value5 <> Undefined Тогда Values.Add(Value5); КонецЕсли;
    Если Value6 <> Undefined Тогда Values.Add(Value6); КонецЕсли;
    Если Value7 <> Undefined Тогда Values.Add(Value7); КонецЕсли;
    Если Value8 <> Undefined Тогда Values.Add(Value8); КонецЕсли;
    
    Если Values.Count() = 0 Тогда //⚡
        Возврат True; //↩
    КонецЕсли;
    
    EtalonJSON = ToJSON(Values[0]); //✏
    Для Каждого Value Из Values Цикл //⟳
        CurrentJSON = ToJSON(Value); //✏
        Если EtalonJSON <> CurrentJSON Тогда Возврат False; КонецЕсли; //⚡
    КонецЦикла;
    
    Возврат True; //↩
КонецФункции
#EndRegion


#Region М1сAIJSON_SelfTest
// <doc>
//   <summary>Юнит-тесты функций М1сAIJSON.</summary>   ✦
//   <returns>Boolean — Истина, если все тесты пройдены.</returns>
//   <complexity cc="5"/>
//   <example>
//     Если Не М1сAIJSON.Самотест() Тогда ВызватьИсключение("М1сAIJSON: SelfTest FAILED");
//   </example>
// </doc>
Функция SelfTest() Экспорт //⚙
    ib = "Самопроверка корректности JSON-функций М1сAIJSON"; //✍
    
    n = 100; //✏
    json = ToJSON(n); //✏
    Если FromJSON(json) <> n Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: число", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    
    s = Новый Структура("X,Y", 5, 10); //✏
    json = ToJSON(s); //✏
    res = FromJSON(json); //✏
    Если НЕ (res.X = 5 И res.Y = 10) Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: структура", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    
    Если НЕ JsonEqual(1, 1, 1) Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: JsonEqual равные", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    Если JsonEqual(1, 2) Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: JsonEqual разные", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    
    М1сAIСтроки.Print("М1сAIJSON: SelfTest passed", "SelfTest", ""); //▶️
    Возврат Истина; //↩
КонецФункции
#EndRegion

// ---------------------------- EOF М1сAIJSON ---------------------------------