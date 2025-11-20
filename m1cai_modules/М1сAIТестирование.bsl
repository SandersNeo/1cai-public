// [NEXUS IDENTITY] ID: 2180924897120758556 | DATE: 2025-11-19

﻿// Модуль: М1сAIТестирование
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region PublicInterface

// Создает новую структуру результатов тестирования
//
// Параметры:
//   ModuleName - Строка - имя тестируемого модуля
//
// Возвращаемое значение:
//   Структура - структура результатов тестирования
//
Функция NewTestResult(ModuleName = "") Экспорт
	
	TestResult = Новый Structure;
	TestResult.Insert("ModuleName", ModuleName);
	TestResult.Insert("Success", True);
	TestResult.Insert("TestsTotal", 0);
	TestResult.Insert("TestsPassed", 0);
	TestResult.Insert("TestsFailed", 0);
	TestResult.Insert("TestsSkipped", 0);
	TestResult.Insert("StartTime", CurrentDate());
	TestResult.Insert("EndTime", Undefined);
	TestResult.Insert("Duration", 0);
	TestResult.Insert("Details", Новый Array);
	TestResult.Insert("ErrorLog", "");
	TestResult.Insert("WarningLog", "");
	
	Возврат TestResult;
	
КонецФункции

// Завершает тестирование и фиксирует результат
//
// Параметры:
//   TestResult - Структура - результат тестирования
//
Процедура FinishTesting(TestResult) Экспорт
	
	TestResult.EndTime = CurrentDate();
	TestResult.Duration = TestResult.EndTime - TestResult.StartTime;
	
	// Выводим итоговую статистику
	Если НЕ IsBlankString(TestResult.ModuleName) Тогда
		М1сAIСтроки.Printf("=== ИТОГИ ТЕСТИРОВАНИЯ МОДУЛЯ %1 ===", TestResult.ModuleName);
	Иначе
		М1сAIСтроки.Printf("=== ИТОГИ ТЕСТИРОВАНИЯ ===");
	КонецЕсли;
	
	М1сAIСтроки.Printf("Всего тестов: %1", TestResult.TestsTotal);
	М1сAIСтроки.Printf("Пройдено: %1", TestResult.TestsPassed);
	М1сAIСтроки.Printf("Провалено: %1", TestResult.TestsFailed);
	
	Если TestResult.TestsSkipped > 0 Тогда
		М1сAIСтроки.Printf("Пропущено: %1", TestResult.TestsSkipped);
	КонецЕсли;
	
	М1сAIСтроки.Printf("Время выполнения: %1 сек", TestResult.Duration);
	
	Если TestResult.Success Тогда
		М1сAIСтроки.Printf("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!");
	Иначе
		М1сAIСтроки.Printf("✗ ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ!");
	КонецЕсли;
	
КонецПроцедуры

// Выполняет один тест и обновляет результат
//
// Параметры:
//   TestResult - Структура - структура с результатами тестирования
//   TestName - Строка - имя теста
//   TestFunction - Строка - имя функции теста
//   ModuleName - Строка - имя модуля (необязательно, если функция глобальная)
//
Процедура RunTest(TestResult, TestName, TestFunction, ModuleName = "") Экспорт
	
	TestResult.TestsTotal = TestResult.TestsTotal + 1;
	
	Попытка
		TestPassed = False;
		StartTime = CurrentDate();
		
		// Формируем строку вызова
		Если IsBlankString(ModuleName) Тогда
			CallString = "TestPassed = " + TestFunction + "();";
		Иначе
			CallString = "TestPassed = " + ModuleName + "." + TestFunction + "();";
		КонецЕсли;
		
		Выполнить(CallString);
		
		Duration = CurrentDate() - StartTime;
		
		Если TestPassed Тогда
			TestResult.TestsPassed = TestResult.TestsPassed + 1;
			DetailText = М1сAIСтроки.Printf("✓ %1 - ПРОЙДЕН (%2 мс)", TestName, Duration * 1000);
			TestResult.Details.Add(DetailText);
			М1сAIСтроки.Printf("✓ %1 - ПРОЙДЕН", TestName);
		Иначе
			TestResult.TestsFailed = TestResult.TestsFailed + 1;
			TestResult.Success = False;
			DetailText = М1сAIСтроки.Printf("✗ %1 - ПРОВАЛЕН (%2 мс)", TestName, Duration * 1000);
			TestResult.Details.Add(DetailText);
			TestResult.ErrorLog = TestResult.ErrorLog + TestName + " - тест провален" + Chars.CR;
			М1сAIСтроки.Printf("✗ %1 - ПРОВАЛЕН", TestName);
		КонецЕсли;
		
	Исключение
		TestResult.TestsFailed = TestResult.TestsFailed + 1;
		TestResult.Success = False;
		ErrorText = ErrorDescription();
		DetailText = М1сAIСтроки.Printf("✗ %1 - ОШИБКА: %2", TestName, ErrorText);
		TestResult.Details.Add(DetailText);
		TestResult.ErrorLog = TestResult.ErrorLog + TestName + " - " + ErrorText + Chars.CR;
		М1сAIСтроки.Printf("✗ %1 - ОШИБКА: %2", TestName, ErrorText);
	КонецПопытки;
	
КонецПроцедуры

// Выполняет тест с возможностью пропуска
//
// Параметры:
//   TestResult - Структура - структура с результатами тестирования
//   TestName - Строка - имя теста
//   TestFunction - Строка - имя функции теста
//   SkipCondition - Булево - условие пропуска теста
//   SkipReason - Строка - причина пропуска
//   ModuleName - Строка - имя модуля
//
Процедура RunTestConditional(TestResult, TestName, TestFunction, SkipCondition = False, SkipReason = "", ModuleName = "") Экспорт
	
	Если SkipCondition Тогда
		TestResult.TestsTotal = TestResult.TestsTotal + 1;
		TestResult.TestsSkipped = TestResult.TestsSkipped + 1;
		
		ReasonText = ?(IsBlankString(SkipReason), "условие пропуска", SkipReason);
		DetailText = М1сAIСтроки.Printf("— %1 - ПРОПУЩЕН (%2)", TestName, ReasonText);
		TestResult.Details.Add(DetailText);
		М1сAIСтроки.Printf("— %1 - ПРОПУЩЕН (%2)", TestName, ReasonText);
	Иначе
		RunTest(TestResult, TestName, TestFunction, ModuleName);
	КонецЕсли;
	
КонецПроцедуры

// Выполняет один тест и обновляет результат
//
// Параметры:
//   TestResult - Структура - результат тестирования
//   GroupName - Строка - название группы тестов
//   TestsArray - Массив - массив структур с описанием тестов:
//     * Name - Строка - имя теста
//     * Function - Строка - имя функции
//     * Module - Строка - имя модуля (необязательно)
//     * Skip - Булево - пропустить тест (необязательно)
//     * SkipReason - Строка - причина пропуска (необязательно)
//
Процедура RunTestGroup(TestResult, GroupName, TestsArray) Экспорт
	
	М1сAIСтроки.Printf("--- ГРУППА ТЕСТОВ: %1 ---", GroupName);
	
	Для Каждого TestDescription Из TestsArray Цикл
		
		TestName = TestDescription.Name;
		TestFunction = TestDescription.Function;
		ModuleName = ?(TestDescription.Property("Module"), TestDescription.Module, "");
		SkipTest = ?(TestDescription.Property("Skip"), TestDescription.Skip, False);
		SkipReason = ?(TestDescription.Property("SkipReason"), TestDescription.SkipReason, "");
		
		RunTestConditional(TestResult, TestName, TestFunction, SkipTest, SkipReason, ModuleName);
		
	КонецЦикла;
	
КонецПроцедуры

// Выполняет тестирование всех указанных модулей
//
// Параметры:
//   ModulesArray - Массив - массив имен модулей для тестирования
//   DetailedOutput - Булево - выводить детальную информацию
//
// Возвращаемое значение:
//   Структура - общий результат тестирования всех модулей
//
Функция RunModulesTest(ModulesArray, DetailedOutput = True) Экспорт
	
	OverallResult = NewTestResult("Все модули");
	ModuleResults = Новый Array;
	
	М1сAIСтроки.Printf("=== ЗАПУСК ТЕСТИРОВАНИЯ МОДУЛЕЙ ===");
	М1сAIСтроки.Printf("Модулей для тестирования: %1", ModulesArray.Count());
	
	Для Каждого ModuleName Из ModulesArray Цикл
		
		М1сAIСтроки.Printf("");
		М1сAIСтроки.Printf(">>> Тестирование модуля: %1", ModuleName);
		
		Попытка
			// Вызываем SelfTest модуля
			ModuleResult = Undefined;
			Выполнить("ModuleResult = " + ModuleName + ".SelfTest();");
			
			Если ModuleResult <> Undefined Тогда
				ModuleResults.Add(ModuleResult);
				
				// Суммируем результаты
				OverallResult.TestsTotal = OverallResult.TestsTotal + ModuleResult.TestsTotal;
				OverallResult.TestsPassed = OverallResult.TestsPassed + ModuleResult.TestsPassed;
				OverallResult.TestsFailed = OverallResult.TestsFailed + ModuleResult.TestsFailed;
				
				Если ModuleResult.Property("TestsSkipped") Тогда
					OverallResult.TestsSkipped = OverallResult.TestsSkipped + ModuleResult.TestsSkipped;
				КонецЕсли;
				
				Если НЕ ModuleResult.Success Тогда
					OverallResult.Success = False;
				КонецЕсли;
				
				М1сAIСтроки.Printf("<<< Модуль %1: %2/%3 тестов пройдено",
					ModuleName, ModuleResult.TestsPassed, ModuleResult.TestsTotal);
				
				Если DetailedOutput И ModuleResult.TestsFailed > 0 Тогда
					М1сAIСтроки.Printf("Ошибки в модуле %1:", ModuleName);
					М1сAIСтроки.Printf(ModuleResult.ErrorLog);
				КонецЕсли;
			Иначе
				М1сAIСтроки.Printf("!!! Модуль %1 вернул неопределенный результат", ModuleName);
				OverallResult.Success = False;
				OverallResult.WarningLog = OverallResult.WarningLog +
					"Модуль " + ModuleName + " вернул неопределенный результат" + Chars.CR;
			КонецЕсли;
			
		Исключение
			ErrorText = ErrorDescription();
			М1сAIСтроки.Printf("!!! Ошибка при тестировании модуля %1: %2", ModuleName, ErrorText);
			OverallResult.Success = False;
			OverallResult.ErrorLog = OverallResult.ErrorLog +
				"Модуль " + ModuleName + " - " + ErrorText + Chars.CR;
		КонецПопытки;
		
	КонецЦикла;
	
	OverallResult.Insert("ModuleResults", ModuleResults);
	FinishTesting(OverallResult);
	
	Возврат OverallResult;
	
КонецФункции

#EndRegion

#Region PerformanceTools

// Измеряет производительность выполнения функции
//
// Параметры:
//   FunctionName - Строка - имя функции для тестирования
//   IterationsCount - Число - количество итераций
//   ModuleName - Строка - имя модуля (если требуется)
//   Parameters - Строка - параметры для вызова функции
//
// Возвращаемое значение:
//   Структура - результат измерения производительности
//
Функция MeasurePerformance(FunctionName, IterationsCount = 1000, ModuleName = "", Parameters = "") Экспорт
	
	Result = Новый Structure;
	Result.Insert("FunctionName", FunctionName);
	Result.Insert("ModuleName", ModuleName);
	Result.Insert("IterationsCount", IterationsCount);
	Result.Insert("TotalTime", 0);
	Result.Insert("AverageTime", 0);
	Result.Insert("MinTime", 999999);
	Result.Insert("MaxTime", 0);
	Result.Insert("SuccessfulIterations", 0);
	Result.Insert("ErrorsCount", 0);
	Result.Insert("ErrorLog", "");
	
	// Формируем строку вызова
	Если IsBlankString(ModuleName) Тогда
		Если IsBlankString(Parameters) Тогда
			CallString = FunctionName + "();";
		Иначе
			CallString = FunctionName + "(" + Parameters + ");";
		КонецЕсли;
	Иначе
		Если IsBlankString(Parameters) Тогда
			CallString = ModuleName + "." + FunctionName + "();";
		Иначе
			CallString = ModuleName + "." + FunctionName + "(" + Parameters + ");";
		КонецЕсли;
	КонецЕсли;
	
	М1сAIСтроки.Printf("Измерение производительности: %1 (%2 итераций)", CallString, IterationsCount);
	
	Для i = 1 По IterationsCount Цикл
		
		Попытка
			StartTime = CurrentDate();
			Выполнить(CallString);
			EndTime = CurrentDate();
			
			IterationTime = (EndTime - StartTime) * 1000; // В миллисекундах
			
			Result.TotalTime = Result.TotalTime + IterationTime;
			Result.SuccessfulIterations = Result.SuccessfulIterations + 1;
			
			Если IterationTime < Result.MinTime Тогда
				Result.MinTime = IterationTime;
			КонецЕсли;
			
			Если IterationTime > Result.MaxTime Тогда
				Result.MaxTime = IterationTime;
			КонецЕсли;
			
		Исключение
			Result.ErrorsCount = Result.ErrorsCount + 1;
			Result.ErrorLog = Result.ErrorLog + "Итерация " + i + ": " + ErrorDescription() + Chars.CR;
		КонецПопытки;
		
	КонецЦикла;
	
	Если Result.SuccessfulIterations > 0 Тогда
		Result.AverageTime = Result.TotalTime / Result.SuccessfulIterations;
	КонецЕсли;
	
	// Выводим результаты
	М1сAIСтроки.Printf("Результаты измерения производительности:");
	М1сAIСтроки.Printf("  Успешных итераций: %1/%2", Result.SuccessfulIterations, IterationsCount);
	М1сAIСтроки.Printf("  Общее время: %1 мс", Result.TotalTime);
	М1сAIСтроки.Printf("  Среднее время: %1 мс", Result.AverageTime);
	М1сAIСтроки.Printf("  Минимальное время: %1 мс", Result.MinTime);
	М1сAIСтроки.Printf("  Максимальное время: %1 мс", Result.MaxTime);
	
	Если Result.ErrorsCount > 0 Тогда
		М1сAIСтроки.Printf("  Ошибок: %1", Result.ErrorsCount);
	КонецЕсли;
	
	Возврат Result;
	
КонецФункции

// Сравнивает производительность нескольких функций
//
// Параметры:
//   FunctionsArray - Массив - массив структур с описанием функций:
//     * Name - Строка - имя для отображения
//     * Function - Строка - имя функции
//     * Module - Строка - имя модуля
//     * Parameters - Строка - параметры
//   IterationsCount - Число - количество итераций для каждой функции
//
// Возвращаемое значение:
//   Массив - результаты измерений для каждой функции
//
Функция ComparePerformance(FunctionsArray, IterationsCount = 1000) Экспорт
	
	Results = Новый Array;
	
	М1сAIСтроки.Printf("=== СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ ===");
	
	Для Каждого FunctionDescription Из FunctionsArray Цикл
		
		DisplayName = FunctionDescription.Name;
		FunctionName = FunctionDescription.Function;
		ModuleName = ?(FunctionDescription.Property("Module"), FunctionDescription.Module, "");
		Parameters = ?(FunctionDescription.Property("Parameters"), FunctionDescription.Parameters, "");
		
		М1сAIСтроки.Printf("");
		М1сAIСтроки.Printf("--- Тестирование: %1 ---", DisplayName);
		
		Result = MeasurePerformance(FunctionName, IterationsCount, ModuleName, Parameters);
		Result.Insert("DisplayName", DisplayName);
		Results.Add(Result);
		
	КонецЦикла;
	
	// Выводим сравнительную таблицу
	М1сAIСтроки.Printf("");
	М1сAIСтроки.Printf("=== СРАВНИТЕЛЬНАЯ ТАБЛИЦА ===");
	М1сAIСтроки.Printf("Функция | Среднее время (мс) | Мин (мс) | Макс (мс) | Успешно");
	М1сAIСтроки.Printf("--------|-------------------|----------|-----------|--------");
	
	Для Каждого Result Из Results Цикл
		М1сAIСтроки.Printf("%1 | %2 | %3 | %4 | %5/%6",
			Result.DisplayName,
			Result.AverageTime,
			Result.MinTime,
			Result.MaxTime,
			Result.SuccessfulIterations,
			Result.IterationsCount);
	КонецЦикла;
	
	Возврат Results;
	
КонецФункции

#EndRegion

#Region AssertionHelpers

// Проверяет истинность условия
//
// Параметры:
//   Condition - Булево - проверяемое условие
//   ErrorMessage - Строка - сообщение об ошибке
//
// Возвращаемое значение:
//   Булево - результат проверки
//
Функция Assert(Condition, ErrorMessage = "Утверждение не выполнено") Экспорт
	
	Если НЕ Condition Тогда
		ВызватьИсключение ErrorMessage;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

// Проверяет равенство значений
//
// Параметры:
//   Expected - Произвольный - ожидаемое значение
//   Actual - Произвольный - фактическое значение
//   ErrorMessage - Строка - сообщение об ошибке
//
// Возвращаемое значение:
//   Булево - результат сравнения
//
Функция AssertEquals(Expected, Actual, ErrorMessage = "") Экспорт
	
	Если Expected <> Actual Тогда
		Если IsBlankString(ErrorMessage) Тогда
			ErrorMessage = М1сAIСтроки.Printf("Ожидалось '%1', получено '%2'", Expected, Actual);
		КонецЕсли;
		ВызватьИсключение ErrorMessage;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

// Проверяет неравенство значений
//
// Параметры:
//   NotExpected - Произвольный - значение, которого не должно быть
//   Actual - Произвольный - фактическое значение
//   ErrorMessage - Строка - сообщение об ошибке
//
// Возвращаемое значение:
//   Булево - результат сравнения
//
Функция AssertNotEquals(NotExpected, Actual, ErrorMessage = "") Экспорт
	
	Если NotExpected = Actual Тогда
		Если IsBlankString(ErrorMessage) Тогда
			ErrorMessage = М1сAIСтроки.Printf("Не ожидалось значение '%1'", Actual);
		КонецЕсли;
		ВызватьИсключение ErrorMessage;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

// Проверяет, что значение не пустое
//
// Параметры:
//   Value - Произвольный - проверяемое значение
//   ErrorMessage - Строка - сообщение об ошибке
//
// Возвращаемое значение:
//   Булево - результат проверки
//
Функция AssertNotEmpty(Value, ErrorMessage = "Значение не должно быть пустым") Экспорт
	
	Если Value = Undefined
		ИЛИ (TypeOf(Value) = Type("String") И IsBlankString(Value))
		ИЛИ (TypeOf(Value) = Type("Array") И Value.Count() = 0)
		ИЛИ (TypeOf(Value) = Type("Map") И Value.Count() = 0) Тогда
		
		ВызватьИсключение ErrorMessage;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

// Проверяет тип значения
//
// Параметры:
//   Value - Произвольный - проверяемое значение
//   ExpectedType - Тип, Строка - ожидаемый тип
//   ErrorMessage - Строка - сообщение об ошибке
//
// Возвращаемое значение:
//   Булево - результат проверки типа
//
Функция AssertType(Value, ExpectedType, ErrorMessage = "") Экспорт
	
	ActualType = TypeOf(Value);
	
	Если TypeOf(ExpectedType) = Type("String") Тогда
		ExpectedType = Type(ExpectedType);
	КонецЕсли;
	
	Если ActualType <> ExpectedType Тогда
		Если IsBlankString(ErrorMessage) Тогда
			ErrorMessage = М1сAIСтроки.Printf("Ожидался тип '%1', получен '%2'", ExpectedType, ActualType);
		КонецЕсли;
		ВызватьИсключение ErrorMessage;
	КонецЕсли;
	
	Возврат True;
	
КонецФункции

#EndRegion

#Region ReportGeneration

// Генерирует HTML отчет о результатах тестирования
//
// Параметры:
//   TestResult - Структура - результат тестирования
//   FilePath - Строка - путь для сохранения файла
//
Функция GenerateHTMLReport(TestResult, FilePath = "") Экспорт
	
	HTML = "<!DOCTYPE html>
		|<html>
		|<head>
		|    <meta charset='utf-8'>
		|    <title>Отчет о тестировании модулей</title>
		|    <style>
		|        body { font-family: Arial, sans-serif; margin: 20px; }
		|        .header { background: #f5f5f5; padding: 15px; border-radius: 5px; }
		|        .success { color: green; font-weight: bold; }
		|        .failure { color: red; font-weight: bold; }
		|        .details { margin: 20px 0; }
		|        .test-item { margin: 5px 0; padding: 5px; border-left: 3px solid #ddd; }
		|        .test-passed { border-left-color: green; background: #f0fff0; }
		|        .test-failed { border-left-color: red; background: #fff0f0; }
		|        .test-skipped { border-left-color: orange; background: #fff8dc; }
		|        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
		|        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
		|        th { background: #f5f5f5; }
		|    </style>
		|</head>
		|<body>";
	
	// Заголовок
	HTML = HTML + "<div class='header'>";
	HTML = HTML + "<h1>Отчет о тестировании " + TestResult.ModuleName + "</h1>";
	HTML = HTML + "<p><strong>Дата:</strong> " + Format(TestResult.StartTime, "ДЛФ=DT") + "</p>";
	HTML = HTML + "<p><strong>Длительность:</strong> " + TestResult.Duration + " сек</p>";
	HTML = HTML + "</div>";
	
	// Общая статистика
	HTML = HTML + "<table>";
	HTML = HTML + "<tr><th>Показатель</th><th>Значение</th></tr>";
	HTML = HTML + "<tr><td>Всего тестов</td><td>" + TestResult.TestsTotal + "</td></tr>";
	HTML = HTML + "<tr><td>Пройдено</td><td class='success'>" + TestResult.TestsPassed + "</td></tr>";
	HTML = HTML + "<tr><td>Провалено</td><td class='failure'>" + TestResult.TestsFailed + "</td></tr>";
	
	Если TestResult.Property("TestsSkipped") И TestResult.TestsSkipped > 0 Тогда
		HTML = HTML + "<tr><td>Пропущено</td><td>" + TestResult.TestsSkipped + "</td></tr>";
	КонецЕсли;
	
	Если TestResult.Success Тогда
		HTML = HTML + "<tr><td>Результат</td><td class='success'>УСПЕХ</td></tr>";
	Иначе
		HTML = HTML + "<tr><td>Результат</td><td class='failure'>ЕСТЬ ОШИБКИ</td></tr>";
	КонецЕсли;
	
	HTML = HTML + "</table>";
	
	// Детали тестов
	HTML = HTML + "<div class='details'>";
	HTML = HTML + "<h2>Детали тестирования</h2>";
	
	Для Каждого Detail Из TestResult.Details Цикл
		Если StrFind(Detail, "✓") > 0 Тогда
			HTML = HTML + "<div class='test-item test-passed'>" + Detail + "</div>";
		ИначеЕсли StrFind(Detail, "✗") > 0 Тогда
			HTML = HTML + "<div class='test-item test-failed'>" + Detail + "</div>";
		Иначе
			HTML = HTML + "<div class='test-item test-skipped'>" + Detail + "</div>";
		КонецЕсли;
	КонецЦикла;
	
	HTML = HTML + "</div>";
	
	// Лог ошибок (если есть)
	Если НЕ IsBlankString(TestResult.ErrorLog) Тогда
		HTML = HTML + "<div class='details'>";
		HTML = HTML + "<h2>Лог ошибок</h2>";
		HTML = HTML + "<pre>" + TestResult.ErrorLog + "</pre>";
		HTML = HTML + "</div>";
	КонецЕсли;
	
	HTML = HTML + "</body></html>";
	
	// Сохраняем файл если указан путь
	Если НЕ IsBlankString(FilePath) Тогда
		Попытка
			TextDocument = Новый TextDocument;
			TextDocument.SetText(HTML);
			TextDocument.Write(FilePath, TextEncoding.UTF8);
			М1сAIСтроки.Printf("HTML отчет сохранен: %1", FilePath);
		Исключение
			М1сAIСтроки.Printf("Ошибка сохранения HTML отчета: %1", ErrorDescription());
		КонецПопытки;
	КонецЕсли;
	
	Возврат HTML;
	
КонецФункции

#EndRegion

#Region SelfTest

// Выполняет самотестирование модуля М1сAIТестирование
//
// Возвращаемое значение:
//   Структура - результат тестирования
//
Функция SelfTest() Экспорт
	
	TestResult = NewTestResult("М1сAIТестирование");
	
	RunTest(TestResult, "NewTestResult", "Test_NewTestResult");
	RunTest(TestResult, "Assert", "Test_Assert");
	RunTest(TestResult, "AssertEquals", "Test_AssertEquals");
	RunTest(TestResult, "AssertNotEquals", "Test_AssertNotEquals");
	RunTest(TestResult, "AssertNotEmpty", "Test_AssertNotEmpty");
	RunTest(TestResult, "AssertType", "Test_AssertType");
	
	FinishTesting(TestResult);
	
	Возврат TestResult;
	
КонецФункции

// Тестирует создание структуры результатов
Функция Test_NewTestResult()
	
	Result = М1сAIТестирование.NewTestResult("TestModule");
	
	Возврат Result.ModuleName = "TestModule"
		И Result.Success = True
		И Result.TestsTotal = 0
		И Result.TestsPassed = 0
		И Result.TestsFailed = 0
		И TypeOf(Result.Details) = Type("Array")
		И TypeOf(Result.StartTime) = Type("Date");
	
КонецФункции

// Тестирует функцию Assert
Функция Test_Assert()
	
	Попытка
		М1сAIТестирование.Assert(True);
		Попытка
			М1сAIТестирование.Assert(False);
			Возврат False; // Не должны дойти до этой строки
		Исключение
			Возврат True; // Ожидали исключение
		КонецПопытки;
	Исключение
		Возврат False;
	КонецПопытки;
	
КонецФункции

// Тестирует функцию AssertEquals
Функция Test_AssertEquals()
	
	Попытка
		М1сAIТестирование.AssertEquals("Test", "Test");
		М1сAIТестирование.AssertEquals(123, 123);
		Попытка
			М1сAIТестирование.AssertEquals("A", "B");
			Возврат False; // Не должны дойти до этой строки
		Исключение
			Возврат True; // Ожидали исключение
		КонецПопытки;
	Исключение
		Возврат False;
	КонецПопытки;
	
КонецФункции

// Тестирует функцию AssertNotEquals
Функция Test_AssertNotEquals()
	
	Попытка
		М1сAIТестирование.AssertNotEquals("A", "B");
		Попытка
			М1сAIТестирование.AssertNotEquals("A", "A");
			Возврат False; // Не должны дойти до этой строки
		Исключение
			Возврат True; // Ожидали исключение
		КонецПопытки;
	Исключение
		Возврат False;
	КонецПопытки;
	
КонецФункции

// Тестирует функцию AssertNotEmpty
Функция Test_AssertNotEmpty()
	
	Попытка
		М1сAIТестирование.AssertNotEmpty("NotEmpty");
		М1сAIТестирование.AssertNotEmpty(123);
		
		Попытка
			М1сAIТестирование.AssertNotEmpty("");
			Возврат False; // Не должны дойти до этой строки
		Исключение
			Попытка
				М1сAIТестирование.AssertNotEmpty(Undefined);
				Возврат False; // Не должны дойти до этой строки
			Исключение
				Возврат True; // Ожидали исключения
			КонецПопытки;
		КонецПопытки;
	Исключение
		Возврат False;
	КонецПопытки;
	
КонецФункции

// Тестирует функцию AssertType
Функция Test_AssertType()
	
	Попытка
		М1сAIТестирование.AssertType("Test", Type("String"));
		М1сAIТестирование.AssertType(123, "Number");
		
		Попытка
			М1сAIТестирование.AssertType("Test", Type("Number"));
			Возврат False; // Не должны дойти до этой строки
		Исключение
			Возврат True; // Ожидали исключение
		КонецПопытки;
	Исключение
		Возврат False;
	КонецПопытки;
	
КонецФункции

#EndRegion

#Region Examples

////////////////////////////////////////////////////////////////////////////////
// ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ М1сAIТестирование
////////////////////////////////////////////////////////////////////////////////

// Пример 1: Простое тестирование модуля
// TestResult = М1сAIТестирование.NewTestResult("МойМодуль");
// М1сAIТестирование.RunTest(TestResult, "Тест создания", "Test_Creation", "МойМодуль");
// М1сAIТестирование.FinishTesting(TestResult);

// Пример 2: Тестирование через соответствие
// TestsMap = New Map;
// TestsMap.Insert("Создание объекта", "Test_NewObject");
// TestsMap.Insert("Копирование", "Test_Copy");
// TestsMap.Insert("Очистка", "Test_Clear");
// М1сAIТестирование.RunTestsFromMap(TestResult, TestsMap, "МойМодуль");

// Пример 3: Условное тестирование
// TestsMap = New Map;
// TestsMap.Insert("Быстрый тест", "Test_Fast");
// TestsMap.Insert("Медленный тест", New Structure("Function,Skip,SkipReason",
//     "Test_Slow", True, "занимает много времени"));
// М1сAIТестирование.RunConditionalTestsFromMap(TestResult, TestsMap, "МойМодуль");

// Пример 4: Групповое тестирование
// TestGroup = New Array;
// TestGroup.Add(New Structure("Name,Function", "Тест 1", "Test_One"));
// TestGroup.Add(New Structure("Name,Function,Skip,SkipReason",
//     "Тест 2", "Test_Two", True, "не готов"));
// М1сAIТестирование.RunTestGroup(TestResult, "Основные тесты", TestGroup);

// Пример 5: Тестирование всех модулей
// ModulesArray = New Array;
// ModulesArray.Add("М1сAIСоответствия");
// ModulesArray.Add("М1сAIМассивы");
// ModulesArray.Add("М1сAIСтруктуры");
// OverallResult = М1сAIТестирование.RunModulesTest(ModulesArray, True);

// Пример 6: Использование утверждений в тестах
// Function Test_MyFunction()
//
//     Result = МойМодуль.МояФункция("параметр");
//
//     М1сAIТестирование.AssertNotEmpty(Result, "Результат не должен быть пустым");
//     М1сAIТестирование.AssertType(Result, Type("String"), "Результат должен быть строкой");
//     М1сAIТестирование.AssertEquals("ожидаемый результат", Result, "Неверный результат");
//
//     Return True;
//
// EndFunction

// Пример 7: Измерение производительности
// PerformanceResult = М1сAIТестирование.MeasurePerformance("МояФункция", 1000, "МойМодуль", "'параметр'");

// Пример 8: Сравнение производительности функций
// FunctionsArray = New Array;
// FunctionsArray.Add(New Structure("Name,Function,Module",
//     "Старая реализация", "ОldFunction", "МойМодуль"));
// FunctionsArray.Add(New Structure("Name,Function,Module",
//     "Новая реализация", "NewFunction", "МойМодуль"));
// ComparisonResult = М1сAIТестирование.ComparePerformance(FunctionsArray, 500);

// Пример 9: Генерация HTML отчета
// TestResult = МойМодуль.SelfTest();
// HTMLReport = М1сAIТестирование.GenerateHTMLReport(TestResult, "C:\Temp\TestReport.html");

// Пример 10: Комплексное тестирование с отчетом
// Function CompleteModuleTesting()
//
//     TestResult = М1сAIТестирование.NewTestResult("МойМодуль");
//
//     // Создаем план тестирования
//     TestsMap = New Map;
//     TestsMap.Insert("Базовая функциональность", "Test_Basic");
//     TestsMap.Insert("Обработка ошибок", "Test_ErrorHandling");
//     TestsMap.Insert("Граничные случаи", "Test_EdgeCases");
//     TestsMap.Insert("Производительность", New Structure("Function,Skip,SkipReason",
//         "Test_Performance", False, ""));
//
//     // Выполняем тестирование
//     М1сAIТестирование.RunConditionalTestsFromMap(TestResult, TestsMap, "МойМодуль");
//     М1сAIТестирование.FinishTesting(TestResult);
//
//     // Генерируем отчет
//     If TestResult.TestsFailed = 0 Then
//         М1сAIТестирование.GenerateHTMLReport(TestResult, "Reports\Success_" + Format(CurrentDate(), "ДФ=yyyy-MM-dd_HH-mm-ss") + ".html");
//     Else
//         М1сAIТестирование.GenerateHTMLReport(TestResult, "Reports\Failed_" + Format(CurrentDate(), "ДФ=yyyy-MM-dd_HH-mm-ss") + ".html");
//         М1сAIEventLog.Write("Тестирование провалено: " + TestResult.ErrorLog);
//     EndIf;
//
//     Return TestResult;
//
// EndFunction

#EndRegion