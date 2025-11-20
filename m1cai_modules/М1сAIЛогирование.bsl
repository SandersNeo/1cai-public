// [NEXUS IDENTITY] ID: -346542007408222439 | DATE: 2025-11-19

﻿// Модуль: М1сAIЛогирование
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


//^tree[М1сAIЛогирование]
//М1сAIЛогирование
//├── GetLevels / ПолучитьУровни
//│   └── Function GetLevels( Information =True, Error =False, Warning =False, Note =False )
//├── GetLog / ПолучитьЖурнал
//│   └── Function GetLog( ДатаНачала, ДатаОкончания, EnsureDayBounds =True )
//├── Show / Показать
//│   └── Procedure Show( ДатаНачала, ДатаОкончания, FilterBy ="" )
//├── Write / Записать (+ Info/Инфо, Error/Ошибка, Warn/Предупреждение, Note/Заметка, Debug/Отладка)
//│   ├── Procedure Write( text="", showTime=False, event="", logLevel=Undefined )
//│   ├── Procedure Info( EventName="", EventComment="", withTime=False ) / Инфо
//│   ├── Procedure Error( EventName, EventComment ) / Ошибка
//│   ├── Procedure Warn( EventName, EventComment ) / Предупреждение
//│   ├── Procedure Note( EventName, EventComment ) / Заметка
//│   ├── Procedure Debug( EventName="", EventComment="", withTime=False ) / Отладка
//│   ├── Procedure InfoJSON( EventName="", EventData=Undefined ) / ИнфоJSON
//│   ├── Procedure ErrorJSON( EventName, EventData ) / ОшибкаJSON
//│   ├── Procedure WarnJSON( EventName, EventData ) / ПредупреждениеJSON
//│   ├── Procedure NoteJSON( EventName, EventData ) / ЗаметкаJSON
//│   └── Procedure DebugJSON( EventName, EventData ) / ОтладкаJSON
//├── Configuration
//│   └── Function CreateConfig() / СоздатьКонфиг()
//├── Context
//│   ├── Function CreateContext( CustomFields = Undefined ) / СоздатьКонтекст()
//│   └── Function ContextWithField( Context, FieldName, FieldValue ) / КонтекстСПолем()
//├── Performance
//│   ├── Function StartPerformanceTimer( OperationName, Context = Undefined ) / НачатьИзмерение()
//│   └── Procedure StopPerformanceTimer( Timer, AdditionalData = Undefined, Config = Undefined, Context = Undefined ) / ЗавершитьИзмерение()
//├── Invoke
//│   └── Function InvokeCallable( Callable ) / ВызватьПоИмени()
//├── Measure
//│   └── Function MeasureExecution( OperationName, Method, Parameters = Undefined, Config = Undefined, Context = Undefined ) / ИзмеритьВыполнение()
//├── StructuredLogging
//│   ├── Function ShouldLog( Level, Config = Undefined ) / СледуетЛогировать()
//│   ├── Function FormatMessage( Template, Properties ) / ФорматСообщения()
//│   ├── Function GetStackTrace() / ПолучитьСтек()
//│   ├── Function LevelToString( Level ) / УровеньВСтроку()
//│   ├── Function ParseEventLogLevel( LevelAny ) / СтрокаВУровеньСобытия()
//│   ├── Procedure WriteStructured( Level, Template, Properties = Undefined, Exception = Undefined, Config = Undefined, Context = Undefined ) / ЗаписатьСтруктурировано()
//│   ├── Procedure OutputToTargets( LogEvent, Config ) / ВывестиВСцели()
//│   ├── Procedure OutputToEventLog( LogEvent ) / ВывестиВЖурналСобытий()
//│   ├── Procedure OutputToConsole( LogEvent ) / ВывестиВКонсоль()
//│   └── Procedure OutputToFile( LogEvent ) / ВывестиВФайл()
//├── ModernShortcuts
//│   ├── Procedure InfoStructured( Template, Properties = Undefined, Config = Undefined, Context = Undefined ) / ИнфоСтруктурно()
//│   ├── Procedure WarnStructured( Template, Properties = Undefined, Config = Undefined, Context = Undefined ) / ПредупреждениеСтруктурно()
//│   ├── Procedure ErrorStructured( Template, Properties = Undefined, Exception = Undefined, Config = Undefined, Context = Undefined ) / ОшибкаСтруктурно()
//│   ├── Procedure NoteStructured( Template, Properties = Undefined, Config = Undefined, Context = Undefined ) / ЗаметкаСтруктурно()
//│   ├── Procedure BeginOperation( OperationName, Properties = Undefined, Config = Undefined, Context = Undefined ) / НачалоОперации()
//│   └── Procedure EndOperation( OperationName, Success = True, Properties = Undefined, Config = Undefined, Context = Undefined ) / КонецОперации()
//└── SelfTest / СамоТест
//    ├── Function SelfTest() / СамоТест()
//    ├── Function Examples() / Примеры()
//    └── Function ModernSelfTest() / СовременныйСамоТест()

#Region М1сAIЛогирование_ModuleMap
// М1сAIЛогирование (flags: Server + External connection)
// Requires: М1сAIСтроки, М1сAIСимволы, М1сAIJSON
//
// Regions:
//   GetLevels / ПолучитьУровни    – Формирует список уровней журнала
//   GetLog / ПолучитьЖурнал       – Извлекает события за период
//   Show / Показать               – Вывод и запись событий
//   Write / Записать              – Базовый метод записи + краткие уровни + JSON
//   Configuration                 – Создание конфигурации логгера
//   Context                       – Контекст логирования и утилиты
//   Performance                   – Старт/стоп измерений времени
//   Invoke                        – Безопасный вызов функций по имени
//   Measure                       – Обёртка измерения выполнения функции
//   StructuredLogging             – Современное структурированное логирование
//   ModernShortcuts               – Короткие процедуры structured-логирования и трейсинга
//   SelfTest / СамоТест           – Юнит-тесты и примеры
#EndRegion

#Region М1сAIЛогирование_GetLevels
// <doc>
//   <summary>Формирует массив перечислений уровней логирования.</summary>   ✦
//   <param i="1" name="Information" type="Boolean" default="True">Включить Information.</param>
//   <param i="2" name="Error" type="Boolean" default="False">Включить Error.</param>
//   <param i="3" name="Warning" type="Boolean" default="False">Включить Warning.</param>
//   <param i="4" name="Note" type="Boolean" default="False">Включить Note.</param>
//   <returns>Array — значения EventLogLevel.</returns>
//   <complexity cc="1"/>
// </doc>
Функция GetLevels(Information = True, Error = False, Warning = False, Note = False) Экспорт //⚙
	ib = "Построение набора уровней логирования"; //✍
	Levels = Новый Array; //✏
	Если Boolean(Information) Тогда Levels.Add(EventLogLevel.Information); КонецЕсли;
	Если Boolean(Error) Тогда Levels.Add(EventLogLevel.Error); КонецЕсли;
	Если Boolean(Warning) Тогда Levels.Add(EventLogLevel.Warning); КонецЕсли;
	Если Boolean(Note) Тогда Levels.Add(EventLogLevel.Note); КонецЕсли;
	Возврат Levels; //↩
КонецФункции

// <doc>
//   <summary>Русский алиас для GetLevels.</summary>   ✦
//   <returns>Array — значения EventLogLevel.</returns>
//   <complexity cc="1"/>
// </doc>
Функция ПолучитьУровни(Information = True, Error = False, Warning = False, Note = False) Экспорт //⚙
	ib = "Алиас GetLevels (RU)"; //✍
	Возврат GetLevels(Information, Error, Warning, Note); //↩
КонецФункции

#Region examples_М1сAIЛогирование_GetLevels
// Пример:
// Levels = М1сAIЛогирование.GetLevels(True, True);
// УровниЖурнала = М1сAIЛогирование.ПолучитьУровни(True, True);
#EndRegion
#EndRegion

#Region М1сAIЛогирование_GetLog
// <doc>
//   <summary>Возвращает текст лог-событий за период; опционально нормализует границы дат.</summary>   ✦
//   <param i="1" name="ДатаНачала" type="Date">Начало периода.</param>
//   <param i="2" name="ДатаОкончания" type="Date">Конец периода.</param>
//   <param i="3" name="EnsureDayBounds" type="Boolean" default="True">Истина — обрезать до начала/конца дня.</param>
//   <returns>String — конкатенированный текст событий.</returns>
//   <complexity cc="5"/>
// </doc>
Функция GetLog(ДатаНачала, ДатаОкончания, EnsureDayBounds = True) Экспорт //⚙
	ib = "Сбор событий журнала за период"; //✍
	
	Если Boolean(EnsureDayBounds) Тогда //⚡
		startDate = НачалоДня(ДатаНачала); //✏
		endDate = КонецДня(ДатаОкончания); //✏
	Иначе
		startDate = ДатаНачала; //✏
		endDate = ДатаОкончания; //✏
	КонецЕсли;
	
	Данные = Новый ValueTable; //✏
	Отбор = Новый Structure("ДатаНачала, ДатаОкончания", Date(startDate), Date(endDate)); //✏
	
	SetPrivilegedMode(True); //▶️
	Попытка //✱
		UnloadEventLog(Данные, Отбор); //▶️
	Исключение
		М1сAIЛогирование.Write(ErrorDescription()); //▶️
	КонецПопытки;
	SetPrivilegedMode(False); //▶️
	
	Result = ""; //✏
	Для Каждого r Из Данные Цикл //⟳
		Попытка //✱
			Если ValueIsFilled(r.Comment) ИЛИ ValueIsFilled(r.DataPresentation) Тогда //⚡
				ТекстСобытия = String(r.Date) + " " + String(r.Event) + " " +
					StrReplace(String(r.Comment), Chars.CR, " ") + " " +
					String(r.DataPresentation) + Chars.CR; //✏
				Message(ТекстСобытия); //▶️
				Result = Result + ТекстСобытия; //✏
			КонецЕсли;
		Исключение КонецПопытки;
		
		Попытка //✱
			Если ValueIsFilled(r.Комментарий) ИЛИ ValueIsFilled(r.ПредставлениеДанных) Тогда //⚡
				ТекстСобытия = String(r.Дата) + " " + String(r.Событие) + " " +
					StrReplace(String(r.Комментарий), Chars.CR, " ") + " " +
					String(r.ПредставлениеДанных) + Chars.CR; //✏
				Message(ТекстСобытия); //▶️
				Result = Result + ТекстСобытия; //✏
			КонецЕсли;
		Исключение КонецПопытки;
	КонецЦикла;
	
	Возврат Result; //↩
КонецФункции

// <doc>
//   <summary>Русский алиас для GetLog.</summary>   ✦
//   <returns>String — конкатенированный текст событий.</returns>
//   <complexity cc="1"/>
// </doc>
Функция ПолучитьЖурнал(ДатаНачала, ДатаОкончания, EnsureDayBounds = True) Экспорт //⚙
	ib = "Алиас GetLog (RU)"; //✍
	Возврат GetLog(ДатаНачала, ДатаОкончания, EnsureDayBounds); //↩
КонецФункции

#Region examples_М1сAIЛогирование_GetLog
// Пример:
// LogText = М1сAIЛогирование.GetLog(Date("20250101"), Date("20250102"));
// ТекстЖурнала = М1сAIЛогирование.ПолучитьЖурнал(Date("20250101"), Date("20250102"));
#EndRegion
#EndRegion

#Region М1сAIЛогирование_Show
// <doc>
//   <summary>Выводит и записывает события журнала за период.</summary>   ✦
//   <param i="1" name="ДатаНачала" type="Date">Начало периода.</param>
//   <param i="2" name="ДатаОкончания" type="Date">Конец периода.</param>
//   <param i="3" name="FilterBy" type="String" optional="True">Фильтр по тексту (необязательно).</param>
//   <returns>Void</returns>
//   <complexity cc="2"/>
// </doc>
Процедура Show(ДатаНачала, ДатаОкончания, FilterBy = "") Экспорт //⚙
	ib = "Показ журнала и запись в лог"; //✍
	Текст = GetLog(ДатаНачала, ДатаОкончания); //▶️
	М1сAIЛогирование.Write(Текст, , Chars.CR, FilterBy); //▶️
КонецПроцедуры

// <doc>
//   <summary>Русский алиас для Show.</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="1"/>
// </doc>
Процедура Показать(ДатаНачала, ДатаОкончания, FilterBy = "") Экспорт //⚙
	ib = "Алиас Show (RU)"; //✍
	Show(ДатаНачала, ДатаОкончания, FilterBy); //▶️
КонецПроцедуры

#Region examples_М1сAIЛогирование_Show
// Пример:
// М1сAIЛогирование.Show(Date("20250101"), Date("20250102"), "Error");
// М1сAIЛогирование.Показать(Date("20250101"), Date("20250102"), "Error");
#EndRegion
#EndRegion

#Region М1сAIЛогирование_Write
// <doc>
//   <summary>Записывает событие в системный журнал (WriteLogEvent).</summary>   ✦
//   <param i="1" name="text" type="String" optional="True">Описание события.</param>
//   <param i="2" name="showTime" type="Boolean" default="False">Добавить метку времени к имени.</param>
//   <param i="3" name="event" type="String" optional="True">Имя события (если пусто — берётся text).</param>
//   <param i="4" name="logLevel" type="EventLogLevel" optional="True">Уровень (по умолчанию Information).</param>
//   <returns>Void</returns>
//   <complexity cc="4"/>
// </doc>
Процедура Write(text = "", showTime = False, event = "", logLevel = Undefined) Экспорт //⚙
	ib = "Базовая запись в WriteLogEvent"; //✍
	Если logLevel = Undefined Тогда logLevel = EventLogLevel.Information; КонецЕсли; //⚡
	Попытка //✱
		Title =
			?(Boolean(showTime), "[" + CurrentDate() + "] ", "") +
			?(event = "", ?(text = "", "--", String(text)), String(event)); //✏
		WriteLogEvent(Title, logLevel, , , String(?(text = "", "--", String(text)))); //▶️
	Исключение
		WriteLogEvent(ErrorDescription(), EventLogLevel.Error, , , ErrorDescription()); //▶️
	КонецПопытки;
КонецПроцедуры

/// <summary>Русский алиас для Write.</summary>
/// <param name="text" type="String">Описание события (комментарий).</param>
/// <param name="showTime" type="Boolean" optional="True">Добавить метку времени к имени события.</param>
/// <param name="event" type="String" optional="True">Имя события (если пусто — берётся текст).</param>
/// <param name="logLevel" type="EventLogLevel" optional="True">Уровень события.</param>
Процедура Записать(text = "", showTime = False, event = "", logLevel = Undefined) Экспорт //⚙
	ib = "Русский алиас для Write"; //✍
	Write(text, showTime, event, logLevel); //▶️
КонецПроцедуры

// <doc><summary>Информационное событие.</summary>   ✦</doc>
Процедура Info(EventName = "", EventComment = "", withTime = False) Экспорт //⚙
	ib = "Информационное событие"; //✍
	Write(EventName, withTime, EventComment, EventLogLevel.Information); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для Info.</summary>   ✦</doc>
Процедура Инфо(EventName = "", EventComment = "", withTime = False) Экспорт //⚙
	ib = "Алиас Info (RU)"; //✍
	Info(EventName, EventComment, withTime); //▶️
КонецПроцедуры

// <doc><summary>Ошибка.</summary>   ✦</doc>
Процедура Error(EventName = "", EventComment = "") Экспорт //⚙
	ib = "Событие ошибки"; //✍
	Write(EventName, True, EventComment, EventLogLevel.Error); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для Error.</summary>   ✦</doc>
Процедура Ошибка(EventName = "", EventComment = "") Экспорт //⚙
	ib = "Алиас Error (RU)"; //✍
	Error(EventName, EventComment); //▶️
КонецПроцедуры

// <doc><summary>Предупреждение.</summary>   ✦</doc>
Процедура Warn(EventName = "", EventComment = "") Экспорт //⚙
	ib = "Событие предупреждения"; //✍
	Write(EventName, True, EventComment, EventLogLevel.Warning); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для Warn.</summary>   ✦</doc>
Процедура Предупреждение(EventName = "", EventComment = "") Экспорт //⚙
	ib = "Алиас Warn (RU)"; //✍
	Warn(EventName, EventComment); //▶️
КонецПроцедуры

// <doc><summary>Заметка.</summary>   ✦</doc>
Процедура Note(EventName = "", EventComment = "") Экспорт //⚙
	ib = "Событие заметки"; //✍
	Write(EventName, True, EventComment, EventLogLevel.Note); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для Note.</summary>   ✦</doc>
Процедура Заметка(EventName = "", EventComment = "") Экспорт //⚙
	ib = "Алиас Note (RU)"; //✍
	Note(EventName, EventComment); //▶️
КонецПроцедуры

// <doc><summary>Отладка (уровень Note).</summary>   ✦</doc>
Процедура Debug(EventName = "", EventComment = "", withTime = False) Экспорт //⚙
	ib = "Отладочное событие"; //✍
	Write(EventName, withTime, EventComment, EventLogLevel.Note); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для Debug.</summary>   ✦</doc>
Процедура Отладка(EventName = "", EventComment = "", withTime = False) Экспорт //⚙
	ib = "Алиас Debug (RU)"; //✍
	Debug(EventName, EventComment, withTime); //▶️
КонецПроцедуры

// <doc><summary>Информационное событие с JSON данными.</summary>   ✦</doc>
Процедура InfoJSON(EventName = "", EventData = Undefined) Экспорт //⚙
	ib = "Info + JSON"; //✍
	JSONString = М1сAIJSON.ToJSON(EventData); //▶️
	Info(EventName, JSONString); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для InfoJSON.</summary>   ✦</doc>
Процедура ИнфоJSON(EventName = "", EventData = Undefined) Экспорт //⚙
	ib = "Алиас InfoJSON (RU)"; //✍
	InfoJSON(EventName, EventData); //▶️
КонецПроцедуры

// <doc><summary>Ошибка с JSON данными.</summary>   ✦</doc>
Процедура ErrorJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Error + JSON"; //✍
	JSONString = М1сAIJSON.ToJSON(EventData); //▶️
	Error(EventName, JSONString); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для ErrorJSON.</summary>   ✦</doc>
Процедура ОшибкаJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Алиас ErrorJSON (RU)"; //✍
	ErrorJSON(EventName, EventData); //▶️
КонецПроцедуры

// <doc><summary>Предупреждение с JSON данными.</summary>   ✦</doc>
Процедура WarnJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Warn + JSON"; //✍
	JSONString = М1сAIJSON.ToJSON(EventData); //▶️
	Warn(EventName, JSONString); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для WarnJSON.</summary>   ✦</doc>
Процедура ПредупреждениеJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Алиас WarnJSON (RU)"; //✍
	WarnJSON(EventName, EventData); //▶️
КонецПроцедуры

// <doc><summary>Заметка с JSON данными.</summary>   ✦</doc>
Процедура NoteJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Note + JSON"; //✍
	JSONString = М1сAIJSON.ToJSON(EventData); //▶️
	Note(EventName, JSONString); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для NoteJSON.</summary>   ✦</doc>
Процедура ЗаметкаJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Алиас NoteJSON (RU)"; //✍
	NoteJSON(EventName, EventData); //▶️
КонецПроцедуры

// <doc><summary>Отладка с JSON данными.</summary>   ✦</doc>
Процедура DebugJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Debug + JSON"; //✍
	JSONString = М1сAIJSON.ToJSON(EventData); //▶️
	Debug(EventName, JSONString); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для DebugJSON.</summary>   ✦</doc>
Процедура ОтладкаJSON(EventName = "", EventData) Экспорт //⚙
	ib = "Алиас DebugJSON (RU)"; //✍
	DebugJSON(EventName, EventData); //▶️
КонецПроцедуры
#EndRegion

#Region М1сAIЛогирование_SelfTest
// <doc>
//   <summary>Выполняет тесты для М1сAIЛогирование.</summary>   ✦
//   <returns>Boolean — Истина при успешном прохождении тестов.</returns>
//   <complexity cc="5"/>
// </doc>
Функция SelfTest() Экспорт //⚙
	ib = "Базовая самопроверка модуля логирования"; //✍
	
	lvl = GetLevels(True, True); //▶️
	Если lvl.Count() <> 2 Тогда //⚡
		М1сAIСтроки.Print("SelfTest FAILED: GetLevels", "SelfTest", ""); //▶️
		Возврат False; //↩
	КонецЕсли;
	
	Попытка //✱
		logText = GetLog(CurrentDate(), CurrentDate()); //▶️
	Исключение
		М1сAIСтроки.Print("SelfTest FAILED: GetLog threw error", "SelfTest", ""); //▶️
		Возврат False; //↩
	КонецПопытки;
	
	Если TypeOf(logText) <> Type("String") Тогда //⚡
		М1сAIСтроки.Print("SelfTest FAILED: GetLog returned non-string", "SelfTest", ""); //▶️
		Возврат False; //↩
	КонецЕсли;
	
	Info("t1", "c1"); Error("t2", "c2"); Warn("t3", "c3"); Note("t4", "c4"); Debug("t5", "c5"); //▶️
	
	Попытка //✱
		TestData = Новый Structure("test", "value"); //✏
		InfoJSON("JSONTest", TestData); //▶️
	Исключение
		М1сAIСтроки.Print("SelfTest FAILED: JSON methods error", "SelfTest", ""); //▶️
		Возврат False; //↩
	КонецПопытки;
	
	М1сAIСтроки.Print("М1сAIЛогирование: SelfTest passed", "SelfTest", ""); //▶️
	Возврат True; //↩
КонецФункции

// <doc>
//   <summary>Русский алиас для SelfTest.</summary>   ✦
//   <returns>Boolean — Истина при успешном прохождении тестов.</returns>
//   <complexity cc="1"/>
// </doc>
Функция СамоТест() Экспорт //⚙
	ib = "Алиас SelfTest (RU)"; //✍
	Возврат SelfTest(); //↩
КонецФункции

// <doc>
//   <summary>Демонстрирует все функции модуля М1сAIЛогирование с примерами.</summary>   ✦
//   <returns>Boolean — Истина, если примеры выполнены успешно.</returns>
//   <complexity cc="5"/>
// </doc>
Функция Examples() Экспорт //⚙
	ib = "Демонстрация функций модуля"; //✍
	Попытка //✱
		// === Базовые ===
		М1сAIЛогирование.Write("Базовая запись в журнал"); //▶️
		М1сAIЛогирование.Write("Запись с меткой времени", True); //▶️
		М1сAIЛогирование.Write("Запись с событием и комментарием", False, "TestEvent"); //▶️
		
		// === Уровни ===
		М1сAIЛогирование.Info("ApplicationStart", "Приложение запущено"); //▶️
		М1сAIЛогирование.Error("DatabaseError", "Ошибка подключения к базе данных"); //▶️
		М1сAIЛогирование.Warn("MemoryWarning", "Использовано 90% памяти"); //▶️
		М1сAIЛогирование.Note("UserAction", "Пользователь выполнил действие"); //▶️
		М1сAIЛогирование.Debug("DebugInfo", "Значение переменной: x=42"); //▶️
		
		// === RU алиасы ===
		М1сAIЛогирование.Инфо("ИнфоСобытие", "Информационное сообщение"); //▶️
		М1сAIЛогирование.Ошибка("ОшибкаСистемы", "Системная ошибка"); //▶️
		М1сAIЛогирование.Предупреждение("ПредупреждениеСистемы", "Системное предупреждение"); //▶️
		М1сAIЛогирование.Заметка("ЗаметкаПользователя", "Заметка пользователя"); //▶️
		М1сAIЛогирование.Отладка("ОтладочнаяИнформация", "Отладочные данные"); //▶️
		
		// === JSON ===
		UserData = Новый Structure("Login, IP", "admin", "192.168.1.100"); //✏
		М1сAIЛогирование.InfoJSON("UserLogin", UserData); //▶️
		
		ErrorData = Новый Structure("ErrorCode, ErrorMessage, URL", 404, "Страница не найдена", "/nonexistent-page"); //✏
		М1сAIЛогирование.ErrorJSON("HTTPError", ErrorData); //▶️
		
		WarnData = Новый Structure("ResourceType, CurrentUsage, MaxUsage", "Memory", 85.7, 100); //✏
		М1сAIЛогирование.WarnJSON("ResourceWarning", WarnData); //▶️
		
		NoteData = Новый Structure("ProcessName, RecordsProcessed, Duration", "DataSync", 1500, "00:05:30"); //✏
		М1сAIЛогирование.NoteJSON("ProcessComplete", NoteData); //▶️
		
		DebugData = Новый Structure; //✏
		DebugData.Insert("FunctionName", "CalculateTotal");
		DebugData.Insert("Parameters", Новый Array);
		DebugData.Parameters.Add("param1=100");
		DebugData.Parameters.Add("param2=200");
		DebugData.Insert("Result", 300);
		М1сAIЛогирование.DebugJSON("FunctionCall", DebugData); //▶️
		
		// === Уровни выборки ===
		УровниВсе = М1сAIЛогирование.GetLevels(True, True, True, True); //▶️
		Message("Всего уровней: " + УровниВсе.Count()); //▶️
		
		УровниОшибки = М1сAIЛогирование.ПолучитьУровни(False, True, False, False); //▶️
		Message("Уровней ошибок: " + УровниОшибки.Count()); //▶️
		
		// === Получение журнала ===
		СегодняЖурнал = М1сAIЛогирование.GetLog(CurrentDate(), CurrentDate()); //▶️
		Message("Размер журнала за сегодня: " + StrLen(СегодняЖурнал) + " символов"); //▶️
		
		ВчераСегодня = М1сAIЛогирование.ПолучитьЖурнал(CurrentDate() - 86400, CurrentDate()); //▶️
		Message("Размер журнала за вчера-сегодня: " + StrLen(ВчераСегодня) + " символов"); //▶️
		
		М1сAIЛогирование.Info("ExamplesComplete", "Все примеры выполнены успешно!"); //▶️
		Возврат True; //↩
	Исключение
		М1сAIЛогирование.Error("ExamplesError", "Ошибка при выполнении примеров: " + ErrorDescription()); //▶️
		Возврат False; //↩
	КонецПопытки;
КонецФункции

// <doc>
//   <summary>Русский алиас для Examples.</summary>   ✦
//   <returns>Boolean — Истина, если примеры выполнены успешно.</returns>
//   <complexity cc="1"/>
// </doc>
Функция Примеры() Экспорт //⚙
	ib = "Алиас Examples (RU)"; //✍
	Возврат Examples(); //↩
КонецФункции
#EndRegion

// ---------------------------- EOF М1сAIЛогирование ---------------------------------

#Region М1сAIЛогирование_Configuration
// <doc>
//   <summary>Создать конфигурацию логгера по умолчанию (stateless).</summary>   ✦
//   <returns>Structure — настройки (MinLevel, OutputTargets и др.).</returns>
//   <complexity cc="1"/>
// </doc>
Функция CreateConfig() Экспорт //⚙
	ib = "Создание конфигурации по умолчанию"; //✍
	Config = Новый Structure; //✏
	Config.Insert("MinLevel", EventLogLevel.Information);
	Config.Insert("MaxLogSize", 50 * 1024 * 1024);
	Config.Insert("RotateOnSize", True);
	Config.Insert("AsyncEnabled", False);
	Config.Insert("IncludeStackTrace", False);
	Config.Insert("CorrelationEnabled", True);
	Config.Insert("PerformanceTracking", True);
	Config.Insert("OutputTargets", Новый Array);
	Config.OutputTargets.Add("EventLog");
	Config.Insert("CustomFields", Новый Structure);
	Config.Insert("SamplingRate", 1.0);
	Config.Insert("BufferSize", 1000);
	Возврат Config; //↩
КонецФункции
#EndRegion

#Region М1сAIЛогирование_Context
// <doc>
//   <summary>Создать контекст логирования (stateless).</summary>   ✦
//   <param i="1" name="CustomFields" type="Structure" optional="True">Доп. поля.</param>
//   <returns>Structure — CorrelationId, SessionId, UserId, Timestamp и др.</returns>
//   <complexity cc="2"/>
// </doc>
Функция CreateContext(CustomFields = Undefined) Экспорт //⚙
	ib = "Создание контекста логирования"; //✍
	Ctx = Новый Structure; //✏
	Ctx.Insert("CorrelationId", String(Новый UUID));
	Ctx.Insert("SessionId", InfoBaseSessionNumber());
	Ctx.Insert("UserId", ?(UserName() = "", "System", UserName()));
	Ctx.Insert("Timestamp", CurrentDate());
	Ctx.Insert("MachineName", ComputerName());
	Ctx.Insert("ProcessId", String(Новый UUID));
	Ctx.Insert("ThreadId", "Main");
	Ctx.Insert("ApplicationVersion", "1.0.0");
	Ctx.Insert("Environment", "Production");
	Ctx.Insert("CustomFields", Новый Structure);
	Если CustomFields <> Undefined Тогда //⚡
		Для Каждого Pair Из CustomFields Цикл //⟳
			Ctx.CustomFields.Insert(Pair.Key, Pair.Value); //✏
		КонецЦикла;
	КонецЕсли;
	Возврат Ctx; //↩
КонецФункции

// <doc>
//   <summary>Вернуть копию контекста с добавленным полем.</summary>   ✦
//   <returns>Structure — новая копия с полем.</returns>
//   <complexity cc="2"/>
// </doc>
Функция ContextWithField(Context, FieldName, FieldValue) Экспорт //⚙
	ib = "Копия контекста + поле"; //✍
	NewCtx = Новый Structure; //✏
	Для Каждого Pair Из Context Цикл //⟳
		Если Pair.Key = "CustomFields" И TypeOf(Pair.Value) = Type("Structure") Тогда //⚡
			CF = Новый Structure; //✏
			Для Каждого CFPair Из Pair.Value Цикл //⟳
				CF.Insert(CFPair.Key, CFPair.Value); //✏
			КонецЦикла;
			NewCtx.Insert("CustomFields", CF); //✏
		Иначе
			NewCtx.Insert(Pair.Key, Pair.Value); //✏
		КонецЕсли;
	КонецЦикла;
	Если НЕ NewCtx.Contains("CustomFields") Тогда //⚡
		NewCtx.Insert("CustomFields", Новый Structure); //✏
	КонецЕсли;
	NewCtx.CustomFields.Insert(FieldName, FieldValue); //✏
	Возврат NewCtx; //↩
КонецФункции
#EndRegion

#Region М1сAIЛогирование_Performance
// <doc>
//   <summary>Запустить измерение производительности операции.</summary>   ✦
//   <returns>Structure — OperationName, StartTime, CorrelationId.</returns>
//   <complexity cc="1"/>
// </doc>
Функция StartPerformanceTimer(OperationName, Context = Undefined) Экспорт //⚙
	ib = "Старт таймера производительности"; //✍
	Timer = Новый Structure; //✏
	Timer.Insert("OperationName", OperationName);
	Timer.Insert("StartTime", CurrentUniversalDate());
	Timer.Insert("CorrelationId", ?(Context = Undefined, String(Новый UUID), Context.CorrelationId));
	Возврат Timer; //↩
КонецФункции

// <doc>
//   <summary>Завершить измерение и записать событие о производительности.</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="4"/>
// </doc>
Процедура StopPerformanceTimer(Timer, AdditionalData = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Стоп таймера производительности"; //✍
	Если Timer = Undefined Тогда Возврат; КонецЕсли; //⚡
	
	EndTime = CurrentUniversalDate(); //✏
	DurationMs = (EndTime - Timer.StartTime) * 1000; //✏
	
	PerfData = Новый Structure; //✏
	PerfData.Insert("Operation", Timer.OperationName);
	PerfData.Insert("DurationMs", DurationMs);
	PerfData.Insert("StartTime", Timer.StartTime);
	PerfData.Insert("EndTime", EndTime);
	PerfData.Insert("CorrelationId", Timer.CorrelationId);
	
	Если AdditionalData <> Undefined Тогда //⚡
		Если TypeOf(AdditionalData) = Type("Structure") Тогда //⚡
			Для Каждого Pair Из AdditionalData Цикл //⟳
				PerfData.Insert(Pair.Key, Pair.Value); //✏
			КонецЦикла;
		Иначе
			PerfData.Insert("AdditionalData", AdditionalData); //✏
		КонецЕсли;
	КонецЕсли;
	
	Если Config = Undefined Тогда Config = CreateConfig(); КонецЕсли; //⚡
	Если Context = Undefined Тогда Context = CreateContext(); КонецЕсли; //⚡
	
	WriteStructured(EventLogLevel.Information, //▶️
		"Performance {Operation} completed in {DurationMs} ms",
		PerfData, Undefined, Config, Context);
КонецПроцедуры
#EndRegion

#Region М1сAIЛогирование_Invoke
// <doc>
//   <summary>Выполнить вызываемый объект (строка — имя глобальной функции без параметров).</summary>   ✦
//   <returns>Any — результат вызова.</returns>
//   <complexity cc="1"/>
// </doc>
Функция InvokeCallable(Callable) Экспорт //⚙
	ib = "Вызов глобальной функции по имени"; //✍
	Если TypeOf(Callable) <> Type("String") Тогда //⚡
		ВызватьИсключение "InvokeCallable: поддерживается только строка — имя глобальной функции без параметров."; //✏
	КонецЕсли;
	Возврат Вычислить(Callable + "()"); //↩
КонецФункции
#EndRegion

#Region М1сAIЛогирование_Performance // обновлённая MeasureExecution
// <doc>
//   <summary>Измерить выполнение функции по её имени (без параметров), с авто-логированием.</summary>   ✦
//   <returns>Any — результат вызываемой функции.</returns>
//   <complexity cc="5"/>
// </doc>
Функция MeasureExecution(OperationName, Method, Parameters = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Обёртка измерения выполнения"; //✍
	Если Config = Undefined Тогда Config = CreateConfig(); КонецЕсли; //⚡
	Если Context = Undefined Тогда Context = CreateContext(); КонецЕсли; //⚡
	
	Если Parameters <> Undefined Тогда //⚡
		WarnStructured("MeasureExecution: Parameters игнорируются на сервере; используйте обёртку.",
			Новый Structure("Operation", OperationName), Config, Context); //▶️
	КонецЕсли;
	
	T = StartPerformanceTimer(OperationName, Context); //▶️
	Result = Undefined; //✏
	Попытка //✱
		Result = InvokeCallable(Method); //▶️
		StopPerformanceTimer(T, Новый Structure("Success", True), Config, Context); //▶️
	Исключение
		Err = Новый Structure("Success, Error", False, ErrorDescription()); //✏
		StopPerformanceTimer(T, Err, Config, Context); //▶️
		ErrorStructured("Performance error in {Operation}",
			Новый Structure("Operation", OperationName, "Error", ErrorDescription()),
			Undefined, Config, Context); //▶️
		ВызватьИсключение; //✏
	КонецПопытки;
	Возврат Result; //↩
КонецФункции
#EndRegion

#Region М1сAIЛогирование_StructuredLogging
// <doc>
//   <summary>Проверить, нужно ли логировать событие данного уровня.</summary>   ✦
//   <returns>Boolean — Истина, если событие проходит порог MinLevel.</returns>
//   <complexity cc="2"/>
// </doc>
Функция ShouldLog(Level, Config = Undefined) Экспорт //⚙
	ib = "Порог уровня логирования"; //✍
	Если Config = Undefined Тогда Config = CreateConfig(); КонецЕсли; //⚡
	
	LevelOrder = Новый Map; //✏
	LevelOrder.Insert(EventLogLevel.Information, 1);
	LevelOrder.Insert(EventLogLevel.Note, 2);
	LevelOrder.Insert(EventLogLevel.Warning, 3);
	LevelOrder.Insert(EventLogLevel.Error, 4);
	
	CurrentLevelOrder = LevelOrder.Get(Level); //✏
	MinLevelOrder = LevelOrder.Get(Config.MinLevel); //✏
	
	Если CurrentLevelOrder = Undefined ИЛИ MinLevelOrder = Undefined Тогда //⚡
		Возврат True; //↩
	КонецЕсли;
	Возврат CurrentLevelOrder >= MinLevelOrder; //↩
КонецФункции

// <doc>
//   <summary>Подставить значения из Properties в шаблон сообщения.</summary>   ✦
//   <returns>String — сообщение.</returns>
//   <complexity cc="2"/>
// </doc>
Функция FormatMessage(Template, Properties) Экспорт //⚙
	ib = "Форматирование сообщения из шаблона"; //✍
	Если Properties = Undefined Тогда //⚡
		Возврат Template; //↩
	КонецЕсли;
	Res = Template; //✏
	Для Каждого Pair Из Properties Цикл //⟳
		Placeholder = "{" + Pair.Key + "}"; //✏
		Если StrFind(Res, Placeholder) > 0 Тогда //⚡
			Res = StrReplace(Res, Placeholder, String(Pair.Value)); //✏
		КонецЕсли;
	КонецЦикла;
	Возврат Res; //↩
КонецФункции

// <doc>
//   <summary>Получить упрощённую информацию о стеке.</summary>   ✦
//   <returns>Structure — Timestamp, Session, User, Note.</returns>
//   <complexity cc="1"/>
// </doc>
Функция GetStackTrace() Экспорт //⚙
	ib = "Упрощённая информация о стеке"; //✍
	S = Новый Structure; //✏
	S.Insert("Timestamp", CurrentDate());
	S.Insert("Session", InfoBaseSessionNumber());
	S.Insert("User", UserName());
	S.Insert("Note", "Stack trace not available in 1C:Enterprise");
	Возврат S; //↩
КонецФункции

// <doc>
//   <summary>Преобразовать уровень события в строку.</summary>   ✦
//   <returns>String — строковое представление.</returns>
//   <complexity cc="1"/>
// </doc>
Функция LevelToString(Level) Экспорт //⚙
	ib = "Уровень события в строку"; //✍
	Если TypeOf(Level) = Type("EventLogLevel") Тогда //⚡
		Если Level = EventLogLevel.Information Тогда Возврат "Information"; КонецЕсли;
		Если Level = EventLogLevel.Warning Тогда Возврат "Warning"; КонецЕсли;
		Если Level = EventLogLevel.Error Тогда Возврат "Error"; КонецЕсли;
		Если Level = EventLogLevel.Note Тогда Возврат "Note"; КонецЕсли;
	КонецЕсли;
	Возврат String(Level); //↩
КонецФункции

// <doc>
//   <summary>Преобразовать строку/значение в EventLogLevel.</summary>   ✦
//   <returns>EventLogLevel</returns>
//   <complexity cc="1"/>
// </doc>
Функция ParseEventLogLevel(LevelAny) Экспорт //⚙
	ib = "Строка в EventLogLevel"; //✍
	Если TypeOf(LevelAny) = Type("EventLogLevel") Тогда //⚡
		Возврат LevelAny; //↩
	КонецЕсли;
	L = Upper(String(LevelAny)); //✏
	Если L = "INFORMATION" Тогда Возврат EventLogLevel.Information; КонецЕсли;
	Если L = "WARNING" Тогда Возврат EventLogLevel.Warning; КонецЕсли;
	Если L = "ERROR" Тогда Возврат EventLogLevel.Error; КонецЕсли;
	Если L = "NOTE" Тогда Возврат EventLogLevel.Note; КонецЕсли;
	Возврат EventLogLevel.Information; //↩
КонецФункции

// <doc>
//   <summary>Структурированная запись события.</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="4"/>
// </doc>
Процедура WriteStructured(Level, Template, Properties = Undefined, Exception = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Структурированная запись"; //✍
	Если Config = Undefined Тогда Config = CreateConfig(); КонецЕсли; //⚡
	Если НЕ ShouldLog(Level, Config) Тогда Возврат; КонецЕсли; //⚡
	Если Context = Undefined Тогда Context = CreateContext(); КонецЕсли; //⚡
	
	LogEvent = Новый Structure; //✏
	LogEvent.Insert("Timestamp", CurrentUniversalDate());
	LogEvent.Insert("Level", LevelToString(Level));
	LogEvent.Insert("Template", Template);
	LogEvent.Insert("Message", FormatMessage(Template, Properties));
	LogEvent.Insert("Properties", ?(Properties = Undefined, Новый Structure, Properties));
	LogEvent.Insert("Context", Context);
	
	Если Exception <> Undefined Тогда //⚡
		Ex = Новый Structure; //✏
		Ex.Insert("Message", String(Exception));
		Ex.Insert("Type", "1C:Enterprise Error");
		LogEvent.Insert("Exception", Ex);
	КонецЕсли;
	
	Если Config.IncludeStackTrace Тогда //⚡
		LogEvent.Insert("StackTrace", GetStackTrace()); //✏
	КонецЕсли;
	
	OutputToTargets(LogEvent, Config); //▶️
КонецПроцедуры

// <doc>
//   <summary>Вывод события во все настроенные цели.</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="2"/>
// </doc>
Процедура OutputToTargets(LogEvent, Config) Экспорт //⚙
	ib = "Диспатчинг по целям вывода"; //✍
	Для Каждого Target Из Config.OutputTargets Цикл //⟳
		Попытка //✱
			Если Target = "EventLog" Тогда
				OutputToEventLog(LogEvent); //▶️
			ИначеЕсли Target = "Console" Тогда
				OutputToConsole(LogEvent); //▶️
			ИначеЕсли Target = "File" Тогда
				OutputToFile(LogEvent); //▶️
			КонецЕсли;
		Исключение
		КонецПопытки;
	КонецЦикла;
КонецПроцедуры

// <doc>
//   <summary>Вывести событие в системный журнал (WriteLogEvent).</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="2"/>
// </doc>
Процедура OutputToEventLog(LogEvent) Экспорт //⚙
	ib = "Вывод в системный журнал"; //✍
	Попытка //✱
		EventLevel = ParseEventLogLevel(LogEvent.Level); //▶️
		EventName = LogEvent.Template; //✏
		EventComment = М1сAIJSON.ToJSON(LogEvent); //▶️
		WriteLogEvent(EventName, EventLevel, , , EventComment); //▶️
	Исключение
		WriteLogEvent(LogEvent.Message, EventLogLevel.Information); //▶️
	КонецПопытки;
КонецПроцедуры

// <doc>
//   <summary>Вывести событие в консоль (Message).</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="1"/>
// </doc>
Процедура OutputToConsole(LogEvent) Экспорт //⚙
	ib = "Вывод в консоль"; //✍
	ConsoleMessage = String(LogEvent.Timestamp) + " [" + LogEvent.Level + "] " +
		LogEvent.Context.CorrelationId + " " + LogEvent.Message; //✏
	Message(ConsoleMessage); //▶️
КонецПроцедуры

// <doc>
//   <summary>Вывести событие в файл (заглушка).</summary>   ✦
//   <returns>Void</returns>
//   <complexity cc="1"/>
// </doc>
Процедура OutputToFile(LogEvent) Экспорт //⚙
	ib = "Вывод в файл (заглушка)"; //✍
	// Реализовать при наличии прав ФС или модуля работы с файловой системой
КонецПроцедуры
#EndRegion

#Region М1сAIЛогирование_ModernShortcuts
// <doc><summary>Информационное структурированное событие.</summary>   ✦</doc>
Процедура InfoStructured(Template, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Шорткат structured Info"; //✍
	WriteStructured(EventLogLevel.Information, Template, Properties, Undefined, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Предупреждение (structured).</summary>   ✦</doc>
Процедура WarnStructured(Template, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Шорткат structured Warn"; //✍
	WriteStructured(EventLogLevel.Warning, Template, Properties, Undefined, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Ошибка (structured).</summary>   ✦</doc>
Процедура ErrorStructured(Template, Properties = Undefined, Exception = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Шорткат structured Error"; //✍
	WriteStructured(EventLogLevel.Error, Template, Properties, Exception, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Заметка (structured).</summary>   ✦</doc>
Процедура NoteStructured(Template, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Шорткат structured Note"; //✍
	WriteStructured(EventLogLevel.Note, Template, Properties, Undefined, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Начало операции (трейсинг).</summary>   ✦</doc>
Процедура BeginOperation(OperationName, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Начало операции (трейс)"; //✍
	Если Context = Undefined Тогда Context = CreateContext(); КонецЕсли; //⚡
	Data = Новый Structure("Operation", OperationName); //✏
	Если Properties <> Undefined Тогда //⚡
		Для Каждого Pair Из Properties Цикл //⟳
			Data.Insert(Pair.Key, Pair.Value); //✏
		КонецЦикла;
	КонецЕсли;
	InfoStructured("Begin operation: {Operation}", Data, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Завершение операции (трейсинг).</summary>   ✦</doc>
Процедура EndOperation(OperationName, Success = True, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Завершение операции (трейс)"; //✍
	Если Context = Undefined Тогда Context = CreateContext(); КонецЕсли; //⚡
	Data = Новый Structure("Operation, Success", OperationName, Success); //✏
	Если Properties <> Undefined Тогда //⚡
		Для Каждого Pair Из Properties Цикл //⟳
			Data.Insert(Pair.Key, Pair.Value); //✏
		КонецЦикла;
	КонецЕсли;
	Если Success Тогда //⚡
		InfoStructured("End operation: {Operation} - Success", Data, Config, Context); //▶️
	Иначе
		ErrorStructured("End operation: {Operation} - Failed", Data, Undefined, Config, Context); //▶️
	КонецЕсли;
КонецПроцедуры
#EndRegion

#Region М1сAIЛогирование_ModernSelfTest
// <doc>
//   <summary>Прогон self-test для современной части М1сAIЛогирование.</summary>   ✦
//   <returns>Boolean — Истина при успешном завершении.</returns>
//   <complexity cc="4"/>
// </doc>
Функция ModernSelfTest() Экспорт //⚙
	ib = "Самотест structured-части"; //✍
	Попытка //✱
		Cfg = CreateConfig(); //▶️
		Ctx = CreateContext(Новый Structure("RequestId", "REQ-12345")); //▶️
		InfoStructured("User {User} logged in", Новый Structure("User", "john.doe"), Cfg, Ctx); //▶️
		
		BeginOperation("DatabaseQuery", Новый Structure("Table", "Users"), Cfg, Ctx); //▶️
		
		T = StartPerformanceTimer("ComplexCalc", Ctx); //▶️
		Sum = 0; //✏
		Для i = 1 По 10000 Цикл //⟳
			Sum = Sum + i; //✏
		КонецЦикла;
		StopPerformanceTimer(T, Новый Structure("Result", Sum), Cfg, Ctx); //▶️
		
		EndOperation("DatabaseQuery", True, Новый Structure("Rows", 150), Cfg, Ctx); //▶️
		
		Попытка //✱
			ВызватьИсключение "Тестовая ошибка"; //✏
		Исключение
			ErrorStructured("Failed op {Op}",
				Новый Structure("Op", "TestOp", "Error", ErrorDescription()),
				ErrorDescription(), Cfg, Ctx); //▶️
		КонецПопытки;
		
		WarnStructured("Memory usage {V}% exceeds {T}%",
			Новый Structure("V", 85.7, "T", 80.0, "Server", "APP-01"), Cfg, Ctx); //▶️
		NoteStructured("Process {P} completed with {N} items",
			Новый Structure("P", "Sync", "N", 5000, "Duration", "00:15:30"), Cfg, Ctx); //▶️
		
		Возврат True; //↩
	Исключение
		Write("ModernSelfTest failed: " + ErrorDescription(), True, "М1сAIЛогирование.ModernSelfTest", EventLogLevel.Error); //▶️
		Возврат False; //↩
	КонецПопытки;
КонецФункции
#EndRegion

#Region М1сAIЛогирование_RU_Aliases
// <doc><summary>Русский алиас для CreateConfig.</summary>   ✦</doc>
Функция СоздатьКонфиг() Экспорт //⚙
	ib = "Алиас CreateConfig (RU)"; //✍
	Возврат CreateConfig(); //↩
КонецФункции

// <doc><summary>Русский алиас для CreateContext.</summary>   ✦</doc>
Функция СоздатьКонтекст(CustomFields = Undefined) Экспорт //⚙
	ib = "Алиас CreateContext (RU)"; //✍
	Возврат CreateContext(CustomFields); //↩
КонецФункции

// <doc><summary>Русский алиас для ContextWithField.</summary>   ✦</doc>
Функция КонтекстСПолем(Context, FieldName, FieldValue) Экспорт //⚙
	ib = "Алиас ContextWithField (RU)"; //✍
	Возврат ContextWithField(Context, FieldName, FieldValue); //↩
КонецФункции

// <doc><summary>Русский алиас для StartPerformanceTimer.</summary>   ✦</doc>
Функция НачатьИзмерение(OperationName, Context = Undefined) Экспорт //⚙
	ib = "Алиас StartPerformanceTimer (RU)"; //✍
	Возврат StartPerformanceTimer(OperationName, Context); //↩
КонецФункции

// <doc><summary>Русский алиас для StopPerformanceTimer.</summary>   ✦</doc>
Процедура ЗавершитьИзмерение(Timer, AdditionalData = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас StopPerformanceTimer (RU)"; //✍
	StopPerformanceTimer(Timer, AdditionalData, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для InvokeCallable.</summary>   ✦</doc>
Функция ВызватьПоИмени(Callable) Экспорт //⚙
	ib = "Алиас InvokeCallable (RU)"; //✍
	Возврат InvokeCallable(Callable); //↩
КонецФункции

// <doc><summary>Русский алиас для MeasureExecution.</summary>   ✦</doc>
Функция ИзмеритьВыполнение(OperationName, Method, Parameters = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас MeasureExecution (RU)"; //✍
	Возврат MeasureExecution(OperationName, Method, Parameters, Config, Context); //↩
КонецФункции

// <doc><summary>Русский алиас для ShouldLog.</summary>   ✦</doc>
Функция СледуетЛогировать(Level, Config = Undefined) Экспорт //⚙
	ib = "Алиас ShouldLog (RU)"; //✍
	Возврат ShouldLog(Level, Config); //↩
КонецФункции

// <doc><summary>Русский алиас для FormatMessage.</summary>   ✦</doc>
Функция ФорматСообщения(Template, Properties = Undefined) Экспорт //⚙
	ib = "Алиас FormatMessage (RU)"; //✍
	Возврат FormatMessage(Template, Properties); //↩
КонецФункции

// <doc><summary>Русский алиас для GetStackTrace.</summary>   ✦</doc>
Функция ПолучитьСтек() Экспорт //⚙
	ib = "Алиас GetStackTrace (RU)"; //✍
	Возврат GetStackTrace(); //↩
КонецФункции

// <doc><summary>Русский алиас для LevelToString.</summary>   ✦</doc>
Функция УровеньВСтроку(Level) Экспорт //⚙
	ib = "Алиас LevelToString (RU)"; //✍
	Возврат LevelToString(Level); //↩
КонецФункции

// <doc><summary>Русский алиас для ParseEventLogLevel.</summary>   ✦</doc>
Функция СтрокаВУровеньСобытия(LevelAny) Экспорт //⚙
	ib = "Алиас ParseEventLogLevel (RU)"; //✍
	Возврат ParseEventLogLevel(LevelAny); //↩
КонецФункции

// <doc><summary>Русский алиас для WriteStructured.</summary>   ✦</doc>
Процедура ЗаписатьСтруктурировано(Level, Template, Properties = Undefined, Exception = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас WriteStructured (RU)"; //✍
	WriteStructured(Level, Template, Properties, Exception, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для OutputToTargets.</summary>   ✦</doc>
Процедура ВывестиВСцели(LogEvent, Config) Экспорт //⚙
	ib = "Алиас OutputToTargets (RU)"; //✍
	OutputToTargets(LogEvent, Config); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для OutputToEventLog.</summary>   ✦</doc>
Процедура ВывестиВЖурналСобытий(LogEvent) Экспорт //⚙
	ib = "Алиас OutputToEventLog (RU)"; //✍
	OutputToEventLog(LogEvent); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для OutputToConsole.</summary>   ✦</doc>
Процедура ВывестиВКонсоль(LogEvent) Экспорт //⚙
	ib = "Алиас OutputToConsole (RU)"; //✍
	OutputToConsole(LogEvent); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для OutputToFile.</summary>   ✦</doc>
Процедура ВывестиВФайл(LogEvent) Экспорт //⚙
	ib = "Алиас OutputToFile (RU)"; //✍
	OutputToFile(LogEvent); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для InfoStructured.</summary>   ✦</doc>
Процедура ИнфоСтруктурно(Template, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас InfoStructured (RU)"; //✍
	InfoStructured(Template, Properties, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для WarnStructured.</summary>   ✦</doc>
Процедура ПредупреждениеСтруктурно(Template, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас WarnStructured (RU)"; //✍
	WarnStructured(Template, Properties, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для ErrorStructured.</summary>   ✦</doc>
Процедура ОшибкаСтруктурно(Template, Properties = Undefined, Exception = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас ErrorStructured (RU)"; //✍
	ErrorStructured(Template, Properties, Exception, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для NoteStructured.</summary>   ✦</doc>
Процедура ЗаметкаСтруктурно(Template, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас NoteStructured (RU)"; //✍
	NoteStructured(Template, Properties, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для BeginOperation.</summary>   ✦</doc>
Процедура НачалоОперации(OperationName, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас BeginOperation (RU)"; //✍
	BeginOperation(OperationName, Properties, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для EndOperation.</summary>   ✦</doc>
Процедура КонецОперации(OperationName, Success = True, Properties = Undefined, Config = Undefined, Context = Undefined) Экспорт //⚙
	ib = "Алиас EndOperation (RU)"; //✍
	EndOperation(OperationName, Success, Properties, Config, Context); //▶️
КонецПроцедуры

// <doc><summary>Русский алиас для ModernSelfTest.</summary>   ✦</doc>
Функция СовременныйСамоТест() Экспорт //⚙
	ib = "Алиас ModernSelfTest (RU)"; //✍
	Возврат ModernSelfTest(); //↩
КонецФункции
#EndRegion

// ---------------------------- EOF М1сAIЛогирование ---------------------------------