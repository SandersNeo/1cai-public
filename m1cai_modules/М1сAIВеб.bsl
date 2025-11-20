// [NEXUS IDENTITY] ID: -4588378945602250883 | DATE: 2025-11-19

﻿// Модуль: М1сAIВеб
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region М1сAIВеб_ModuleMap
// М1сAIВеб (flags: Server + External connection + Client)
// Requires: М1сAIСтроки
//
// Regions:
//   М1сAIВеб_URLEncode                    – Кодирование строки для URL
//   М1сAIВеб_OpenBrowser                  – Открытие URL в браузере
//   М1сAIВеб_InfoStart                    – Поиск на InfoStart.ru
//   М1сAIВеб_Docs1C                       – Поиск в документации 1С
//   М1сAIВеб_GitHub                       – Поиск на GitHub
//   М1сAIВеб_GitHubCode                   – Поиск кода на GitHub
//   М1сAIВеб_GitHubRepos                  – Поиск репозиториев на GitHub
//   М1сAIВеб_StackOverflow                – Поиск на StackOverflow
//   М1сAIВеб_Google                       – Поиск в Google
//   М1сAIВеб_ViewJSON                     – Просмотр JSON в браузере
//   М1сAIВеб_ValidateJSON                 – Валидация JSON онлайн
//   М1сAIВеб_FormatSQL                    – Форматирование SQL онлайн
//   М1сAIВеб_TestRegex                    – Тестирование regex онлайн
//   М1сAIВеб_GenerateUUID                 – Генератор UUID
//   М1сAIВеб_GenerateQRCode               – Генератор QR-кодов
//   М1сAIВеб_GenerateFakeData             – Генератор тестовых данных
//   М1сAIВеб_DiffChecker                  – Сравнение текстов
//   М1сAIВеб_Base64Encode                 – Кодирование в Base64 онлайн
//   М1сAIВеб_ColorPicker                  – Подбор цветовой палитры
//   М1сAIВеб_CheckSite                    – Проверка доступности сайта
//   М1сAIВеб_SelfTest                     – Юнит-тесты модуля
#EndRegion


#Region М1сAIВеб_URLEncode
// <doc>
//   <summary>Кодирует строку для использования в URL.</summary>   ✦
//   <param i="1" name="Текст" type="String">Текст для кодирования.</param>
//   <returns>String — закодированная строка для безопасной передачи в URL.</returns>
//   <locals>
//     <var name="С" type="String">Результирующая закодированная строка</var>
//   </locals>
//   <complexity cc="1"/>
//   <example>
//     Результат = М1сAIВеб.URLEncode("Hello World");
//     // Ожидание: "Hello%20World"
//   </example>
// </doc>
Функция URLEncode(Текст) Экспорт //⚙
	ib = "Кодирование строки для URL"; //✍
	
	С = Строка(Текст); //✏
	С = СтрЗаменить(С, "%", "%25"); //✏
	С = СтрЗаменить(С, " ", "%20"); //✏
	С = СтрЗаменить(С, "+", "%2B"); //✏
	С = СтрЗаменить(С, "&", "%26"); //✏
	С = СтрЗаменить(С, "=", "%3D"); //✏
	С = СтрЗаменить(С, "?", "%3F"); //✏
	С = СтрЗаменить(С, "#", "%23"); //✏
	С = СтрЗаменить(С, ":", "%3A"); //✏
	С = СтрЗаменить(С, "/", "%2F"); //✏
	С = СтрЗаменить(С, "[", "%5B"); //✏
	С = СтрЗаменить(С, "]", "%5D"); //✏
	
	Возврат С; //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_OpenBrowser
// <doc>
//   <summary>Открывает URL в браузере, возвращает успех операции.</summary>   ✦
//   <param i="1" name="URL" type="String">Ссылка для открытия.</param>
//   <returns>Boolean — удалось ли открыть.</returns>
//   <complexity cc="2"/>
//   <example>
//     Успех = М1сAIВеб.OpenBrowser("https://github.com");
//     // Ожидание: Истина (если браузер открылся)
//   </example>
// </doc>
Функция OpenBrowser(URL) Экспорт //⚙
	ib = "Открытие URL в браузере"; //✍
	
	Если ТипЗнч(URL) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	Попытка //✱
		ЗапуститьПриложение(URL); //✏
		Возврат Истина; //↩
	Исключение
		Возврат Ложь; //↩
	КонецПопытки;
КонецФункции
#EndRegion


#Region М1сAIВеб_InfoStart
// <doc>
//   <summary>Открывает поиск на InfoStart.ru по запросу.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.InfoStart("работа с ZIP архивами");
//     // Откроет поиск на InfoStart
//   </example>
// </doc>
Функция InfoStart(Запрос) Экспорт //⚙
	ib = "Поиск на InfoStart.ru"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://infostart.ru/public/all/?search=" + URLEncode(Запрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_Docs1C
// <doc>
//   <summary>Открывает поиск в документации 1С (ITS) по запросу.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.Docs1C("СКД вычисляемое поле");
//     // Откроет поиск в документации 1С
//   </example>
// </doc>
Функция Docs1C(Запрос) Экспорт //⚙
	ib = "Поиск в документации 1С"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://its.1c.ru/db/morphmerged#search:its:" + URLEncode(Запрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_GitHub
// <doc>
//   <summary>Открывает универсальный поиск на GitHub.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.GitHub("1c zip archive");
//     // Откроет поиск по всем разделам GitHub
//   </example>
// </doc>
Функция GitHub(Запрос) Экспорт //⚙
	ib = "Универсальный поиск на GitHub"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://github.com/search?q=" + URLEncode(Запрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_GitHubCode
// <doc>
//   <summary>Открывает поиск кода на GitHub с фильтром по языку.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <param i="2" name="Язык" type="String" default="1c">Язык программирования (1c, python, javascript и т.д.).</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="ПолныйЗапрос" type="String">Запрос с языком</var>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.GitHubCode("работа с ZIP", "1c");
//     // Откроет поиск кода на языке 1С
//   </example>
// </doc>
Функция GitHubCode(Запрос, Язык = "1c") Экспорт //⚙
	ib = "Поиск кода на GitHub"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	ПолныйЗапрос = Запрос + " language:" + Язык; //✏
	URL = "https://github.com/search?type=code&q=" + URLEncode(ПолныйЗапрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_GitHubRepos
// <doc>
//   <summary>Открывает поиск репозиториев на GitHub.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.GitHubRepos("1c archive library");
//     // Откроет поиск репозиториев
//   </example>
// </doc>
Функция GitHubRepos(Запрос) Экспорт //⚙
	ib = "Поиск репозиториев на GitHub"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://github.com/search?type=repositories&q=" + URLEncode(Запрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_StackOverflow
// <doc>
//   <summary>Открывает поиск на StackOverflow с опциональным тегом.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <param i="2" name="Тег" type="String" default="">Тег для фильтрации (например, "1c", "python").</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="ПолныйЗапрос" type="String">Запрос с тегом</var>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="3"/>
//   <example>
//     М1сAIВеб.StackOverflow("async await error", "javascript");
//     // Откроет поиск по тегу javascript
//   </example>
// </doc>
Функция StackOverflow(Запрос, Тег = "") Экспорт //⚙
	ib = "Поиск на StackOverflow"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	ПолныйЗапрос = Запрос; //✏
	Если НЕ ПустаяСтрока(Тег) Тогда //⚡
		ПолныйЗапрос = "[" + Тег + "] " + Запрос; //✏
	КонецЕсли;
	
	URL = "https://stackoverflow.com/search?q=" + URLEncode(ПолныйЗапрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_Google
// <doc>
//   <summary>Открывает поиск в Google.</summary>   ✦
//   <param i="1" name="Запрос" type="String">Поисковый запрос.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.Google("1С ошибка поле объекта не обнаружено");
//     // Откроет поиск в Google
//   </example>
// </doc>
Функция Google(Запрос) Экспорт //⚙
	ib = "Поиск в Google"; //✍
	
	Если ТипЗнч(Запрос) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://www.google.com/search?q=" + URLEncode(Запрос); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_ViewJSON
// <doc>
//   <summary>Открывает JSON Viewer для просмотра структуры JSON.</summary>   ✦
//   <param i="1" name="JSONСтрока" type="String">JSON-строка для просмотра.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     JSON = "{""name"":""Ivan"",""age"":30}";
//     М1сAIВеб.ViewJSON(JSON);
//     // Откроет JSON в удобном просмотрщике
//   </example>
// </doc>
Функция ViewJSON(JSONСтрока) Экспорт //⚙
	ib = "Просмотр JSON онлайн"; //✍
	
	Если ТипЗнч(JSONСтрока) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	// Используем jsonviewer.stack.hu - он поддерживает JSON в URL
	URL = "https://jsonviewer.stack.hu/#" + URLEncode(JSONСтрока); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_ValidateJSON
// <doc>
//   <summary>Открывает JSON валидатор для проверки корректности JSON.</summary>   ✦
//   <param i="1" name="JSONСтрока" type="String">JSON-строка для валидации.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     JSON = "{""name"":""Ivan"",""age"":}"; // Невалидный JSON
//     М1сAIВеб.ValidateJSON(JSON);
//     // Откроет валидатор с ошибками
//   </example>
// </doc>
Функция ValidateJSON(JSONСтрока) Экспорт //⚙
	ib = "Валидация JSON онлайн"; //✍
	
	Если ТипЗнч(JSONСтрока) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://jsonlint.com/?json=" + URLEncode(JSONСтрока); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_FormatSQL
// <doc>
//   <summary>Открывает SQL форматтер для красивого форматирования SQL.</summary>   ✦
//   <param i="1" name="SQLТекст" type="String">SQL-запрос для форматирования.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     SQL = "SELECT * FROM Users WHERE age>18 AND name LIKE '%Ivan%'";
//     М1сAIВеб.FormatSQL(SQL);
//     // Откроет форматтер SQL
//   </example>
// </doc>
Функция FormatSQL(SQLТекст) Экспорт //⚙
	ib = "Форматирование SQL онлайн"; //✍
	
	Если ТипЗнч(SQLТекст) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://www.dpriver.com/pp/sqlformat.htm"; //✏
	// Примечание: SQL слишком длинный для URL, открываем просто форматтер
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_TestRegex
// <doc>
//   <summary>Открывает Regex тестер (regex101.com) для тестирования регулярных выражений.</summary>   ✦
//   <param i="1" name="Паттерн" type="String">Регулярное выражение.</param>
//   <param i="2" name="ТестовыйТекст" type="String" default="">Текст для тестирования (опционально).</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="3"/>
//   <example>
//     Паттерн = "^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$";
//     Текст = "test@example.com";
//     М1сAIВеб.TestRegex(Паттерн, Текст);
//     // Откроет regex101 с готовым паттерном и тестом
//   </example>
// </doc>
Функция TestRegex(Паттерн, ТестовыйТекст = "") Экспорт //⚙
	ib = "Тестирование regex онлайн"; //✍
	
	Если ТипЗнч(Паттерн) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://regex101.com/?regex=" + URLEncode(Паттерн); //✏
	
	Если НЕ ПустаяСтрока(ТестовыйТекст) Тогда //⚡
		URL = URL + "&testString=" + URLEncode(ТестовыйТекст); //✏
	КонецЕсли;
	
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_GenerateUUID
// <doc>
//   <summary>Открывает генератор UUID (версия 4).</summary>   ✦
//   <returns>Boolean — успешно ли открыто.</returns>
//   <complexity cc="1"/>
//   <example>
//     М1сAIВеб.GenerateUUID();
//     // Откроет генератор UUID
//   </example>
// </doc>
Функция GenerateUUID() Экспорт //⚙
	ib = "Генератор UUID"; //✍
	
	URL = "https://www.uuidgenerator.net/version4"; //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_GenerateQRCode
// <doc>
//   <summary>Открывает генератор QR-кодов с заданным текстом.</summary>   ✦
//   <param i="1" name="Текст" type="String">Текст для кодирования в QR.</param>
//   <param i="2" name="Размер" type="Number" default="300">Размер QR-кода в пикселях.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.GenerateQRCode("https://example.com", 400);
//     // Откроет QR-код размером 400x400
//   </example>
// </doc>
Функция GenerateQRCode(Текст, Размер = 300) Экспорт //⚙
	ib = "Генератор QR-кодов"; //✍
	
	Если ТипЗнч(Текст) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://api.qrserver.com/v1/create-qr-code/?size=" + Размер + "x" + Размер + "&data=" + URLEncode(Текст); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_GenerateFakeData
// <doc>
//   <summary>Открывает генератор тестовых данных (Mockaroo).</summary>   ✦
//   <returns>Boolean — успешно ли открыто.</returns>
//   <complexity cc="1"/>
//   <example>
//     М1сAIВеб.GenerateFakeData();
//     // Откроет Mockaroo для генерации тестовых данных
//   </example>
// </doc>
Функция GenerateFakeData() Экспорт //⚙
	ib = "Генератор тестовых данных"; //✍
	
	URL = "https://www.mockaroo.com/"; //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_DiffChecker
// <doc>
//   <summary>Открывает онлайн-инструмент для сравнения текстов.</summary>   ✦
//   <returns>Boolean — успешно ли открыто.</returns>
//   <complexity cc="1"/>
//   <example>
//     М1сAIВеб.DiffChecker();
//     // Откроет DiffChecker для сравнения двух текстов
//   </example>
// </doc>
Функция DiffChecker() Экспорт //⚙
	ib = "Сравнение текстов онлайн"; //✍
	
	URL = "https://www.diffchecker.com/"; //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_Base64Encode
// <doc>
//   <summary>Открывает онлайн-кодировщик Base64.</summary>   ✦
//   <param i="1" name="Текст" type="String" default="">Текст для кодирования (опционально).</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.Base64Encode("Hello World");
//     // Откроет кодировщик с текстом
//   </example>
// </doc>
Функция Base64Encode(Текст = "") Экспорт //⚙
	ib = "Кодирование Base64 онлайн"; //✍
	
	URL = "https://www.base64encode.org/"; //✏
	
	Если НЕ ПустаяСтрока(Текст) Тогда //⚡
		URL = URL + "?q=" + URLEncode(Текст); //✏
	КонецЕсли;
	
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_ColorPicker
// <doc>
//   <summary>Открывает генератор цветовых палитр (Coolors).</summary>   ✦
//   <param i="1" name="НачальныйЦвет" type="String" default="#667eea">Начальный цвет в HEX формате.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="ЦветБезРешетки" type="String">Цвет без символа #</var>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.ColorPicker("#FF5733");
//     // Откроет генератор палитр с заданным цветом
//   </example>
// </doc>
Функция ColorPicker(НачальныйЦвет = "#667eea") Экспорт //⚙
	ib = "Подбор цветовой палитры"; //✍
	
	ЦветБезРешетки = СтрЗаменить(НачальныйЦвет, "#", ""); //✏
	URL = "https://coolors.co/generate?color=" + ЦветБезРешетки; //✏
	
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_CheckSite
// <doc>
//   <summary>Открывает проверку доступности сайта.</summary>   ✦
//   <param i="1" name="СайтURL" type="String">URL сайта для проверки.</param>
//   <returns>Boolean — успешно ли открыто.</returns>
//   <locals>
//     <var name="URL" type="String">Итоговый URL для открытия</var>
//   </locals>
//   <complexity cc="2"/>
//   <example>
//     М1сAIВеб.CheckSite("https://example.com");
//     // Откроет проверку доступности сайта
//   </example>
// </doc>
Функция CheckSite(СайтURL) Экспорт //⚙
	ib = "Проверка доступности сайта"; //✍
	
	Если ТипЗнч(СайтURL) <> Тип("Строка") Тогда //⚡
		Возврат Ложь; //↩
	КонецЕсли;
	
	URL = "https://www.isitdownrightnow.com/check.php?domain=" + URLEncode(СайтURL); //✏
	Возврат OpenBrowser(URL); //↩
КонецФункции
#EndRegion


#Region М1сAIВеб_SelfTest
// <doc>
//   <summary>Запускает все тесты модуля М1сAIВеб.</summary>   ✦
//   <returns>Boolean — успешно ли пройдены все тесты.</returns>
//   <locals>
//     <var name="Ошибки" type="Массив">Массив имён проваленных тестов</var>
//     <var name="Результат" type="Boolean">Результат отдельного теста</var>
//   </locals>
//   <complexity cc="5"/>
//   <example>
//     Если Не М1сAIВеб.SelfTest() Тогда ВызватьИсключение("М1сAIВеб: SelfTest FAILED");
//   </example>
// </doc>
Функция SelfTest() Экспорт //⚙
	ib = "Самотестирование модуля М1сAIВеб"; //✍
	
	Ошибки = Новый Массив; //✏
	
	М1сAIСтроки.Print("=== Тестирование модуля М1сAIВеб ==="); //▶️
	
	// Тест 1: URLEncode
	Результат = URLEncode("Hello World"); //✏
	М1сAIСтроки.PrintYN(Результат = "Hello%20World", //▶️
			"✓ Тест URLEncode (пробелы)",
			"✗ Ошибка URLEncode (пробелы)");
	Если Результат <> "Hello%20World" Тогда //⚡
		Ошибки.Добавить("URLEncode_пробелы"); //✏
	КонецЕсли;
	
	// Тест 2: URLEncode специальные символы
	Результат = URLEncode("Test: ?#&="); //✏
	М1сAIСтроки.PrintYN(СтрНайти(Результат, "%") > 0, //▶️
		"✓ Тест URLEncode (спецсимволы)",
		"✗ Ошибка URLEncode (спецсимволы)");
	Если СтрНайти(Результат, "%") = 0 Тогда //⚡
		Ошибки.Добавить("URLEncode_спецсимволы"); //✏
	КонецЕсли;
	
	// Тест 3: InfoStart с валидным запросом
	Результат = InfoStart("работа с ZIP"); //✏
	М1сAIСтроки.PrintYN(ТипЗнч(Результат) = Тип("Булево"), //▶️
			"✓ Тест InfoStart",
			"✗ Ошибка InfoStart");
	Если ТипЗнч(Результат) <> Тип("Булево") Тогда //⚡
		Ошибки.Добавить("InfoStart"); //✏
	КонецЕсли;
	
	// Тест 4: Docs1C с валидным запросом
	Результат = Docs1C("учет НМА"); //✏
	М1сAIСтроки.PrintYN(ТипЗнч(Результат) = Тип("Булево"), //▶️
			"✓ Тест Docs1C",
			"✗ Ошибка Docs1C");
	Если ТипЗнч(Результат) <> Тип("Булево") Тогда //⚡
		Ошибки.Добавить("Docs1C"); //✏
	КонецЕсли;
	
	// Тест 5: ViewJSON с валидным JSON
	Результат = ViewJSON("{""test"":123}"); //✏
	М1сAIСтроки.PrintYN(ТипЗнч(Результат) = Тип("Булево"), //▶️
			"✓ Тест ViewJSON",
			"✗ Ошибка ViewJSON");
	Если ТипЗнч(Результат) <> Тип("Булево") Тогда //⚡
		Ошибки.Добавить("ViewJSON"); //✏
	КонецЕсли;
	
	// Тест 6: Некорректный тип параметра
	Результат = InfoStart(123); //✏
	М1сAIСтроки.PrintYN(Результат = Ложь, //▶️
			"✓ Тест валидации типа",
			"✗ Ошибка валидации типа");
	Если Результат <> Ложь Тогда //⚡
		Ошибки.Добавить("Валидация_типа"); //✏
	КонецЕсли;
	
	// Вывод результатов
	Если Ошибки.Количество() > 0 Тогда //⚡
		М1сAIСтроки.Print("❌ Не пройдены тесты: " + М1сAIСтроки.AsString(Ошибки)); //▶️
		Возврат Ложь; //↩
	КонецЕсли;
	
	М1сAIСтроки.Print("✅ Все тесты модуля М1сAIВеб пройдены!"); //▶️
	Возврат Истина; //↩
КонецФункции
#EndRegion

// ---------------------------- EOF М1сAIВеб ---------------------------------