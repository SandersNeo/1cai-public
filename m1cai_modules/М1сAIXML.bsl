// [NEXUS IDENTITY] ID: -1483128076868603550 | DATE: 2025-11-19

﻿// Модуль: М1сAIXML
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region М1сAIXML_ModuleMap
// М1сAIXML (flags: Server + External connection + Client)
// Requires: -
//
// Regions:
//   М1сAIXML_ToXML     – Преобразует значение в XML-строку
//   М1сAIXML_FromXML   – Преобразует XML-строку обратно в значение
//   М1сAIXML_Aliases   – Русские алиасы к экспортным функциям (ВXML/ИзXML/Самотест)
//   М1сAIXML_SelfTest  – Юнит-тесты модуля
#EndRegion


#Region М1сAIXML_ToXML
// <doc>
//   <summary>Преобразует произвольное значение 1C в XML-строку (через XDTOSerializer).</summary>   ✦
//   <param i="1" name="Value"       type="Variant">Значение любого поддерживаемого типа.</param>
//   <param i="2" name="ShowMessage" type="Boolean" default="False">Истина — вывести результат в окно сообщения.</param>
//   <returns>String — XML-представление значения или пустая строка при ошибке.</returns>
//   <locals>
//     <var name="XMLWriter" type="XMLWriter">Писатель XML в строку</var>
//     <var name="XMLString" type="String">Результирующая XML-строка</var>
//   </locals>
//   <complexity cc="3"/>
//   <example>
//     Массив = Новый Массив(); Массив.Добавить("A"); Массив.Добавить("B");
//     XML = М1сAIXML.ВXML(Массив);
//     // ожидание: XML содержит <Value>A</Value> и <Value>B</Value>
//   </example>
// </doc>
Функция ToXML(Value, ShowMessage = False) Экспорт //⚙
    ib = "Сериализация значения в XML"; //✍
    
    XMLWriter = Новый XMLWriter(); //✏
    XMLWriter.SetString(); //✏
    
    Попытка //✱
        XDTOSerializer.WriteXML(XMLWriter, Value);
        XMLString = XMLWriter.Close(); //✏
    Исключение
        XMLString = ""; //✏
    КонецПопытки;
    
    Если Boolean(ShowMessage) Тогда //⚡
        М1сAIСтроки.Print(XMLString, "XML", ""); //▶️
    КонецЕсли;
    
    Возврат XMLString; //↩
КонецФункции
#EndRegion


#Region М1сAIXML_FromXML
// <doc>
//   <summary>Восстанавливает значение 1C из XML-строки (через XDTOSerializer).</summary>   ✦
//   <param i="1" name="XMLString" type="String">XML-строка, полученная через ToXML или из иного источника.</param>
//   <returns>Variant — восстановленное значение (массив, структура, число и т.п.) или Неопределено при ошибке.</returns>
//   <locals>
//     <var name="XMLReader" type="XMLReader">Читатель XML из строки</var>
//     <var name="Value"     type="Variant">Результат десериализации</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     XML = М1сAIXML.ВXML(Новый Структура("A,B",123,"XYZ"));
//     Знач = М1сAIXML.ИзXML(XML);
//   </example>
// </doc>
Функция FromXML(XMLString) Экспорт //⚙
    ib = "Десериализация XML-строки в значение"; //✍
    
    XMLReader = Новый XMLReader(); //✏
    XMLReader.SetString(XMLString); //✏
    
    Попытка //✱
        Value = XDTOSerializer.ReadXML(XMLReader); //✏
    Исключение
        М1сAIСтроки.Print(ErrorDescription(), "Ошибка чтения XML", ":", Истина); //▶️
    КонецПопытки;
    
    Возврат Value; //↩
КонецФункции
#EndRegion


#Region М1сAIXML_Aliases
// <doc>
//   <summary>Русские формат-явные алиасы экспортных функций для удобства вызова.</summary>   ✦
//   <returns>Обёртки вызывают исходные функции ToXML, FromXML и SelfTest без изменения логики.</returns>
//   <complexity cc="1"/>
//   <example>
//     XML = М1сAIXML.ВXML(Структура);
//     Знач = М1сAIXML.ИзXML(XML);
//     Ок   = М1сAIXML.Самотест();
//   </example>
// </doc>
Функция ВXML(Значение, ПоказыватьСообщение = Ложь) Экспорт //⚙
    ib = "Русский алиас ToXML"; //✍
    Возврат ToXML(Значение, ПоказыватьСообщение); //↩
КонецФункции

Функция ИзXML(XMLСтрока) Экспорт //⚙
    ib = "Русский алиас FromXML"; //✍
    Возврат FromXML(XMLСтрока); //↩
КонецФункции

Функция Самотест() Экспорт //⚙
    ib = "Русский алиас SelfTest"; //✍
    Возврат SelfTest(); //↩
КонецФункции
#EndRegion


#Region М1сAIXML_SelfTest
// <doc>
//   <summary>Запускает базовые юнит-проверки корректности сериализации/десериализации.</summary>   ✦
//   <returns>Boolean — Истина при успешном прохождении всех проверок.</returns>
//   <locals>
//     <var name="ИсходМассив"  type="Массив">Тестовый набор значений</var>
//     <var name="ВосстМассив"  type="Массив">Результат после FromXML</var>
//     <var name="ИсходСтрукт"  type="Структура">Тестовая структура</var>
//     <var name="ВосстСтрукт"  type="Структура">Восстановленная структура</var>
//     <var name="XML1"         type="String">XML массива</var>
//     <var name="XML2"         type="String">XML структуры</var>
//     <var name="XML3"         type="String">XML числа</var>
//     <var name="Число"        type="Число">Тестовое число</var>
//   </locals>
//   <complexity cc="6"/>
//   <example>
//     Если Не М1сAIXML.Самотест() Тогда ВызватьИсключение("М1сAIXML: SelfTest FAILED");
//   </example>
// </doc>
Функция SelfTest() Экспорт //⚙
    ib = "Самопроверка функций М1сAIXML"; //✍
    
    // Тест 1: массив
    ИсходМассив = Новый Массив(); //✏
    ИсходМассив.Добавить(10); //✏
    ИсходМассив.Добавить(20); //✏
    XML1 = ToXML(ИсходМассив); //✏
    ВосстМассив = FromXML(XML1); //✏
    
    Если ВосстМассив.Количество() <> ИсходМассив.Количество() Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: Массив - неверное количество", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    
    Для i = 0 По ИсходМассив.Количество() - 1 Цикл //⟳
        Если ВосстМассив.Получить(i) <> ИсходМассив.Получить(i) Тогда //⚡
            М1сAIСтроки.Print("SelfTest FAILED: Массив - элемент №" + String(i), "SelfTest", ""); //▶️
            Возврат False; //↩
        КонецЕсли;
    КонецЦикла;
    
    // Тест 2: структура
    ИсходСтрукт = Новый Структура("A,B", 123, "XYZ"); //✏
    XML2 = ToXML(ИсходСтрукт); //✏
    ВосстСтрукт = FromXML(XML2); //✏
    Если НЕ (ВосстСтрукт.A = 123 И ВосстСтрукт.B = "XYZ") Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: Структура", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    
    // Тест 3: число
    Число = 42; //✏
    XML3 = ToXML(Число); //✏
    Если FromXML(XML3) <> Число Тогда //⚡
        М1сAIСтроки.Print("SelfTest FAILED: Число", "SelfTest", ""); //▶️
        Возврат False; //↩
    КонецЕсли;
    
    М1сAIСтроки.Print("М1сAIXML: SelfTest passed", "SelfTest", ""); //▶️
    Возврат Истина; //↩
КонецФункции
#EndRegion

// ---------------------------- EOF М1сAIXML ---------------------------------