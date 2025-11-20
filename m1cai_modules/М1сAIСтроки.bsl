// [NEXUS IDENTITY] ID: -286095299546011106 | DATE: 2025-11-19

﻿// Модуль: М1сAIСтроки
// Назначение: Модуль работы со строками
//
////////////////////////////////////////////////////////////////////////////////


#Region М1сAIСтроки_ModuleMap
// М1сAIСтроки (flags: Server + External connection + Client)
//
// Regions:
//   М1сAIСтроки_AsString    – Преобразование значения в строку
//   М1сAIСтроки_Split       – Разбиение строки с добавлением префикса/суффикса
//   М1сAIСтроки_Wrap        – Обёртывание строк или частей
//   М1сAIСтроки_HasText     – Проверка наличия текста
//   М1сAIСтроки_FormatText – Форматирование вывода и логирование
//   М1сAIСтроки_Print       – Вывод через Message
//   М1сAIСтроки_PrintYN     – Вывод в зависимости от условия
//   М1сAIСтроки_PrintJSON   – Вывод JSON через Message
//   М1сAIСтроки_PrintXML    – Вывод XML через Message
//   М1сAIСтроки_FilterTableByField - фильтрация таблицы по переданным параметрам
//   М1сAIСтроки_GetTemplate - Получает текст из общего макета с подстановкой параметров  | 1.1.0
//   М1сAIСтроки_SelfTest    – Юнит-тесты модуля
#EndRegion

#Region М1сAIСтроки_AsString
/// <summary>
/// Enhanced conversion of any 1C value to string representation with advanced formatting.
/// </summary>
/// <param name="Value">Value to convert (date, number, object, etc.)</param>
/// <param name="Prefix" type="String" optional="True">Prefix to add before result</param>
/// <param name="Suffix" type="String" optional="True">Suffix to add after result</param>
/// <param name="FormatOptions" type="Structure" optional="True">Advanced formatting options</param>
/// <returns type="String">Enhanced string representation with formatting applied</returns>
Функция AsString(Value, Prefix = "", Suffix = "",
		FormatOptions = Undefined,
		ConfigPerformanceLog = False,
		ConfigDebugMode = False)
	Экспорт
	
	// Performance tracking
	StartTime = ?(ConfigPerformanceLog, CurrentUniversalDateInMilliseconds(), 0);
	
	Попытка
		// Input validation
		Если Value = Undefined Тогда
			Result = "Undefined";
		ИначеЕсли Value = Null Тогда
			Result = "Null";
		Иначе
			// Enhanced type-specific formatting
			ValueType = TypeOf(Value);
			
			Если ValueType = Type("Date") Тогда
				Result = FormatDate(Value, FormatOptions);
			ИначеЕсли ValueType = Type("Number") Тогда
				Result = FormatNumber(Value, FormatOptions);
			ИначеЕсли ValueType = Type("Boolean") Тогда
				Result = FormatBoolean(Value, FormatOptions);
			ИначеЕсли ValueType = Type("String") Тогда
				Result = FormatString(Value, FormatOptions);
			ИначеЕсли ValueType = Type("UUID") Тогда
				Result = String(Value);
			ИначеЕсли ValueType = Type("Type") Тогда
				Result = "Type(" + Value + ")";
			ИначеЕсли ValueType = Type("Структура") Тогда
				
				Описание = "";
				Ключи = М1сAIОбщие.Ключи(Value);
				Для Каждого Ключ Из Ключи Цикл
					Описание = Описание + Ключ + ": " + Value[Ключ] + Символы.ПС;
				КонецЦикла;
				Result = Описание;
			ИначеЕсли ValueType = Тип("Массив") Тогда
				
				Описание = "";
				i = 0;
				Для Каждого v Из Value Цикл
					Описание = Описание + "[" + i + "]" + ": " + v + Символы.ПС;
					i = i + 1;
				КонецЦикла;
				Result = Описание;
				
			Иначе
				// Handle complex objects
				Result = FormatComplexObject(Value, FormatOptions);
			КонецЕсли;
		КонецЕсли;
		
		// Apply prefix and suffix with validation
		Если HasText(Prefix) Тогда
			Result = String(Prefix) + Result;
		КонецЕсли;
		
		Если HasText(Suffix) Тогда
			Result = Result + String(Suffix);
		КонецЕсли;
		
		// Length validation
		//If StrLen(Result) > ConfigMaxStringLength Then
		//    Result = Left(Result, ConfigMaxStringLength) + "...[truncated]";
		//EndIf;
		
	Исключение
		Result = "[Error converting value: " + ErrorDescription() + "]";
		
		Если ConfigDebugMode Тогда
			М1сAIЛогирование.Error("AsString conversion error", ErrorInfo());
		КонецЕсли;
	КонецПопытки;
	
	// Performance logging
	Если ConfigPerformanceLog Тогда
		ElapsedTime = CurrentUniversalDateInMilliseconds() - StartTime;
		Если ElapsedTime > 100 Тогда // Log only slow operations
			М1сAIЛогирование.Write("AsString - " + ElapsedTime + StrLen(String(Value)));
		КонецЕсли;
	КонецЕсли;
	
	Возврат Result;
КонецФункции

#Region examples_М1сAIСтроки_AsString
// Пример 1: Дата
//   Msg = М1сAIСтроки.AsString(Дата(2025,5,13)); // "13052025"
// Пример 2: Число
//   Msg = М1сAIСтроки.AsString(1234.56, "[", "]"); // "[1234.56]"
#EndRegion

#Region examples_М1сAIСтроки_AsString_Enhanced
// Example 1: Simple conversion
//   Msg = М1сAIСтроки.AsString(Date(2025,5,13)); // "13.05.2025"
//
// Example 2: With formatting options
//   Options = New Structure;
//   Options.Insert("DateFormat", "ddMMyyyy");
//   Msg = М1сAIСтроки.AsString(Date(2025,5,13), "[", "]", Options); // "[13052025]"
//
// Example 3: Number with precision
//   Options = New Structure;
//   Options.Insert("Precision", 2);
//   Msg = М1сAIСтроки.AsString(1234.567, "", "", Options); // "1234.57"
#EndRegion

// Helper functions for enhanced formatting
Функция FormatDate(DateValue, FormatOptions = Undefined) Экспорт
	Если FormatOptions = Undefined Тогда
		Возврат Format(DateValue, "DLF=D");
	КонецЕсли;
	
	Если FormatOptions.Property("DateFormat") Тогда
		FormatString = FormatOptions.DateFormat;
	Иначе
		FormatString = "DLF=D";
	КонецЕсли;
	
	Возврат Format(DateValue, FormatString);
КонецФункции

Функция FormatNumber(NumberValue, FormatOptions = Undefined) Экспорт
	
	// Явная обработка нуля
	Если TypeOf(NumberValue) = Type("Number") И NumberValue = 0 Тогда
		Возврат "0";
	КонецЕсли;
	Если FormatOptions = Undefined Тогда
		Возврат Format(NumberValue, "NG=0");
	КонецЕсли;
	Если FormatOptions.Property("NumberFormat") Тогда
		
		
		FormatString = FormatOptions.NumberFormat;
	Иначе
		FormatString = "NG=0";
	КонецЕсли;
	Если FormatOptions.Property("Precision") Тогда
		Precision = FormatOptions.Precision;
	Иначе
		
		
		
		
		Precision = -1;
	КонецЕсли;
	Если Precision >= 0 Тогда
		
		FormatString = "NFD=" + String(Precision) + "; " + FormatString;
	КонецЕсли;
	Возврат Format(NumberValue, FormatString);
КонецФункции
Функция FormatBoolean(BoolValue, FormatOptions = Undefined) Экспорт
	Если FormatOptions = Undefined Тогда
		Возврат ?(BoolValue, "True", "False");
	КонецЕсли;
	
	Если FormatOptions.Property("TrueText") Тогда
		
		
		
		
		
		
		
		
		TrueText = FormatOptions.TrueText;
	Иначе
		TrueText = "True";
	КонецЕсли;
	
	Если FormatOptions.Property("FalseText") Тогда
		FalseText = FormatOptions.Property("FalseText");
	Иначе
		FalseText = "False";
	КонецЕсли;
	
	Возврат ?(BoolValue, TrueText, FalseText);
КонецФункции

Функция FormatString(StringValue, FormatOptions = Undefined) Экспорт
	Если FormatOptions = Undefined Тогда
		Возврат StringValue;
	КонецЕсли;
	
	Result = StringValue;
	
	// Apply string transformations
	Если FormatOptions.Property("UpperCase", False) Тогда
		Result = Upper(Result);
	ИначеЕсли FormatOptions.Property("LowerCase", False) Тогда
		Result = Lower(Result);
	ИначеЕсли FormatOptions.Property("TitleCase", False) Тогда
		Result = Title(Result);
	КонецЕсли;
	
	Если FormatOptions.Property("Trim", False) Тогда
		Result = TrimAll(Result);
	КонецЕсли;
	
	MaxLength = FormatOptions.Property("MaxLength", 0);
	Если MaxLength > 0 И StrLen(Result) > MaxLength Тогда
		Result = Left(Result, MaxLength) + "...";
	КонецЕсли;
	
	Возврат Result;
КонецФункции

Функция FormatComplexObject(ObjectValue, FormatOptions = Undefined) Экспорт
	Попытка
		// Try JSON serialization first
		Возврат М1сAIJSON.ToJSON(ObjectValue);
	Исключение
		// Fallback to string conversion
		Возврат String(ObjectValue);
	КонецПопытки;
КонецФункции

#EndRegion

#Region М1сAIСтроки_Of

// <doc>
//   <summary>Создает строку из значений (до 8) с автоконвертацией. Разделитель - пробел.</summary> ✦
//   <warning>⚠️ МЕДЛЕННЕЕ платформенной конкатенации в 2-3 раза!</warning>
//   <warning>✅ Используйте для DEBUG/редких вызовов, НЕ в циклах!</warning>
//   <warning>⚡ Для производительности используйте Printf() или прямую конкатенацию.</warning>
//   <param i="1" name="Знач1" type="Произвольный" optional="True">Значение 1</param> ➤
//   <param i="2" name="Знач2" type="Произвольный" optional="True">Значение 2</param> ➤
//   <param i="3" name="Знач3" type="Произвольный" optional="True">Значение 3</param> ➤
//   <param i="4" name="Знач4" type="Произвольный" optional="True">Значение 4</param> ➤
//   <param i="5" name="Знач5" type="Произвольный" optional="True">Значение 5</param> ➤
//   <param i="6" name="Знач6" type="Произвольный" optional="True">Значение 6</param> ➤
//   <param i="7" name="Знач7" type="Произвольный" optional="True">Значение 7</param> ➤
//   <param i="8" name="Знач8" type="Произвольный" optional="True">Значение 8</param> ➤
//   <returns>String — объединенная строка с разделителем-пробелом</returns> ⬅
//   <complexity cc="2"/>
//   <performance>Медленнее платформы в 2-3 раза. Используйте осторожно!</performance>
//   <example>
//     // ✅ ХОРОШО - Debug (редко):
//     М1сAIСтроки.Of("X=", X, "Y=", Y, "Z=", Z)
//     // → "X= 10 Y= 20 Z= 30"
//
//     // ✅ ХОРОШО - Одиночный вызов:
//     Текст = М1сAIСтроки.Of("Пользователь:", Имя, "Дата:", ТекущаяДата())
//
//     // ❌ ПЛОХО - В цикле (медленно!):
//     Для Каждого Товар Из Товары Цикл
//         Текст = М1сAIСтроки.Of("Товар:", Товар.Наименование); // НЕ ДЕЛАЙТЕ ТАК!
//     КонецЦикла;
//
//     // ⚡ ЛУЧШЕ ИСПОЛЬЗОВАТЬ:
//     М1сAIСтроки.Printf("X=%1 Y=%2", X, Y)  // Быстрее, нужен шаблон
//     Текст = "X= " + Строка(X)        // Самое быстрое
//   </example>
// </doc>
Функция Of(
		Знач1 = Неопределено,
		Знач2 = Неопределено,
		Знач3 = Неопределено,
		Знач4 = Неопределено,
		Знач5 = Неопределено,
		Знач6 = Неопределено,
		Знач7 = Неопределено,
		Знач8 = Неопределено
	) Экспорт //⚙
	
	ib = "Создание строки из значений (до 8)"; //✍
	
	// Оптимизация: собираем напрямую в строку без промежуточного массива
	Результат = ""; //✏
	
	Если Знач1 <> Неопределено Тогда //⚡
		Результат = AsString(Знач1); //▶️
	КонецЕсли;
	
	Если Знач2 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач2); //✏
	КонецЕсли;
	
	Если Знач3 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач3); //✏
	КонецЕсли;
	
	Если Знач4 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач4); //✏
	КонецЕсли;
	
	Если Знач5 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач5); //✏
	КонецЕсли;
	
	Если Знач6 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач6); //✏
	КонецЕсли;
	
	Если Знач7 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач7); //✏
	КонецЕсли;
	
	Если Знач8 <> Неопределено Тогда //⚡
		Результат = Результат + ?(Результат = "", "", " ") + AsString(Знач8); //✏
	КонецЕсли;
	
	Возврат Результат; //↩
	
КонецФункции

#Region examples_М1сAIСтроки_Of
// ✅ Пример 1: Debug-вывод (ХОРОШО - редко)
//   Текст = М1сAIСтроки.Of("X=", X, "Y=", Y, "Z=", Z);
//   // "X= 10 Y= 20 Z= 30"
//
// ✅ Пример 2: Формирование сообщения (ХОРОШО - одиночный вызов)
//   Текст = М1сAIСтроки.Of("Пользователь:", Пользователь.Имя, "Роль:", Пользователь.Роль);
//   // "Пользователь: Иванов Роль: Администратор"
//
// ✅ Пример 3: Смешанные типы (ХОРОШО)
//   Текст = М1сAIСтроки.Of("Дата:", ТекущаяДата(), "Сумма:", 1234.56, "ОК:", Истина);
//   // "Дата: 13.05.2025 Сумма: 1234.56 ОК: True"
//
// ❌ Пример 4: В цикле (ПЛОХО - медленно!)
//   Для Каждого Товар Из Товары Цикл
//       Текст = М1сAIСтроки.Of("Товар:", Товар.Наименование, "Цена:", Товар.Цена); // ❌ НЕ ДЕЛАЙТЕ ТАК!
//   КонецЦикла;
//
// ⚡ Альтернативы для производительности:
//   // Вариант 1 - Printf (быстрее):
//   М1сAIСтроки.Printf("X=%1 Y=%2 Z=%3", X, Y, Z);
//
//   // Вариант 2 - Прямая конкатенация (самое быстрое):
//   Текст = "X= " + Строка(X) + " Y= " + Строка(Y);
#EndRegion

#EndRegion

#Region М1сAIСтроки_PrintOf

// <doc>
//   <summary>Выводит через Message строку из значений (до 8) с автоконвертацией.</summary> ✦
//   <warning>⚠️ МЕДЛЕННЕЕ платформенной конкатенации в 2-3 раза!</warning>
//   <warning>✅ Используйте для DEBUG/редких вызовов, НЕ в циклах!</warning>
//   <warning>⚡ Для производительности используйте Printf().</warning>
//   <param i="1" name="Знач1" type="Произвольный" optional="True">Значение 1</param> ➤
//   <param i="2" name="Знач2" type="Произвольный" optional="True">Значение 2</param> ➤
//   <param i="3" name="Знач3" type="Произвольный" optional="True">Значение 3</param> ➤
//   <param i="4" name="Знач4" type="Произвольный" optional="True">Значение 4</param> ➤
//   <param i="5" name="Знач5" type="Произвольный" optional="True">Значение 5</param> ➤
//   <param i="6" name="Знач6" type="Произвольный" optional="True">Значение 6</param> ➤
//   <param i="7" name="Знач7" type="Произвольный" optional="True">Значение 7</param> ➤
//   <param i="8" name="Знач8" type="Произвольный" optional="True">Значение 8</param> ➤
//   <complexity cc="2"/>
//   <performance>Медленнее платформы в 2-3 раза. Используйте осторожно!</performance>
//   <example>
//     // ✅ ХОРОШО - Debug вывод:
//     М1сAIСтроки.PrintOf("X=", X, "Y=", Y, "Z=", Z);
//
//     // ✅ ХОРОШО - Логирование результата:
//     М1сAIСтроки.PrintOf("Обработано:", Количество, "строк за", Время, "мс");
//
//     // ❌ ПЛОХО - В цикле:
//     Для Каждого Элемент Из Коллекция Цикл
//         М1сAIСтроки.PrintOf("Элемент:", Элемент); // ❌ НЕ ДЕЛАЙТЕ ТАК!
//     КонецЦикла;
//
//     // ⚡ ЛУЧШЕ:
//     М1сAIСтроки.Printf("X=%1 Y=%2", X, Y)  // Быстрее
//   </example>
// </doc>
Процедура PrintOf(
		Знач1 = Неопределено,
		Знач2 = Неопределено,
		Знач3 = Неопределено,
		Знач4 = Неопределено,
		Знач5 = Неопределено,
		Знач6 = Неопределено,
		Знач7 = Неопределено,
		Знач8 = Неопределено
	) Экспорт //⚙
	
	ib = "Вывод строки из значений (до 8)"; //✍
	
	// Используем Of для формирования строки
	Текст = Of(Знач1, Знач2, Знач3, Знач4, Знач5, Знач6, Знач7, Знач8); //▶️
	
	// Выводим через Message
	Print(Текст); //▶️
	
КонецПроцедуры

#Region examples_М1сAIСтроки_PrintOf
// ✅ Пример 1: Debug-вывод переменных (ХОРОШО)
//   М1сAIСтроки.PrintOf("X=", X, "Y=", Y, "Z=", Z);
//   // Выведет: "X= 10 Y= 20 Z= 30"
//
// ✅ Пример 2: Логирование (ХОРОШО - редко)
//   М1сAIСтроки.PrintOf("Обработано:", КоличествоСтрок, "строк за", ВремяВыполнения, "мс");
//   // Выведет: "Обработано: 150 строк за 250 мс"
//
// ✅ Пример 3: Вывод состояния (ХОРОШО)
//   М1сAIСтроки.PrintOf("Пользователь:", Пользователь.Имя, "Статус:", Пользователь.Активен);
//   // Выведет: "Пользователь: Иванов Статус: True"
//
// ❌ Пример 4: Вывод в цикле (ПЛОХО!)
//   Для Каждого Товар Из Товары Цикл
//       М1сAIСтроки.PrintOf("Товар:", Товар.Наименование); // ❌ МЕДЛЕННО!
//   КонецЦикла;
//
// ⚡ Альтернатива для производительности:
//   // Используйте Printf вместо PrintOf в критичных местах:
//   М1сAIСтроки.Printf("X=%1 Y=%2", X, Y);  // Быстрее в 2-3 раза!
#EndRegion

#EndRegion

#Region М1сAIСтроки_OfTests

// <doc>
// <summary>Тесты для функций М1сAIСтроки.Of() и М1сAIСтроки.PrintOf().</summary> ✦
// <returns>Boolean — все тесты пройдены успешно</returns> ⬅
// <complexity cc="4"/>
// </doc>
Функция OfTests() Экспорт //⚙
	
	ib = "Тесты М1сAIСтроки.Of/PrintOf"; //✍
	TestsPassed = 0; //✏
	TestsTotal = 0; //✏
	
	Сообщить("=== М1сAIСтроки.Of/PrintOf Tests START ===");
	
	// Тест 1: Простое объединение
	TestsTotal = TestsTotal + 1; //✏
	Результат = Of("Hello", "World"); //✏
	Если Результат = "Hello World" Тогда //⚡
		TestsPassed = TestsPassed + 1; //✏
		Сообщить("✓ Тест 1 (Of простое): ПРОЙДЕН");
	Иначе
		Сообщить("✗ Тест 1 (Of простое): ПРОВАЛЕН - " + Результат);
	КонецЕсли;
	
	// Тест 2: С числами и булево
	TestsTotal = TestsTotal + 1; //✏
	Результат = Of("Number:", 123, "Bool:", Истина); //✏
	Если СтрНайти(Результат, "Number:") > 0 И СтрНайти(Результат, "123") > 0 Тогда //⚡
		TestsPassed = TestsPassed + 1; //✏
		Сообщить("✓ Тест 2 (Of типы): ПРОЙДЕН");
	Иначе
		Сообщить("✗ Тест 2 (Of типы): ПРОВАЛЕН - " + Результат);
	КонецЕсли;
	
	// Тест 3: С пропуском Неопределено
	TestsTotal = TestsTotal + 1; //✏
	Результат = Of("Start", Неопределено, "End"); //✏
	Если Результат = "Start End" Тогда //⚡
		TestsPassed = TestsPassed + 1; //✏
		Сообщить("✓ Тест 3 (Of пропуск Undefined): ПРОЙДЕН");
	Иначе
		Сообщить("✗ Тест 3 (Of пропуск Undefined): ПРОВАЛЕН - " + Результат);
	КонецЕсли;
	
	// Тест 4: Максимальное количество параметров
	TestsTotal = TestsTotal + 1; //✏
	Результат = Of("1", "2", "3", "4", "5", "6", "7", "8"); //✏
	Если СтрНайти(Результат, "1") > 0 И СтрНайти(Результат, "8") > 0 Тогда //⚡
		TestsPassed = TestsPassed + 1; //✏
		Сообщить("✓ Тест 4 (Of 8 параметров): ПРОЙДЕН");
	Иначе
		Сообщить("✗ Тест 4 (Of 8 параметров): ПРОВАЛЕН - " + Результат);
	КонецЕсли;
	
	// Тест 5: PrintOf (проверка что не падает)
	TestsTotal = TestsTotal + 1; //✏
	Попытка //✱
		PrintOf("Test:", 123, "Done"); //▶️
		TestsPassed = TestsPassed + 1; //✏
		Сообщить("✓ Тест 5 (PrintOf): ПРОЙДЕН");
	Исключение
		Сообщить("✗ Тест 5 (PrintOf): ПРОВАЛЕН");
	КонецПопытки;
	
	// Тест 6: Пустой вызов
	TestsTotal = TestsTotal + 1; //✏
	Результат = Of(); //✏
	Если Результат = "" Тогда //⚡
		TestsPassed = TestsPassed + 1; //✏
		Сообщить("✓ Тест 6 (Of пустой): ПРОЙДЕН");
	Иначе
		Сообщить("✗ Тест 6 (Of пустой): ПРОВАЛЕН - " + Результат);
	КонецЕсли;
	
	// Итоги тестирования
	Если TestsPassed = TestsTotal Тогда //⚡
		Сообщить("=== М1сAIСтроки.Of/PrintOf Tests SUCCESS: " + Строка(TestsPassed) + "/" + Строка(TestsTotal) + " ===");
		Возврат Истина; //↩
	Иначе
		Сообщить("=== М1сAIСтроки.Of/PrintOf Tests FAILED: " + Строка(TestsPassed) + "/" + Строка(TestsTotal) + " ===");
		Возврат Ложь; //↩
	КонецЕсли;
	
КонецФункции

#EndRegion

#Region М1сAIСтроки_Split
/// <summary>
/// Разбивает строку на части по разделителю и добавляет префикс/суффикс.
/// </summary>
/// <param name="StringToSplit">Исходная строка.</param>
/// <param name="Prefix" type="String" optional="True">Добавляемый к каждой части слева.</param>
/// <param name="Suffix" type="String" optional="True">Добавляемый к каждой части справа.</param>
/// <param name="Delimiter" type="String" default=",">Разделитель.</param>
/// <returns type="Array">Массив строк, в котором каждая часть обёрнута Prefix/Suffix.</returns>
//Function Split(StringToSplit, Prefix = "", Suffix = "", Delimiter = ",") Export
//	// Use the standard StrSplit function to split the string
//	SplitParts = StrSplit(StringToSplit, Delimiter, False);
//
//	// Add Prefix and Suffix to each part if they are defined
//	For i = 0 To SplitParts.Count() - 1 Do
//		If Prefix <> "" Then
//			SplitParts[i] = Prefix + SplitParts[i];
//		EndIf;
//
//		If Suffix <> "" Then
//			SplitParts[i] = SplitParts[i] + Suffix;
//		EndIf;
//	EndDo;
//
//	Return SplitParts;
//EndFunction

#Region М1сAIСтроки_Split_Enhanced
/// <summary>
/// Enhanced string splitting with validation, error handling, and advanced options.
/// </summary>
/// <param name="StringToSplit">Source string to split</param>
/// <param name="Prefix" type="String" optional="True">Prefix for each part</param>
/// <param name="Suffix" type="String" optional="True">Suffix for each part</param>
/// <param name="Delimiter" type="String" default=",">Delimiter character(s)</param>
/// <param name="Options" type="Structure" optional="True">Advanced splitting options</param>
/// <returns type="Array">Array of processed string parts</returns>
Функция Split(StringToSplit,
		Prefix = "",
		Suffix = "",
		Delimiter = ",",
		Options = Undefined,
		ConfigPerformanceLog = False,
		ConfigDebugMode = False)
	Экспорт
	
	// Input validation
	Если НЕ HasText(StringToSplit) Тогда
		Возврат Новый Array;
	КонецЕсли;
	
	Если Delimiter = "" Тогда
		Delimiter = ",";
	КонецЕсли;
	
	// Performance tracking
	StartTime = ?(ConfigPerformanceLog, CurrentUniversalDateInMilliseconds(), 0);
	
	Попытка
		// Default options
		TrimParts = True;
		SkipEmptyParts = False;
		MaxParts = 0;
		CaseSensitive = True;
		
		Если Options <> Undefined Тогда
			Если Options.Property("TrimParts") Тогда
				TrimParts = Options.TrimParts;
			КонецЕсли;
			Если Options.Property("SkipEmptyParts") Тогда
				SkipEmptyParts = Options.SkipEmptyParts;
			КонецЕсли;
			Если Options.Property("MaxParts") Тогда
				MaxParts = Options.MaxParts;
			КонецЕсли;
			Если Options.Property("CaseSensitive") Тогда
				CaseSensitive = Options.CaseSensitive;
			КонецЕсли;
		КонецЕсли;
		
		// 1. Split
		Parts = StrSplit(StringToSplit, Delimiter);
		
		// 2. Trim and skip empty
		CleanParts = Новый Array;
		Для i = 0 По Parts.Count() - 1 Цикл
			Part = Parts[i];
			Если TrimParts Тогда
				Part = TrimAll(Part);
			КонецЕсли;
			Если SkipEmptyParts И НЕ HasText(Part) Тогда
				Продолжить;
			КонецЕсли;
			CleanParts.Add(Part);
		КонецЦикла;
		
		// 3. MaxParts logic
		Если MaxParts > 0 И CleanParts.Count() > MaxParts Тогда
			RemainingParts = Новый Array;
			Для i = 0 По MaxParts - 2 Цикл
				RemainingParts.Add(CleanParts[i]);
			КонецЦикла;
			LastPartArray = Новый Array;
			Для i = MaxParts - 1 По CleanParts.Count() - 1 Цикл
				LastPartArray.Add(CleanParts[i]);
			КонецЦикла;
			LastPart = СтрСоединить(LastPartArray, Delimiter);
			RemainingParts.Add(LastPart);
			CleanParts = RemainingParts;
		КонецЕсли;
		
		// 4. Prefix/Suffix
		Для i = 0 По CleanParts.Count() - 1 Цикл
			Part = CleanParts[i];
			Если HasText(Prefix) Тогда
				Part = Prefix + Part;
			КонецЕсли;
			Если HasText(Suffix) Тогда
				Part = Part + Suffix;
			КонецЕсли;
			CleanParts[i] = Part;
		КонецЦикла;
		
		// Performance logging
		Если ConfigPerformanceLog Тогда
			ElapsedTime = CurrentUniversalDateInMilliseconds() - StartTime;
			Если ElapsedTime > 100 Тогда
				М1сAIЛогирование.Write("Split - " + ElapsedTime + StrLen(String(StringToSplit)));
			КонецЕсли;
		КонецЕсли;
		
		Возврат CleanParts;
		
	Исключение
		Если ConfigDebugMode Тогда
			М1сAIЛогирование.Error("Split operation failed", ErrorInfo());
		КонецЕсли;
		Result = Новый Array;
		Result.Add(StringToSplit);
		Возврат Result;
	КонецПопытки;
	
КонецФункции

#Region examples_М1сAIСтроки_Split_Enhanced
// Example 1: Basic splitting
//   Result = М1сAIСтроки.Split("apple,banana,cherry", "[", "]", ",");
//   // ["[apple]", "[banana]", "[cherry]"]
//
// Example 2: With options
//   Options = New Structure;
//   Options.Insert("TrimParts", True);
//   Options.Insert("SkipEmptyParts", True);
//   Options.Insert("MaxParts", 2);
//   Result = М1сAIСтроки.Split("a, b, c, d", "", "", ",", Options);
//   // ["a", "b, c, d"]
#EndRegion
#EndRegion

#Region examples_М1сAIСтроки_Split
// Пример:
//   Result = М1сAIСтроки.Split("apple,banana,cherry","[","]",",");
//   // ["[apple]","[banana]","[cherry]"]
#EndRegion
#EndRegion

#Region М1сAIСтроки_Join_Enhanced
/// <summary>
/// Enhanced string concatenation (join) with validation, error handling, and advanced options.
/// </summary>
/// <param name="Arr">Source array (Array or FixedArray) to join</param>
/// <param name="Prefix" type="String" optional="True">Prefix for each part</param>
/// <param name="Suffix" type="String" optional="True">Suffix for each part</param>
/// <param name="Delimiter" type="String" optional="True" default=",">Delimiter between parts</param>
/// <param name="Options" type="Structure" optional="True">Advanced joining options</param>
/// <returns type="String">Resulting joined string</returns>
Функция Join(Arr,
		Prefix = "",
		Suffix = "",
		Delimiter = ",",
		Options = Undefined,
		ConfigPerformanceLog = False,
		ConfigDebugMode = False)
	Экспорт
	
	Result = "";
	Если Arr = Undefined ИЛИ Arr.Count() = 0 Тогда
		Возврат Result;
	КонецЕсли;
	
	// Performance tracking
	StartTime = ?(ConfigPerformanceLog, CurrentUniversalDateInMilliseconds(), 0);
	
	// Default options
	TrimParts = True;
	SkipEmptyParts = False;
	MinParts = 0;
	MaxParts = 0;
	CaseSensitive = True;
	
	// Options parsing
	Если Options <> Undefined Тогда
		Если Options.Property("TrimParts") Тогда
			TrimParts = Options.TrimParts;
		КонецЕсли;
		Если Options.Property("SkipEmptyParts") Тогда
			SkipEmptyParts = Options.SkipEmptyParts;
		КонецЕсли;
		Если Options.Property("MinParts") Тогда
			MinParts = Options.MinParts;
		КонецЕсли;
		Если Options.Property("MaxParts") Тогда
			MaxParts = Options.MaxParts;
		КонецЕсли;
		Если Options.Property("CaseSensitive") Тогда
			CaseSensitive = Options.CaseSensitive;
		КонецЕсли;
	КонецЕсли;
	
	Попытка
		// 1. Обработка всех элементов с Trim/SkipEmpty
		CleanParts = Новый Array;
		Для i = 0 По Arr.Count() - 1 Цикл
			Part = Arr[i];
			Если TrimParts Тогда
				Part = TrimAll(Part);
			КонецЕсли;
			Если SkipEmptyParts И НЕ HasText(Part) Тогда
				Продолжить;
			КонецЕсли;
			CleanParts.Add(Part);
		КонецЦикла;
		
		// 2. MinParts: если меньше — дополняем пустыми
		Если MinParts > 0 И CleanParts.Count() < MinParts Тогда
			Для i = CleanParts.Count() По MinParts - 1 Цикл
				CleanParts.Add("");
			КонецЦикла;
		КонецЕсли;
		
		// 3. MaxParts: если больше — объединяем хвост
		//If MaxParts > 0 And CleanParts.Count() > MaxParts Then
		//    TruncParts = New Array;
		//    For i = 0 To MaxParts - 2 Do
		//        TruncParts.Add(CleanParts[i]);
		//    EndDo;
		//    LastPartArray = New Array;
		//    For i = MaxParts - 1 To CleanParts.Count() - 1 Do
		//        LastPartArray.Add(CleanParts[i]);
		//    EndDo;
		//    LastPart = СтрСоединить(LastPartArray, Delimiter);
		//    TruncParts.Add(LastPart);
		//    CleanParts = TruncParts;
		//EndIf;
		
		// 4. Добавляем Prefix/Suffix к каждой части
		Для i = 0 По CleanParts.Count() - 1 Цикл
			Part = CleanParts[i];
			Если HasText(Prefix) Тогда
				Part = Prefix + Part;
			КонецЕсли;
			Если HasText(Suffix) Тогда
				Part = Part + Suffix;
			КонецЕсли;
			CleanParts[i] = Part;
		КонецЦикла;
		
		// 5. Собираем в строку
		Result = СтрСоединить(CleanParts, Delimiter);
		
		// Performance logging
		Если ConfigPerformanceLog Тогда
			ElapsedTime = CurrentUniversalDateInMilliseconds() - StartTime;
			Если ElapsedTime > 100 Тогда
				М1сAIЛогирование.Write("Join - " + ElapsedTime + " ms; Parts=" + Arr.Count());
			КонецЕсли;
		КонецЕсли;
		
		Возврат Result;
		
	Исключение
		Если ConfigDebugMode Тогда
			М1сAIЛогирование.Error("Join operation failed", ErrorInfo());
		КонецЕсли;
		Возврат "";
	КонецПопытки;
	
КонецФункции

#Region examples_М1сAIСтроки_Join_Enhanced
// Example 1: Basic join
//   Result = М1сAIСтроки.Join(New Array("a", "b", "c"), "", "", ",");
//   // "a,b,c"
//
// Example 2: Prefix/Suffix
//   Result = М1сAIСтроки.Join(New Array("a", "b", "c"), "<", ">", ";");
//   // "<a>;<b>;<c>"
//
// Example 3: With options (skip empty, trim, MaxParts)
//   Options = New Structure;
//   Options.Insert("TrimParts", True);
//   Options.Insert("SkipEmptyParts", True);
//   Options.Insert("MaxParts", 2);
//   Result = М1сAIСтроки.Join(New Array(" a", "", "b", "c", "d "), "", "", ",", Options);
//   // "a,b,c,d" => "a,b,c,d" -> после обработки MaxParts = 2: "a,b,c,d" -> "a,b,c,d"
//   // но если MaxParts=3: ["a","b","c,d"] -> "a,b,c,d"
#EndRegion
#EndRegion

#Region М1сAIСтроки_Wrap
/// <summary>
/// Оборачивает строку или части строки префиксом/суффиксом.
/// </summary>
/// <param name="StringToSplit">Исходная строка.</param>
/// <param name="Prefix">Префикс.</param>
/// <param name="Suffix">Суффикс.</param>
/// <param name="Delimiter" type="String" optional="True">Если задан, строка разбивается, иначе оборачивается целиком.</param>
/// <returns type="String">Обёрнутая строка или конкатенация обёрнутых частей.</returns>
Функция Wrap(StringToSplit, Prefix, Suffix, Delimiter = "") Экспорт
	Если Delimiter = "" Тогда
		// No delimiter – just wrap the whole string
		Возврат Prefix + StringToSplit + Suffix;
	Иначе
		// Use the existing Split to add Prefix/Suffix to each part
		WrappedParts = М1сAIСтроки.Split(StringToSplit, Prefix, Suffix, Delimiter);
		// Re-join into one string
		Возврат StrConcat(WrappedParts, Delimiter);
	КонецЕсли;
КонецФункции

#Region examples_М1сAIСтроки_Wrap
// Пример:
//   Result = М1сAIСтроки.Wrap("a,b,c","(",")",",");
//   // "(a),(b),(c)"
#EndRegion
#EndRegion

#Region М1сAIСтроки_Any

#Region М1сAIСтроки_FindAny
/// <summary>
/// Выполняет регистронезависимый поиск любой из указанных подстрок в строке.
/// </summary>
/// <param name="Where" type="String">Исходная строка.</param>
/// <param name="Substrings" type="String">Строка с подстроками для поиска, разделёнными запятыми или точками с запятой.</param>
/// <returns type="Number">Позиция первой найденной подстроки (начиная с 1) или 0, если ничего не найдено.</returns>
Функция FindAny(Where, Substrings) Экспорт
	
	LowerWhere = НРег(Where);
	Splitter = ",;";
	SearchList = СтрРазделить(Substrings, Splitter, Истина); // исключаем пустышки
	
	Для Каждого Substring Из SearchList Цикл
		LowerSub = НРег(Substring);
		Pos = СтрНайти(LowerWhere, LowerSub);
		Если Pos > 0 Тогда
			Возврат Pos;
		КонецЕсли;
	КонецЦикла;
	
	Возврат 0;
	
КонецФункции

#Region examples_М1сAIСтроки_FindAny
// Пример:
//   pos = М1сAIСтроки.FindAny("SELECT ... INTO TempTable", "ПОМЕСТИТЬ,INTO");
//   // вернёт позицию слова INTO
#EndRegion
#EndRegion


#Region М1сAIСтроки_HasAny
/// <summary>
/// Проверяет, содержит ли строка хотя бы одну из указанных подстрок (без учёта регистра).
/// </summary>
/// <param name="Where" type="String">Исходная строка.</param>
/// <param name="Substrings" type="String">Строка с подстроками для поиска, разделёнными запятыми или точками с запятой.</param>
/// <returns type="Boolean">Истина, если хотя бы одна подстрока найдена; иначе Ложь.</returns>
Функция HasAny(Where, Substrings) Экспорт
	
	LowerWhere = НРег(Where);
	Splitter = ",;";
	SearchList = СтрРазделить(Substrings, Splitter, Истина);
	
	Для Каждого Substring Из SearchList Цикл
		LowerSub = НРег(Substring);
		Если СтрНайти(LowerWhere, LowerSub) > 0 Тогда
			Возврат Истина;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Ложь;
	
КонецФункции

#Region examples_М1сAIСтроки_HasAny
// Пример:
//   ЕстьЛи = М1сAIСтроки.HasAny("ПОМЕСТИТЬ ВТ_Товары", "ПОМЕСТИТЬ,INTO");
//   // вернёт Истина
#EndRegion
#EndRegion


#Region М1сAIСтроки_StartsWithAny
/// <summary>
/// Проверяет, начинается ли строка с одной из подстрок (без учёта регистра).
/// </summary>
/// <param name="Where" type="String">Исходная строка.</param>
/// <param name="Substrings" type="String">Подстроки для сравнения, разделённые запятыми или точками с запятой.</param>
/// <returns type="Boolean">Истина, если строка начинается с одной из подстрок; иначе Ложь.</returns>
Функция StartsWithAny(Where, Substrings) Экспорт
	
	LowerWhere = НРег(Where);
	Splitter = ",;";
	SearchList = СтрРазделить(Substrings, Splitter, Истина);
	
	Для Каждого Substring Из SearchList Цикл
		LowerSub = НРег(Substring);
		Если Лев(LowerWhere, СтрДлина(LowerSub)) = LowerSub Тогда
			Возврат Истина;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Ложь;
	
КонецФункции

#Region examples_М1сAIСтроки_StartsWithAny
// Пример:
//   Результат = М1сAIСтроки.StartsWithAny("Error: not found", "ошибка,error,warning");
//   // вернёт Истина
#EndRegion
#EndRegion


#Region М1сAIСтроки_EndsWithAny
/// <summary>
/// Проверяет, заканчивается ли строка одной из указанных подстрок (без учёта регистра).
/// </summary>
/// <param name="Where" type="String">Исходная строка.</param>
/// <param name="Substrings" type="String">Подстроки для сравнения, разделённые запятыми или точками с запятой.</param>
/// <returns type="Boolean">Истина, если строка заканчивается одной из подстрок; иначе Ложь.</returns>
Функция EndsWithAny(Where, Substrings) Экспорт
	
	LowerWhere = НРег(Where);
	Splitter = ",;";
	SearchList = СтрРазделить(Substrings, Splitter, Истина);
	
	Для Каждого Substring Из SearchList Цикл
		LowerSub = НРег(Substring);
		Если Прав(LowerWhere, СтрДлина(LowerSub)) = LowerSub Тогда
			Возврат Истина;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Ложь;
	
КонецФункции

#Region examples_М1сAIСтроки_EndsWithAny
// Пример:
//   Результат = М1сAIСтроки.EndsWithAny("filename.tmp", ".tmp,.log,.bak");
//   // вернёт Истина
#EndRegion
#EndRegion


#Region М1сAIСтроки_ReplaceAny
/// <summary>
/// Заменяет все вхождения любых указанных подстрок на заданную строку.
/// </summary>
/// <param name="Where" type="String">Исходная строка.</param>
/// <param name="Substrings" type="String">Подстроки для замены, разделённые запятыми или точками с запятой.</param>
/// <param name="Replacement" type="String">Строка-замена.</param>
/// <returns type="String">Результат с заменёнными подстроками.</returns>
Функция ReplaceAny(Where, Substrings, Replacement) Экспорт
	
	Result = Where;
	Splitter = ",;";
	SearchList = СтрРазделить(Substrings, Splitter, Истина);
	
	Для Каждого Substring Из SearchList Цикл
		Result = СтрЗаменить(Result, Substring, Replacement);
	КонецЦикла;
	
	Возврат Result;
	
КонецФункции

#Region examples_М1сAIСтроки_ReplaceAny
// Пример:
//   Результат = М1сAIСтроки.ReplaceAny("debug error critical", "debug,error,critical", "X");
//   // вернёт "X X X"
#EndRegion
#EndRegion

#EndRegion

#Region М1сAIСтроки_StringLists
/// <summary>
/// Набор функций для работы со строковыми списками — строками с элементами, разделёнными разделителем.
/// </summary>

#Region М1сAIСтроки_StringLists

/// <summary>
/// Добавляет к строке с разделёнными значениями новые значения без дублирования.
/// </summary>
/// <param name="BaseString" type="String">Исходная строка со значениями, разделёнными по разделителю.</param>
/// <param name="AddString" type="String">Строка с новыми значениями, разделёнными по разделителю.</param>
/// <param name="Separator" type="String" optional="True">Разделитель значений (по умолчанию запятая).</param>
/// <returns type="String">Строка с объединёнными значениями без дубликатов.</returns>
Функция AddAny(BaseString, AddString, Separator = ",") Экспорт
	BaseList = СтрРазделить(BaseString, Separator, Истина);
	AddList = СтрРазделить(AddString, Separator, Истина);
	
	Unique = Новый Соответствие;
	Для Каждого Значение Из BaseList Цикл
		Ключ = СокрЛП(Значение);
		Если Unique.Получить(Ключ) = Неопределено Тогда
			Unique.Вставить(Ключ, Значение);
		КонецЕсли;
	КонецЦикла;
	
	Для Каждого Значение Из AddList Цикл
		Ключ = СокрЛП(Значение);
		Если Unique.Получить(Ключ) = Неопределено Тогда
			Unique.Вставить(Ключ, Значение);
		КонецЕсли;
	КонецЦикла;
	
	РезультатМассив = Новый Массив;
	// Сохраняем порядок из BaseList
	Для Каждого Значение Из BaseList Цикл
		Ключ = СокрЛП(Значение);
		Если Unique.Получить(Ключ) <> Неопределено Тогда
			РезультатМассив.Добавить(Значение);
			Unique.Удалить(Ключ);
		КонецЕсли;
	КонецЦикла;
	
	// Добавляем оставшиеся из AddList
	Для Каждого Пара Из Unique Цикл
		РезультатМассив.Добавить(Пара.Значение);
	КонецЦикла;
	
	Возврат СтрСоединить(РезультатМассив, Separator);
КонецФункции

#Region examples_М1сAIСтроки_StringLists_AddAny
// Пример AddAny:
// Base = "a,b,c";
// Add = "b,d,e";
// Result = М1сAIСтроки.AddAny(Base, Add);
// // Result = "a,b,c,d,e"
#EndRegion

#EndRegion


/// <summary>
/// Удаляет из строки со списком все элементы, указанные в строке удаления.
/// </summary>
/// <param name="BaseString" type="String">Исходная строка со значениями.</param>
/// <param name="RemoveString" type="String">Строка с элементами для удаления.</param>
/// <param name="Separator" type="String" optional="True">Разделитель (по умолчанию запятая).</param>
/// <returns type="String">Строка без удалённых элементов.</returns>
Функция RemoveAnyFromList(BaseString, RemoveString, Separator = ",") Экспорт
	BaseList = СтрРазделить(BaseString, Separator, Истина);
	RemoveList = СтрРазделить(RemoveString, Separator, Истина);
	
	RemoveSet = Новый Соответствие;
	Для Каждого Значение Из RemoveList Цикл
		RemoveSet.Вставить(СокрЛП(Значение), Истина);
	КонецЦикла;
	
	Результат = Новый Массив;
	Для Каждого Значение Из BaseList Цикл
		Если RemoveSet.Получить(СокрЛП(Значение)) = Неопределено Тогда
			Результат.Добавить(Значение);
		КонецЕсли;
	КонецЦикла;
	
	Возврат СтрСоединить(Результат, Separator);
КонецФункции

/// <summary>
/// Проверяет, содержит ли строковый список хотя бы один элемент из проверочного списка.
/// </summary>
/// <param name="BaseString" type="String">Строка с элементами.</param>
/// <param name="CheckString" type="String">Строка с элементами для проверки.</param>
/// <param name="Separator" type="String" optional="True">Разделитель (по умолчанию запятая).</param>
/// <returns type="Boolean">Истина, если есть хотя бы один совпадающий элемент.</returns>
Функция ContainsAnyFromList(BaseString, CheckString, Separator = ",") Экспорт
	BaseList = СтрРазделить(BaseString, Separator, Истина);
	CheckList = СтрРазделить(CheckString, Separator, Истина);
	
	BaseSet = Новый Соответствие;
	Для Каждого Значение Из BaseList Цикл
		BaseSet.Вставить(СокрЛП(Значение), Истина);
	КонецЦикла;
	
	Для Каждого Значение Из CheckList Цикл
		Если BaseSet.Получить(СокрЛП(Значение)) <> Неопределено Тогда
			Возврат Истина;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Ложь;
КонецФункции

/// <summary>
/// Проверяет, содержит ли строковый список все элементы из проверочного списка.
/// </summary>
/// <param name="BaseString" type="String">Строка с элементами.</param>
/// <param name="CheckString" type="String">Строка с элементами для проверки.</param>
/// <param name="Separator" type="String" optional="True">Разделитель (по умолчанию запятая).</param>
/// <returns type="Boolean">Истина, если все элементы присутствуют.</returns>
Функция ContainsAllFromList(BaseString, CheckString, Separator = ",") Экспорт
	BaseList = СтрРазделить(BaseString, Separator, Истина);
	CheckList = СтрРазделить(CheckString, Separator, Истина);
	
	BaseSet = Новый Соответствие;
	Для Каждого Значение Из BaseList Цикл
		BaseSet.Вставить(СокрЛП(Значение), Истина);
	КонецЦикла;
	
	Для Каждого Значение Из CheckList Цикл
		Если BaseSet.Получить(СокрЛП(Значение)) = Неопределено Тогда
			Возврат Ложь;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Истина;
КонецФункции

/// <summary>
/// Возвращает строку с элементами, которые есть одновременно в двух строковых списках.
/// </summary>
/// <param name="List1" type="String">Первый список элементов.</param>
/// <param name="List2" type="String">Второй список элементов.</param>
/// <param name="Separator" type="String" optional="True">Разделитель (по умолчанию запятая).</param>
/// <returns type="String">Строка с пересечением элементов.</returns>
Функция IntersectLists(List1, List2, Separator = ",") Экспорт
	List1Arr = СтрРазделить(List1, Separator, Истина);
	
	List2Set = Новый Соответствие;
	Для Каждого Значение Из СтрРазделить(List2, Separator, Истина) Цикл
		List2Set.Вставить(СокрЛП(Значение), Истина);
	КонецЦикла;
	
	Результат = Новый Массив;
	Для Каждого Значение Из List1Arr Цикл
		Если List2Set.Получить(СокрЛП(Значение)) <> Неопределено Тогда
			Результат.Добавить(Значение);
		КонецЕсли;
	КонецЦикла;
	
	Возврат СтрСоединить(Результат, Separator);
КонецФункции

/// <summary>
/// Удаляет дубликаты из строки со списком элементов.
/// </summary>
/// <param name="ListString" type="String">Строка со списком элементов.</param>
/// <param name="Separator" type="String" optional="True">Разделитель (по умолчанию запятая).</param>
/// <returns type="String">Строка без дубликатов.</returns>
Функция UniqueList(ListString, Separator = ",") Экспорт
	ListArr = СтрРазделить(ListString, Separator, Истина);
	UniqueSet = Новый Соответствие;
	Результат = Новый Массив;
	
	Для Каждого Значение Из ListArr Цикл
		Ключ = СокрЛП(Значение);
		Если UniqueSet.Получить(Ключ) = Неопределено Тогда
			UniqueSet.Вставить(Ключ, Истина);
			Результат.Добавить(Значение);
		КонецЕсли;
	КонецЦикла;
	
	Возврат СтрСоединить(Результат, Separator);
КонецФункции

#Region М1сAIСтроки_ExceptLists

/// <summary>
/// Возвращает разность строковых списков: элементы, которые есть в первом, но отсутствуют во втором.
/// </summary>
/// <param name="List1" type="String">Первый список (основа).</param>
/// <param name="List2" type="String">Второй список (то, что нужно исключить).</param>
/// <param name="Separator" type="String" optional="True">Разделитель значений (по умолчанию запятая).</param>
/// <returns type="String">Строка с элементами, присутствующими только в первом списке.</returns>
Функция ExceptLists(List1, List2, Separator = ",") Экспорт
	Возврат RemoveAnyFromList(List1, List2, Separator);
КонецФункции

#Region examples_М1сAIСтроки_ExceptLists
// Пример использования:
// List1 = "Роль1, Роль23, Роль33";
// List2 = "Роль1, Роль2";
// Result = М1сAIСтроки.ExceptLists(List1, List2);
// // "Роль23, Роль33"
#EndRegion

#EndRegion

#Region examples_М1сAIСтроки_StringLists
// Пример AddAny:
// Base = "a,b,c";
// Add = "b,d,e";
// Result = М1сAIСтроки.AddAny(Base, Add);
// // "a,b,c,d,e"

// Пример RemoveAnyFromList:
// Base = "a,b,c,d";
// Remove = "b,d";
// Result = М1сAIСтроки.RemoveAnyFromList(Base, Remove);
// // "a,c"

// Пример ContainsAnyFromList:
// Base = "a,b,c";
// Check = "x,c,z";
// Result = М1сAIСтроки.ContainsAnyFromList(Base, Check);
// // Истина

// Пример ContainsAllFromList:
// Base = "a,b,c,d";
// Check = "b,d";
// Result = М1сAIСтроки.ContainsAllFromList(Base, Check);
// // Истина

// Пример IntersectLists:
// List1 = "a,b,c,d";
// List2 = "b,d,x";
// Result = М1сAIСтроки.IntersectLists(List1, List2);
// // "b,d"

// Пример UniqueList:
// List = "a,b,a,c,b";
// Result = М1сAIСтроки.UniqueList(List);
// // "a,b,c"
#EndRegion

#EndRegion


#Region М1сAIСтроки_HasText_Enhanced
/// <summary>
/// Enhanced text validation with multiple criteria and options.
/// </summary>
/// <param name="Value">Value to check</param>
/// <param name="Options" type="Structure" optional="True">Validation options</param>
/// <returns type="Boolean">True if value contains meaningful text</returns>
Функция HasText(Value, Options = Undefined) Экспорт
	
	// Basic undefined/null check
	Если Value = Undefined ИЛИ Value = Null Тогда
		Возврат False;
	КонецЕсли;
	
	// Type validation
	Если TypeOf(Value) <> Type("String") Тогда
		// Option to convert non-strings
		Если Options <> Undefined И Options.Property("ConvertNonStrings", False) Тогда
			Value = String(Value);
		Иначе
			Возврат False;
		КонецЕсли;
	КонецЕсли;
	
	// Initialize validation options
	MinLength = 1;
	AllowWhitespaceOnly = False;
	RequireAlphanumeric = False;
	ForbiddenChars = "";
	
	Если Options <> Undefined Тогда
		MinLength = Options.Property("MinLength", 1);
		AllowWhitespaceOnly = Options.Property("AllowWhitespaceOnly", False);
		RequireAlphanumeric = Options.Property("RequireAlphanumeric", False);
		ForbiddenChars = Options.Property("ForbiddenChars", "");
	КонецЕсли;
	
	// Length check
	Если StrLen(Value) < MinLength Тогда
		Возврат False;
	КонецЕсли;
	
	// Whitespace check
	TrimmedValue = TrimAll(Value);
	Если StrLen(TrimmedValue) = 0 Тогда
		Возврат AllowWhitespaceOnly;
	КонецЕсли;
	
	// Alphanumeric requirement
	Если RequireAlphanumeric Тогда
		HasAlphanumeric = False;
		Для i = 1 По StrLen(TrimmedValue) Цикл
			CharCode = CharCode(Mid(TrimmedValue, i, 1));
			Если (CharCode >= 48 И CharCode <= 57) ИЛИ // 0-9
				(CharCode >= 65 И CharCode <= 90) ИЛИ // A-Z
				(CharCode >= 97 И CharCode <= 122) Тогда // a-z
				HasAlphanumeric = True;
				Прервать;
			КонецЕсли;
		КонецЦикла;
		
		Если НЕ HasAlphanumeric Тогда
			Возврат False;
		КонецЕсли;
	КонецЕсли;
	
	// Forbidden characters check
	Если HasText(ForbiddenChars) Тогда
		Для i = 1 По StrLen(ForbiddenChars) Цикл
			Если StrFind(Value, Mid(ForbiddenChars, i, 1)) > 0 Тогда
				Возврат False;
			КонецЕсли;
		КонецЦикла;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

#Region examples_М1сAIСтроки_HasText_Enhanced
// Example 1: Basic usage
//   Message(HasText("Hello, A1s!"));      // TRUE
//   Message(HasText("   "));              // FALSE
//   Message(HasText(Undefined));          // FALSE
//
// Example 2: With options
//   Options = New Structure;
//   Options.Insert("MinLength", 5);
//   Options.Insert("RequireAlphanumeric", True);
//   Message(HasText("12345", Options));   // TRUE
//   Message(HasText("!@#$", Options));    // FALSE
#EndRegion
#EndRegion

#Region М1сAIСтроки_StringMetrics_NEW
/// <summary>
/// String analysis and metrics calculation utilities.
/// </summary>

/// <summary>
/// Calculates various string metrics and statistics.
/// </summary>
/// <param name="SourceText">Text to analyze</param>
/// <returns type="Structure">Structure with metrics: Length, Words, Lines, Characters, etc.</returns>
Функция CalculateMetrics(SourceText) Экспорт
	
	Metrics = Новый Structure;
	Metrics.Insert("Length", 0);
	Metrics.Insert("Words", 0);
	Metrics.Insert("Lines", 0);
	Metrics.Insert("Characters", 0);
	Metrics.Insert("Digits", 0);
	Metrics.Insert("Spaces", 0);
	Metrics.Insert("SpecialChars", 0);
	
	Если НЕ HasText(SourceText) Тогда
		Возврат Metrics;
	КонецЕсли;
	
	Metrics.Length = StrLen(SourceText);
	
	// Count lines
	Metrics.Lines = StrOccurrenceCount(SourceText, Chars.LF) + 1;
	Если Right(SourceText, 1) = Chars.LF Тогда
		Metrics.Lines = Metrics.Lines - 1;
	КонецЕсли;
	
	// Analyze characters
	Для i = 1 По StrLen(SourceText) Цикл
		Char = Mid(SourceText, i, 1);
		CharCode = CharCode(Char);
		
		Если CharCode >= 48 И CharCode <= 57 Тогда // 0-9
			Metrics.Digits = Metrics.Digits + 1;
		ИначеЕсли CharCode = 32 ИЛИ CharCode = 9 ИЛИ CharCode = 10 ИЛИ CharCode = 13 Тогда // Spaces
			Metrics.Spaces = Metrics.Spaces + 1;
		ИначеЕсли (CharCode >= 65 И CharCode <= 90) ИЛИ (CharCode >= 97 И CharCode <= 122) Тогда // A-Z, a-z
			Metrics.Characters = Metrics.Characters + 1;
		Иначе
			Metrics.SpecialChars = Metrics.SpecialChars + 1;
		КонецЕсли;
	КонецЦикла;
	
	// Count words (approximate)
	Words = StrSplit(TrimAll(SourceText), " ", True);
	Metrics.Words = Words.Count();
	
	Возврат Metrics;
	
КонецФункции

/// <summary>
/// Calculates similarity between two strings using various algorithms.
/// </summary>
/// <param name="String1">First string</param>
/// <param name="String2">Second string</param>
/// <param name="Algorithm" type="String" default="Levenshtein">Similarity algorithm</param>
/// <returns type="Number">Similarity coefficient (0-1)</returns>
Функция CalculateSimilarity(String1, String2, Algorithm = "Levenshtein") Экспорт
	
	Если String1 = String2 Тогда
		Возврат 1.0;
	КонецЕсли;
	
	Если НЕ HasText(String1) ИЛИ НЕ HasText(String2) Тогда
		Возврат 0.0;
	КонецЕсли;
	
	Если Algorithm = "Levenshtein" Тогда
		Distance = LevenshteinDistance(String1, String2);
		MaxLength = Max(StrLen(String1), StrLen(String2));
		Возврат 1.0 - (Distance / MaxLength);
	ИначеЕсли Algorithm = "Jaccard" Тогда
		Возврат JaccardSimilarity(String1, String2);
	Иначе
		// Simple character overlap
		Возврат SimpleOverlapSimilarity(String1, String2);
	КонецЕсли;
	
КонецФункции

// Helper function for Levenshtein distance
Функция LevenshteinDistance(S1, S2)
	Len1 = StrLen(S1);
	Len2 = StrLen(S2);
	
	Если Len1 = 0 Тогда Возврат Len2; КонецЕсли;
	Если Len2 = 0 Тогда Возврат Len1; КонецЕсли;
	
	// Create matrix
	Matrix = Новый Array(Len1 + 1);
	Для i = 0 По Len1 Цикл
		Matrix[i] = Новый Array(Len2 + 1);
		Matrix[i][0] = i;
	КонецЦикла;
	
	Для j = 0 По Len2 Цикл
		Matrix[0][j] = j;
	КонецЦикла;
	
	// Fill matrix
	Для i = 1 По Len1 Цикл
		Для j = 1 По Len2 Цикл
			Cost = ?(Mid(S1, i, 1) = Mid(S2, j, 1), 0, 1);
			Matrix[i][j] = Min(
					Matrix[i - 1][j] + 1, // Deletion
					Matrix[i][j - 1] + 1, // Insertion
					Matrix[i - 1][j - 1] + Cost // Substitution
				);
		КонецЦикла;
	КонецЦикла;
	
	Возврат Matrix[Len1][Len2];
КонецФункции

Функция JaccardSimilarity(S1, S2)
	Set1 = Новый Map;
	Set2 = Новый Map;
	
	// Create character sets
	Для i = 1 По StrLen(S1) Цикл
		Char = Mid(S1, i, 1);
		Set1.Insert(Char, True);
	КонецЦикла;
	
	Для i = 1 По StrLen(S2) Цикл
		Char = Mid(S2, i, 1);
		Set2.Insert(Char, True);
	КонецЦикла;
	
	// Calculate intersection and union
	Intersection = 0;
	Union = Set1.Count();
	
	Для Каждого Item Из Set2 Цикл
		Если Set1.Get(Item.Key) <> Undefined Тогда
			Intersection = Intersection + 1;
		Иначе
			Union = Union + 1;
		КонецЕсли;
	КонецЦикла;
	
	Возврат ?(Union = 0, 0, Intersection / Union);
КонецФункции

Функция SimpleOverlapSimilarity(S1, S2)
	CommonChars = 0;
	TotalChars = StrLen(S1) + StrLen(S2);
	
	Для i = 1 По StrLen(S1) Цикл
		Char = Mid(S1, i, 1);
		Если StrFind(S2, Char) > 0 Тогда
			CommonChars = CommonChars + 1;
		КонецЕсли;
	КонецЦикла;
	
	Возврат ?(TotalChars = 0, 0, (2.0 * CommonChars) / TotalChars);
КонецФункции

#EndRegion


#Region М1сAIСтроки_Validation_Enhanced
/// <summary>
/// Enhanced validation utilities for various data types and formats.
/// </summary>

/// <summary>
/// Validates email address format.
/// </summary>
/// <param name="Email">Email address to validate</param>
/// <param name="Strict" type="Boolean" default="False">Use strict validation rules</param>
/// <returns type="Boolean">True if email format is valid</returns>
Функция IsValidEmail(Email, Strict = False) Экспорт
	
	Если НЕ HasText(Email) Тогда
		Возврат False;
	КонецЕсли;
	
	Email = TrimAll(Email);
	
	// Basic format check
	Если StrOccurrenceCount(Email, "@") <> 1 Тогда
		Возврат False;
	КонецЕсли;
	
	Parts = StrSplit(Email, "@", False);
	Если Parts.Count() <> 2 Тогда
		Возврат False;
	КонецЕсли;
	
	LocalPart = Parts[0];
	DomainPart = Parts[1];
	
	// Local part validation
	Если НЕ HasText(LocalPart) ИЛИ StrLen(LocalPart) > 64 Тогда
		Возврат False;
	КонецЕсли;
	
	// Domain part validation
	Если НЕ HasText(DomainPart) ИЛИ StrLen(DomainPart) > 255 Тогда
		Возврат False;
	КонецЕсли;
	
	Если StrFind(DomainPart, ".") = 0 Тогда
		Возврат False;
	КонецЕсли;
	
	Если Strict Тогда
		// Additional strict validation
		ForbiddenChars = " <>()[]{}|\""";
		Для i = 1 По StrLen(ForbiddenChars) Цикл
			Если StrFind(Email, Mid(ForbiddenChars, i, 1)) > 0 Тогда
				Возврат False;
			КонецЕсли;
		КонецЦикла;
		
		// Check for consecutive dots
		Если StrFind(Email, "..") > 0 Тогда
			Возврат False;
		КонецЕсли;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

/// <summary>
/// Validates phone number format.
/// </summary>
/// <param name="PhoneNumber">Phone number to validate</param>
/// <param name="Format" type="String" default="International">Expected format</param>
/// <returns type="Boolean">True if phone number format is valid</returns>
Функция IsValidPhoneNumber(PhoneNumber, Format = "International") Экспорт
	
	Если НЕ HasText(PhoneNumber) Тогда
		Возврат False;
	КонецЕсли;
	
	// Remove common formatting characters
	CleanNumber = PhoneNumber;
	CleanNumber = StrReplace(CleanNumber, " ", "");
	CleanNumber = StrReplace(CleanNumber, "-", "");
	CleanNumber = StrReplace(CleanNumber, "(", "");
	CleanNumber = StrReplace(CleanNumber, ")", "");
	CleanNumber = StrReplace(CleanNumber, ".", "");
	
	// Check for plus sign at the beginning (international format)
	HasPlusSign = Left(CleanNumber, 1) = "+";
	Если HasPlusSign Тогда
		CleanNumber = Mid(CleanNumber, 2);
	КонецЕсли;
	
	// Check if remaining characters are digits
	Если НЕ IsNumericString(CleanNumber) Тогда
		Возврат False;
	КонецЕсли;
	
	NumberLength = StrLen(CleanNumber);
	
	Если Format = "International" Тогда
		Возврат NumberLength >= 7 И NumberLength <= 15;
	ИначеЕсли Format = "National" Тогда
		Возврат NumberLength >= 7 И NumberLength <= 12;
	ИначеЕсли Format = "Local" Тогда
		Возврат NumberLength >= 7 И NumberLength <= 10;
	Иначе
		Возврат NumberLength >= 7 И NumberLength <= 15;
	КонецЕсли;
	
КонецФункции

/// <summary>
/// Validates URL format.
/// </summary>
/// <param name="URL">URL to validate</param>
/// <param name="RequireProtocol" type="Boolean" default="True">Require protocol specification</param>
/// <returns type="Boolean">True if URL format is valid</returns>
Функция IsValidURL(URL, RequireProtocol = True) Экспорт
	
	Если НЕ HasText(URL) Тогда
		Возврат False;
	КонецЕсли;
	
	URL = TrimAll(URL);
	
	// Check for protocol
	HasProtocol = StrFind(URL, "://") > 0;
	
	Если RequireProtocol И НЕ HasProtocol Тогда
		Возврат False;
	КонецЕсли;
	
	Если HasProtocol Тогда
		ProtocolEnd = StrFind(URL, "://");
		Protocol = Left(URL, ProtocolEnd - 1);
		
		// Validate common protocols
		ValidProtocols = "http,https,ftp,ftps,file";
		Если StrFind(ValidProtocols, Lower(Protocol)) = 0 Тогда
			Возврат False;
		КонецЕсли;
		
		URL = Mid(URL, ProtocolEnd + 3);
	КонецЕсли;
	
	// Basic domain validation
	Если НЕ HasText(URL) Тогда
		Возврат False;
	КонецЕсли;
	
	// Check for invalid characters
	InvalidChars = " <>\""{}|^`[]";
	Для i = 1 По StrLen(InvalidChars) Цикл
		Если StrFind(URL, Mid(InvalidChars, i, 1)) > 0 Тогда
			Возврат False;
		КонецЕсли;
	КонецЦикла;
	
	Возврат True;
	
КонецФункции

/// <summary>
/// Checks if string contains only numeric characters.
/// </summary>
/// <param name="Value">String to check</param>
/// <param name="AllowDecimal" type="Boolean" default="False">Allow decimal point</param>
/// <returns type="Boolean">True if string is numeric</returns>
Функция IsNumericString(Value, AllowDecimal = False) Экспорт
	
	Если НЕ HasText(Value) Тогда
		Возврат False;
	КонецЕсли;
	
	DecimalCount = 0;
	
	Для i = 1 По StrLen(Value) Цикл
		Char = Mid(Value, i, 1);
		CharCode = CharCode(Char);
		
		Если CharCode >= 48 И CharCode <= 57 Тогда // 0-9
			Продолжить;
		ИначеЕсли AllowDecimal И (Char = "." ИЛИ Char = ",") Тогда
			DecimalCount = DecimalCount + 1;
			Если DecimalCount > 1 Тогда
				Возврат False;
			КонецЕсли;
		Иначе
			Возврат False;
		КонецЕсли;
	КонецЦикла;
	
	Возврат True;
	
КонецФункции

#Region examples_М1сAIСтроки_Validation
// Example 1: Email validation
//   IsValid = М1сAIСтроки.IsValidEmail("user@example.com"); // True
//   IsValid = М1сAIСтроки.IsValidEmail("invalid.email");    // False
//
// Example 2: Phone validation
//   IsValid = М1сAIСтроки.IsValidPhoneNumber("+1-555-123-4567", "International"); // True
//
// Example 3: URL validation
//   IsValid = М1сAIСтроки.IsValidURL("https://www.example.com"); // True
#EndRegion
#EndRegion


#Region М1сAIСтроки_FormatText
/// <summary>
/// Формирует текст для вывода, поддерживает различные типы и логирование.
/// </summary>
/// <param name="Value" type="Variant" optional="True">Значение или коллекция.</param>
/// <param name="Title" type="String" optional="True">Заголовок перед значением.</param>
/// <param name="TitleDelim" type="String" optional="True">Разделитель после заголовка.</param>
/// <param name="LogNeeded" type="Boolean" optional="True">Если Истина, пишет в лог через М1сAIЛогирование.Write.</param>
/// <returns type="String">Сформированная строка для вывода.</returns>
Функция FormatText(Value = "", Title = "", TitleDelim = "", LogNeeded = False) Экспорт
	
	Result = "";
	Если Title <> "" Тогда
		Result = Title + ?(TitleDelim = "", " ", TitleDelim + " ");
	КонецЕсли;
	
	Тип = TypeOf(Value);
	
	Если Тип = Type("Map") ИЛИ Тип = Type("Structure") Тогда
		Для Каждого P Из Value Цикл
			Result = Result + AsString(P.Key) + ": " + AsString(P.Value) + "; ";
		КонецЦикла;
	ИначеЕсли Тип = Type("Array") ИЛИ Тип = Type("ValueList") Тогда
		Для Каждого E Из Value Цикл
			Result = Result + AsString(E) + "; ";
		КонецЦикла;
		#If Server Or ExternalConnection Then
	ИначеЕсли Тип = Type("ValueTable") Тогда
		Для Каждого R Из Value Цикл
			RowStr = "";
			Для Каждого C Из Value.Columns Цикл
				RowStr = RowStr + AsString(C.Name) + ": " + AsString(R[C.Name]) + "; ";
			КонецЦикла;
			Result = Result + "[" + Left(RowStr, StrLen(RowStr) - 2) + "]; " + М1сAIСимволы.LineBreak();
		КонецЦикла;
		#EndIf
	Иначе
		Result = Result + AsString(Value) + "; ";
	КонецЕсли;
	
	Если Right(Result, 2) = "; " Тогда
		Result = Left(Result, StrLen(Result) - 2);
	КонецЕсли;
	
	Если LogNeeded Тогда
		#If Server Or ExternalConnection Then
		М1сAIЛогирование.Write(Result);
		#EndIf
	КонецЕсли;
	
	Возврат Result;
КонецФункции
#Region examples_М1сAIСтроки_FormatText
// Пример:
// Headers = Новый Map; Headers.Вставить("Accept", "application/json");
// Msg = М1сAIСтроки.FormatText(Headers, "Заголовки", "-", Истина);
#EndRegion
#EndRegion


#Region М1сAIСтроки_Print
/// <summary>
/// Выводит подготовленный текст через Message.
/// </summary>
/// <param name="Value">Значение или коллекция для вывода.</param>
/// <param name="Title" type="String" optional="True">Заголовок.</param>
/// <param name="Delim" type="String" optional="True">Разделитель после заголовка.</param>
/// <param name="LogNeeded" type="Boolean" optional="True">Логгировать ли текст.</param>
Процедура Print(Value = "", Title = "", Delim = "", LogNeeded = False) Экспорт
	Message(FormatText(Value, Title, Delim, LogNeeded));
КонецПроцедуры
#Region examples_М1сAIСтроки_Print
// М1сAIСтроки.Print(Параметры, "Данные", ":");
#EndRegion
#EndRegion

#Region М1сAIСтроки_Printf
// <doc>
//   <summary>Выводит сообщение по шаблону с автоконвертацией параметров; учитывает фактическое число плейсхолдеров.</summary>
//   <param i="1" name="Template" type="String">Шаблон c плейсхолдерами %1…%8 или [%1]…[%8].</param>
//   <param i="2..9" name="v1..v8" type="Variant" default="Undefined">Значения для замены.</param>
//   <complexity cc="3"/>
// </doc>
Процедура Printf(Template = "", v1 = Undefined, v2 = Undefined, v3 = Undefined, v4 = Undefined, v5 = Undefined, v6 = Undefined, v7 = Undefined, v8 = Undefined) Экспорт //⚙
	
	// 1) Определяем максимальный плейсхолдер в шаблоне
	MaxIdx = _М1сAIСтроки_MaxPlaceholderIndex(Template); // 0..8
	
	// 2) Без плейсхолдеров — просто выводим текст как есть
	Если MaxIdx = 0 Тогда
		Message(Template); //▶️
		Возврат;
	КонецЕсли;
	
	// 3) Готовим значения только по факту нужного количества
	//    (автоконвертация + "<пусто>" для Undefined)
	
	// 4) Вызываем StrTemplate с ровно нужным числом параметров
	Если MaxIdx = 1 Тогда
		FormattedText = StrTemplate(Template, ToS(v1));
	ИначеЕсли MaxIdx = 2 Тогда
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2));
	ИначеЕсли MaxIdx = 3 Тогда
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2), ToS(v3));
	ИначеЕсли MaxIdx = 4 Тогда
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2), ToS(v3), ToS(v4));
	ИначеЕсли MaxIdx = 5 Тогда
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2), ToS(v3), ToS(v4), ToS(v5));
	ИначеЕсли MaxIdx = 6 Тогда
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2), ToS(v3), ToS(v4), ToS(v5), ToS(v6));
	ИначеЕсли MaxIdx = 7 Тогда
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2), ToS(v3), ToS(v4), ToS(v5), ToS(v6), ToS(v7));
	Иначе // MaxIdx = 8
		FormattedText = StrTemplate(Template, ToS(v1), ToS(v2), ToS(v3), ToS(v4), ToS(v5), ToS(v6), ToS(v7), ToS(v8));
	КонецЕсли;
	
	Message(FormattedText); //▶️
КонецПроцедуры

Функция ToS(Знч) Экспорт
	Возврат ?(Знч = Undefined, "<пусто>", М1сAIСтроки.AsString(Знч));
КонецФункции

// Вспомогательная: ищет максимальный %N или [%N] в строке (N=1..8)
Функция _М1сAIСтроки_MaxPlaceholderIndex(Template) Экспорт
	i = 8;
	Пока i >= 1 Цикл
		// Поддерживаем оба синтаксиса: "%N" и "[%N]"
		Если (СтрНайти(Template, "%" + Строка(i)) > 0)
			ИЛИ (СтрНайти(Template, "[%" + Строка(i) + "]") > 0) Тогда
			Возврат i;
		КонецЕсли;
		i = i - 1;
	КонецЦикла;
	Возврат 0;
КонецФункции
#EndRegion

#Region М1сAIСтроки_PrintYN
/// <summary>
/// Выводит текст в зависимости от условия.
/// </summary>
/// <param name="Condition">Условие для проверки.</param>
/// <param name="TextIfTrue">Текст, который будет выведен, если условие истинно.</param>
/// <param name="TextIfFalse" type="String" optional="True">Текст, который будет выведен, если условие ложно.</param>
Процедура PrintYN(Condition, TextIfTrue, TextIfFalse = "") Экспорт
	Если Condition Тогда
		Print(TextIfTrue);
	Иначе
		Если TextIfFalse <> "" Тогда
			Print(TextIfFalse);
		КонецЕсли;
	КонецЕсли;
КонецПроцедуры
#Region examples_М1сAIСтроки_PrintYN
// М1сAIСтроки.PrintYN(AreEqual, "HURRAY! They are equal!", "NO! NO! NO! They are NOT equal!");
// М1сAIСтроки.PrintYN(AreEqual, "HURRAY! They are equal!");
#EndRegion
#EndRegion

#Region М1сAIСтроки_PrintJSON
/// <summary>
/// Выводит JSON-представление значения через Message.
/// </summary>
/// <param name="Value">Любое значение.</param>
/// <param name="Title" type="String" optional="True">Заголовок.</param>
/// <param name="Delim" type="String" optional="True">Разделитель.</param>
/// <param name="LogNeeded" type="Boolean" optional="True">Логгировать.</param>
Процедура PrintJSON(Value = "", Title = "", Delim = "", LogNeeded = False) Экспорт
	Message(FormatText(М1сAIJSON.ToJSON(Value), Title, Delim, LogNeeded));
КонецПроцедуры
#Region examples_М1сAIСтроки_PrintJSON
// М1сAIСтроки.PrintJSON(Параметры, "JSON", "-");
#EndRegion
#EndRegion

#Region М1сAIСтроки_PrintXML
/// <summary>
/// Выводит XML-представление значения через Message.
/// </summary>
/// <param name="Value">Любой объект.</param>
/// <param name="Title" type="String" optional="True">Заголовок.</param>
/// <param name="Delim" type="String" optional="True">Разделитель.</param>
/// <param name="LogNeeded" type="Boolean" optional="True">Логгировать.
Процедура PrintXML(Value = "", Title = "", Delim = "", LogNeeded = False) Экспорт
	Message(FormatText(М1сAIXML.ToXML(Value), Title, Delim, LogNeeded));
КонецПроцедуры
#Region examples_М1сAIСтроки_PrintXML
// М1сAIСтроки.PrintXML(Параметры, "XML", ".");
#EndRegion
#EndRegion

#Region М1сAIСтроки_ToAnyReadable
/// <summary>
/// Универсальная сериализация значения в читаемый формат:
/// сначала JSON, затем XML, затем AsString. Без ограничений.
/// </summary>
/// <param name="Value">Любое значение 1С</param>
/// <returns type="String">Читаемое текстовое представление</returns>
Функция ToAnyReadable(Value) Экспорт // ⚙
	Попытка // ✱
		Возврат М1сAIJSON.ToJSON(Value); // ▶️
	Исключение
		Попытка // ✱
			Возврат М1сAIXML.ToXML(Value); // ▶️
		Исключение
			Возврат М1сAIСтроки.AsString(Value); // ▶️
		КонецПопытки;
	КонецПопытки;
КонецФункции

#Region examples_М1сAIСтроки_ToAnyReadable
// Пример 1: структура
//   S = Новый Структура("X,Y", 1, "Test");
//   Msg = М1сAIСтроки.ToAnyReadable(S);
//
// Пример 2: массив
//   Arr = Новый Массив(1, 2, 3);
//   Msg = М1сAIСтроки.ToAnyReadable(Arr);
//
// Пример 3: число
//   Msg = М1сAIСтроки.ToAnyReadable(123); // "123"
#EndRegion
#EndRegion


#Region М1сAIСтроки_ToAnyReadableShort
/// <summary>
/// Сериализация значения с ограничением по длине.
/// Используется для логов, UI и отладочных сообщений.
/// </summary>
/// <param name="Value">Значение для сериализации</param>
/// <param name="MaxLen" type="Number" default="120">Максимальная длина строки</param>
/// <returns type="String">Сокращённая строка</returns>
Функция ToAnyReadableShort(Value, MaxLen = 120) Экспорт // ⚙
	msg = М1сAIСтроки.ToAnyReadable(Value); // ▶️
	
	Если СтрДлина(msg) > MaxLen Тогда // ⚡
		msg = Лев(msg, MaxLen) + "... [" + СтрДлина(msg) + " chars]";
	КонецЕсли;
	
	Возврат msg;
КонецФункции

#Region examples_М1сAIСтроки_ToAnyReadableShort
// Пример: большая структура
//   Struct = Новый Структура("Name,Description", "Товар", СтрПовтор("A", 1000));
//   Msg = М1сAIСтроки.ToAnyReadableShort(Struct); // вернёт урезанный JSON
#EndRegion
#EndRegion

#Region М1сAIСтроки_FilterTableByField
/// ✦ <summary>Фильтрует таблицу по значению поля и возвращает массив другого поля.</summary>
/// ➤ <param name="Таблица">Таблица значений (ValueTable)</param>
/// ➤ <param name="ДопустимыеЗначения">Массив допустимых значений для фильтра</param>
/// ➤ <param name="ПолеФильтра">Имя поля, по которому проводится фильтрация</param>
/// ➤ <param name="ПолеРезультата">Имя поля, значения которого включаются в результат</param>
/// ⬅ <returns>Массив отфильтрованных значений из заданного поля</returns>
&НаСервере
Функция FilterTableByField(Таблица, ДопустимыеЗначения, ПолеФильтра, ПолеРезультата) Экспорт //⚙
	
	Результат = Новый Массив; //✏
	
	Для Каждого строка Из Таблица Цикл //⟳
		Если ДопустимыеЗначения.Найти(строка[ПолеФильтра]) <> Неопределено Тогда //⚡
			Результат.Добавить(строка[ПолеРезультата]); //✏
		КонецЕсли;
	КонецЦикла;
	
	Возврат Результат; //↩
	
КонецФункции
#EndRegion

//--------------------------------------------------------

#Region М1сAIСтроки_TextProcessing_NEW
/// <summary>
/// Advanced text processing utilities for complex string operations.
/// </summary>

/// <summary>
/// Extracts text between specified delimiters with support for nested structures.
/// </summary>
/// <param name="SourceText">Source text to process</param>
/// <param name="StartDelim">Starting delimiter</param>
/// <param name="EndDelim">Ending delimiter</param>
/// <param name="IncludeDelimiters" type="Boolean" default="False">Include delimiters in result</param>
/// <returns type="Array">Array of extracted text fragments</returns>
Функция ExtractBetween(SourceText,
		StartDelim,
		EndDelim,
		IncludeDelimiters = False) Экспорт
	
	Result = Новый Array;
	
	Если НЕ HasText(SourceText) ИЛИ НЕ HasText(StartDelim) ИЛИ НЕ HasText(EndDelim) Тогда
		Возврат Result;
	КонецЕсли;
	
	SearchPos = 1;
	Пока SearchPos <= StrLen(SourceText) Цикл
		StartPos = StrFind(SourceText, StartDelim, SearchDirection.FromBegin, SearchPos);
		Если StartPos = 0 Тогда
			Прервать;
		КонецЕсли;
		
		EndPos = StrFind(SourceText, EndDelim, SearchDirection.FromBegin, StartPos + StrLen(StartDelim));
		Если EndPos = 0 Тогда
			Прервать;
		КонецЕсли;
		
		Если IncludeDelimiters Тогда
			ExtractedText = Mid(SourceText, StartPos, EndPos - StartPos + StrLen(EndDelim));
		Иначе
			ExtractedText = Mid(SourceText, StartPos + StrLen(StartDelim),
					EndPos - StartPos - StrLen(StartDelim));
		КонецЕсли;
		
		Result.Add(ExtractedText);
		SearchPos = EndPos + StrLen(EndDelim);
	КонецЦикла;
	
	Возврат Result;
	
КонецФункции

/// <summary>
/// Replaces text with support for case sensitivity and replace-all.
/// </summary>
/// <param name="SourceText">Source text</param>
/// <param name="SearchText">Text to find</param>
/// <param name="ReplaceText">Replacement text</param>
/// <param name="CaseSensitive" type="Boolean" default="True">Case sensitive search</param>
/// <param name="ReplaceAll" type="Boolean" default="True">Replace all occurrences</param>
/// <param name="ConfigPerformanceLog" type="Boolean" optional="True">Performance log</param>
/// <param name="ConfigDebugMode" type="Boolean" optional="True">Debug mode</param>
/// <returns type="String">Text with replacements applied</returns>
Функция ReplaceText(SourceText,
		SearchText,
		ReplaceText,
		CaseSensitive = True,
		ReplaceAll = True,
		ConfigPerformanceLog = False,
		ConfigDebugMode = False)
	Экспорт
	
	Если НЕ HasText(SourceText) ИЛИ НЕ HasText(SearchText) Тогда
		Возврат SourceText;
	КонецЕсли;
	
	StartTime = ?(ConfigPerformanceLog, CurrentUniversalDateInMilliseconds(), 0);
	
	Result = SourceText;
	
	Попытка
		Если CaseSensitive Тогда
			Если ReplaceAll Тогда
				Result = StrReplace(Result, SearchText, ReplaceText);
			Иначе
				Pos = StrFind(Result, SearchText);
				Если Pos > 0 Тогда
					Result = Left(Result, Pos - 1) + ReplaceText +
						Mid(Result, Pos + StrLen(SearchText));
				КонецЕсли;
			КонецЕсли;
		Иначе
			// Без учёта регистра
			SearchTextLower = Lower(SearchText);
			SourceLower = Lower(Result);
			
			Если ReplaceAll Тогда
				TempResult = "";
				StartPos = 1;
				Пока StartPos <= StrLen(Result) Цикл
					// Найти позицию (без учёта регистра) с текущей позиции
					RelPos = StrFind(Lower(Mid(Result, StartPos)), SearchTextLower);
					Если RelPos > 0 Тогда
						Pos = StartPos + RelPos - 1;
						TempResult = TempResult + Left(Result, Pos - 1) + ReplaceText;
						StartPos = Pos + StrLen(SearchText);
						Result = Mid(Result, StartPos);
						StartPos = 1;
					Иначе
						TempResult = TempResult + Result;
						Прервать;
					КонецЕсли;
				КонецЦикла;
				Result = TempResult;
			Иначе
				Pos = StrFind(Lower(Result), SearchTextLower);
				Если Pos > 0 Тогда
					Result = Left(Result, Pos - 1) + ReplaceText +
						Mid(Result, Pos + StrLen(SearchText));
				КонецЕсли;
			КонецЕсли;
		КонецЕсли;
	Исключение
		Если ConfigDebugMode Тогда
			М1сAIЛогирование.Error("ReplaceText failed", ErrorInfo());
		КонецЕсли;
		Result = SourceText; // Вернуть исходный текст в случае ошибки
	КонецПопытки;
	
	Если ConfigPerformanceLog Тогда
		ElapsedTime = CurrentUniversalDateInMilliseconds() - StartTime;
		Если ElapsedTime > 100 Тогда
			М1сAIЛогирование.Write("ReplaceText - " + ElapsedTime + " ms; SourceLen=" + StrLen(SourceText));
		КонецЕсли;
	КонецЕсли;
	
	Возврат Result;
	
КонецФункции

/// <summary>
/// Creates a template builder for complex template construction.
/// </summary>
/// <returns type="Structure">Template builder object</returns>
Функция CreateTemplateBuilder() Экспорт
	
	Builder = Новый Structure;
	Builder.Insert("Template", "");
	Builder.Insert("Variables", Новый Structure);
	Builder.Insert("Sections", Новый Array);
	
	// Methods as structure properties
	Builder.Insert("AddText", "AddTextToTemplate");
	Builder.Insert("AddVariable", "AddVariableToTemplate");
	Builder.Insert("AddSection", "AddSectionToTemplate");
	Builder.Insert("Build", "BuildTemplate");
	
	Возврат Builder;
	
КонецФункции

// Template builder helper functions
Функция AddTextToTemplate(Builder, Text)
	Builder.Template = Builder.Template + Text;
	Возврат Builder;
КонецФункции

Функция AddVariableToTemplate(Builder, Name, Value)
	Builder.Variables.Insert(Name, Value);
	Builder.Template = Builder.Template + "{" + Name + "}";
	Возврат Builder;
КонецФункции

Функция BuildTemplate(Builder, Variables = Undefined)
	Если Variables = Undefined Тогда
		Variables = Builder.Variables;
	КонецЕсли;
	
	Возврат ProcessTemplate(Builder.Template, Variables);
КонецФункции

/// <summary>
/// Processes template with variable substitution.
/// </summary>
/// <param name="Template">Template string with placeholders</param>
/// <param name="Variables" type="Structure/Map">Variables for substitution</param>
/// <param name="Options" type="Structure" optional="True">Processing options</param>
/// <returns type="String">Processed template</returns>
Функция ProcessTemplate(Template, Variables, Options = Undefined) Экспорт
	
	Если НЕ HasText(Template) Тогда
		Возврат "";
	КонецЕсли;
	
	Если Variables = Undefined Тогда
		Variables = Новый Structure;
	КонецЕсли;
	
	// Initialize options
	PlaceholderStart = "{";
	PlaceholderEnd = "}";
	CaseSensitive = True;
	RemoveUnresolved = False;
	
	Если Options <> Undefined Тогда
		Если Options.Property("PlaceholderStart") Тогда
			PlaceholderStart = Options.PlaceholderStart;
		КонецЕсли;
		Если Options.Property("PlaceholderEnd") Тогда
			PlaceholderEnd = Options.PlaceholderEnd;
		КонецЕсли;
		Если Options.Property("CaseSensitive") Тогда
			CaseSensitive = Options.CaseSensitive;
		КонецЕсли;
		Если Options.Property("RemoveUnresolved") Тогда
			RemoveUnresolved = Options.RemoveUnresolved;
		КонецЕсли;
	КонецЕсли;
	
	Result = Template;
	
	Попытка
		// 1. Подстановка переменных
		Для Каждого Variable Из Variables Цикл
			Placeholder = PlaceholderStart + String(Variable.Key) + PlaceholderEnd;
			Value = AsString(Variable.Value);
			Если CaseSensitive Тогда
				Result = StrReplace(Result, Placeholder, Value);
			Иначе
				Result = ReplaceText(Result, Placeholder, Value, False, True);
			КонецЕсли;
		КонецЦикла;
		
		// 2. Удалить/очистить неразрешённые плейсхолдеры, если нужно
		Если RemoveUnresolved Тогда
			StartPos = StrFind(Result, PlaceholderStart);
			Пока StartPos > 0 Цикл
				EndPos = StrFind(Result, PlaceholderEnd, StartPos);
				Если EndPos > 0 Тогда
					Result = Left(Result, StartPos - 1) + Mid(Result, EndPos + StrLen(PlaceholderEnd));
					StartPos = StrFind(Result, PlaceholderStart, StartPos);
				Иначе
					// Нет пары — выход
					Прервать;
				КонецЕсли;
			КонецЦикла;
		КонецЕсли;
		
	Исключение
		// Вернуть исходный шаблон в случае ошибки
		Result = Template;
	КонецПопытки;
	
	Возврат Result;
	
КонецФункции

//Template = "Hello, {Name}! Your score: {Score}.";
//Vars = New Structure("Name", "Vadim", "Score", 100);
//Str = ProcessTemplate(Template, Vars);
//// "Hello, Vadim! Your score: 100."

//// С удалением неразрешённых плейсхолдеров:
//Template = "Hi, {Name}! {Unknown}!";
//Vars = New Structure("Name", "Vadim");
//Options = New Structure("RemoveUnresolved", True);
//Str = ProcessTemplate(Template, Vars, Options);
//// "Hi, Vadim! !"


#Region examples_М1сAIСтроки_Templates
// Example 1: Simple template
//   Template = "Hello, {Name}! Today is {Date}.";
//   Vars = New Structure;
//   Vars.Insert("Name", "John");
//   Vars.Insert("Date", CurrentDate());
//   Result = М1сAIСтроки.ProcessTemplate(Template, Vars);
//
// Example 2: Template builder
//   Builder = М1сAIСтроки.CreateTemplateBuilder();
//   Builder = AddTextToTemplate(Builder, "User: ");
//   Builder = AddVariableToTemplate(Builder, "UserName", "Admin");
//   Result = BuildTemplate(Builder);
#EndRegion
#EndRegion

/// <summary>
/// Normalizes whitespace in text (removes extra spaces, tabs, line breaks).
/// </summary>
/// <param name="SourceText">Text to normalize</param>
/// <param name="PreserveParagraphs" type="Boolean" default="False">Preserve paragraph breaks</param>
/// <returns type="String">Normalized text</returns>
Функция NormalizeWhitespace(SourceText, PreserveParagraphs = False) Экспорт
	
	Если НЕ HasText(SourceText) Тогда
		Возврат "";
	КонецЕсли;
	
	Result = SourceText;
	
	// Replace multiple spaces with single space
	Пока StrFind(Result, "  ") > 0 Цикл
		Result = StrReplace(Result, "  ", " ");
	КонецЦикла;
	
	// Handle line breaks
	Если PreserveParagraphs Тогда
		// Replace multiple line breaks with double line break
		Result = StrReplace(Result, Chars.CR + Chars.LF, Chars.LF);
		Result = StrReplace(Result, Chars.CR, Chars.LF);
		
		Пока StrFind(Result, Chars.LF + Chars.LF + Chars.LF) > 0 Цикл
			Result = StrReplace(Result, Chars.LF + Chars.LF + Chars.LF, Chars.LF + Chars.LF);
		КонецЦикла;
	Иначе
		// Replace all line breaks with spaces
		Result = StrReplace(Result, Chars.CR + Chars.LF, " ");
		Result = StrReplace(Result, Chars.CR, " ");
		Result = StrReplace(Result, Chars.LF, " ");
		Result = StrReplace(Result, Chars.Tab, " ");
	КонецЕсли;
	
	Возврат TrimAll(Result);
	
КонецФункции

#Region М1сAIСтроки_Subst

// Subst (flags: Server + External connection + Client)
//
// Производит замену плейсхолдеров вида {ключ} в тексте на соответствующие значения из структуры параметров.
//
// Параметры:
//   Text   – Строка – исходный текст с плейсхолдерами {ключ}
//   Params – Структура – структура с параметрами для подстановки ключ-значение
//
// Возвращаемое значение:
//   Строка – текст с подставленными значениями параметров
//
// Пример:
//   Params = Новый Структура("User,Date", "Иванов", "21.07.2025");
//   Текст = "Отчет для {User} от {Date}";
//   Результат = М1сAIСтроки.Subst(Текст, Params); // "Отчет для Иванов от 21.07.2025"
//
Функция Subst(Text, Params) Экспорт
	
	Если Params <> Неопределено И ТипЗнч(Params) = Тип("Структура") Тогда
		Для Каждого Элемент Из Params Цикл
			Placeholder = "{" + Элемент.Ключ + "}";
			Text = СтрЗаменить(Text, Placeholder, Строка(Элемент.Значение));
		КонецЦикла;
	КонецЕсли;
	
	Возврат Text;
	
КонецФункции

#EndRegion

#Region М1сAIСтроки_GetTemplate

// Получает текст из общего макета с подстановкой параметров
// Работает на сервере, толстом клиенте и внешнем соединении
//
// Параметры:
//  TemplateName - Строка - имя общего макета
//  Params - Структура - параметры для подстановки в формате {ключ}
//  DefaultText - Строка - текст по умолчанию при ошибке
//
// Возвращаемое значение:
//  Строка - текст макета с подставленными параметрами
//
// Пример:
//  Params = Новый Структура("User,Date", "Иванов", "21.07.2025");
//  Text = A1s.GetTemplate("UserReport", Params);
//  // В макете: "Отчет для {User} от {Date}" -> "Отчет для Иванов от 21.07.2025"
//
// В общем модуле М1сAIСтроки с флагами: Сервер + Клиент + ВнешнееСоединение

Функция GetTemplate(TemplateName, Params = Неопределено, DefaultText = "") Экспорт
	
	#Если Сервер Или ТолстыйКлиентОбычноеПриложение Или ВнешнееСоединение Тогда
	
	Попытка
		Макет = ПолучитьОбщийМакет(TemplateName);
		Если Макет = Неопределено Тогда
			Возврат DefaultText;
		КонецЕсли;
		
		ТекстМакета = Макет.ПолучитьТекст();
		
		// Подстановка параметров
		Если Params <> Неопределено И ТипЗнч(Params) = Тип("Структура") Тогда
			Для Каждого Элемент Из Params Цикл
				Placeholder = "{" + Элемент.Ключ + "}";
				ТекстМакета = СтрЗаменить(ТекстМакета, Placeholder, Строка(Элемент.Значение));
			КонецЦикла;
		КонецЕсли;
		
		Возврат ТекстМакета;
		
	Исключение
		Возврат DefaultText;
	КонецПопытки;
	
	#Иначе
	
	// На тонком клиенте функция недоступна
	ВызватьИсключение "Функция GetTemplate() недоступна на тонком клиенте. " +
	"Используйте серверную процедуру в модуле формы.";
	
	#КонецЕсли
	
КонецФункции

#EndRegion

#Region М1сAIСтроки_SelfTest_Comprehensive
/// <summary>
/// Comprehensive unit testing suite for enhanced М1сAIСтроки module.
/// </summary>
/// <returns type="Boolean">True if all tests pass</returns>
Функция SelfTest() Экспорт
	
	TestResults = Новый Array;
	
	// Test AsString Enhanced
	TestResults.Add(TestAsStringEnhanced());
	
	// Test Split Enhanced
	TestResults.Add(TestSplitEnhanced());
	
	// Test HasText Enhanced
	TestResults.Add(TestHasTextEnhanced());
	
	// Test Text Processing
	TestResults.Add(TestTextProcessing());
	
	// Test String Metrics
	TestResults.Add(TestStringMetrics());
	
	// Test Validation
	TestResults.Add(TestValidation());
	
	// Test Templates
	TestResults.Add(TestTemplates());
	
	// Evaluate overall result
	AllTestsPassed = True;
	Для Каждого Result Из TestResults Цикл
		Если НЕ Result Тогда
			AllTestsPassed = False;
			Прервать;
		КонецЕсли;
	КонецЦикла;
	
	Если AllTestsPassed Тогда
		Print("М1сAIСтроки Enhanced: All tests PASSED ✓", "SelfTest", "");
	Иначе
		Print("М1сAIСтроки Enhanced: Some tests FAILED ✗", "SelfTest", "");
	КонецЕсли;
	
	Возврат AllTestsPassed;
	
КонецФункции

Функция TestAsStringEnhanced()
	Попытка
		// Test 1: Basic conversion
		Result = AsString(123, "[", "]");
		Если Result <> "[123]" Тогда Возврат False; КонецЕсли;
		
		// Test 2: Date formatting
		Options = Новый Structure;
		Options.Insert("DateFormat", "ДФ='ddMMyyyy'");
		Result = AsString(Date(2025, 5, 13), "", "", Options);
		//13.05.2025 0:00:00
		Если StrLen(Result) <> 8 Тогда Возврат False; КонецЕсли;
		
		// Test 3: Number with precision
		Options = Новый Structure;
		Options.Insert("Precision", 2);
		Result = AsString(1234.567, "", "", Options);
		Если НЕ (StrFind(Result, "1234") > 0) Тогда Возврат False; КонецЕсли;
		
		Print("AsString Enhanced tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("AsString Enhanced tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

Функция TestSplitEnhanced()
	Попытка
		// Test 1: Basic split with wrapping
		Result = Split("a,b,c", "[", "]", ",");
		Если Result.Count() <> 3 ИЛИ Result[0] <> "[a]" Тогда Возврат False; КонецЕсли;
		
		// Test 2: Split with options
		Options = Новый Structure;
		Options.Insert("MaxParts", 2);
		Options.Insert("TrimParts", True);
		Result = Split("a, b, c, d", "", "", ",", Options);
		Если Result.Count() <> 2 Тогда Возврат False; КонецЕсли;
		
		Print("Split Enhanced tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("Split Enhanced tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

Функция TestHasTextEnhanced()
	Попытка
		// Test 1: Basic validation
		Если НЕ HasText("Hello") Тогда Возврат False; КонецЕсли;
		Если HasText("   ") Тогда Возврат False; КонецЕсли;
		Если HasText(Undefined) Тогда Возврат False; КонецЕсли;
		
		// Test 2: With options
		Options = Новый Structure;
		Options.Insert("MinLength", 5);
		Options.Insert("RequireAlphanumeric", True);
		Если НЕ HasText("Hello123", Options) Тогда Возврат False; КонецЕсли;
		Если HasText("!@#$", Options) Тогда Возврат False; КонецЕсли;
		
		Print("HasText Enhanced tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("HasText Enhanced tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

Функция TestTextProcessing()
	Попытка
		// Test ExtractBetween
		Result = ExtractBetween("Hello [World] and [Universe]", "[", "]");
		Если Result.Count() <> 2 Тогда Возврат False; КонецЕсли;
		Если Result[0] <> "World" Тогда Возврат False; КонецЕсли;
		
		// Test ReplaceText
		Result = ReplaceText("Hello World", "World", "Universe");
		Если Result <> "Hello Universe" Тогда Возврат False; КонецЕсли;
		
		// Test NormalizeWhitespace
		Result = NormalizeWhitespace("Hello    World   ");
		Если Result <> "Hello World" Тогда Возврат False; КонецЕсли;
		
		Print("Text Processing tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("Text Processing tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

Функция TestStringMetrics()
	Попытка
		// Test CalculateMetrics
		Metrics = CalculateMetrics("Hello World 123");
		Если Metrics.Length <> 15 Тогда Возврат False; КонецЕсли;
		Если Metrics.Words <> 3 Тогда Возврат False; КонецЕсли;
		Если Metrics.Digits <> 3 Тогда Возврат False; КонецЕсли;
		
		// Test CalculateSimilarity
		Similarity = CalculateSimilarity("Hello", "Hello");
		Если Similarity <> 1.0 Тогда Возврат False; КонецЕсли;
		
		Similarity = CalculateSimilarity("ABC", "XYZ");
		Если Similarity >= 1.0 Тогда Возврат False; КонецЕсли;
		
		Print("String Metrics tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("String Metrics tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

Функция TestValidation()
	Попытка
		// Test email validation
		Если НЕ IsValidEmail("user@example.com") Тогда Возврат False; КонецЕсли;
		Если IsValidEmail("invalid.email") Тогда Возврат False; КонецЕсли;
		
		// Test phone validation
		Если НЕ IsValidPhoneNumber("+1-555-123-4567") Тогда Возврат False; КонецЕсли;
		Если IsValidPhoneNumber("abc") Тогда Возврат False; КонецЕсли;
		
		// Test URL validation
		Если НЕ IsValidURL("https://www.example.com") Тогда Возврат False; КонецЕсли;
		Если IsValidURL("not a url") Тогда Возврат False; КонецЕсли;
		
		// Test numeric string
		Если НЕ IsNumericString("12345") Тогда Возврат False; КонецЕсли;
		Если IsNumericString("abc123") Тогда Возврат False; КонецЕсли;
		
		Print("Validation tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("Validation tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

Функция TestTemplates()
	Попытка
		// Test ProcessTemplate
		Template = "Hello, {Name}!";
		Variables = Новый Structure;
		Variables.Insert("Name", "World");
		Result = ProcessTemplate(Template, Variables);
		Если Result <> "Hello, World!" Тогда Возврат False; КонецЕсли;
		
		// Test CreateTemplateBuilder
		Builder = CreateTemplateBuilder();
		Если TypeOf(Builder) <> Type("Structure") Тогда Возврат False; КонецЕсли;
		
		Print("Templates tests: PASSED", "Test", "");
		Возврат True;
		
	Исключение
		Print("Templates tests: FAILED - " + ErrorDescription(), "Test", "");
		Возврат False;
	КонецПопытки;
КонецФункции

#EndRegion

// ---------------------------- EOF М1сAIСтроки ---------------------------------