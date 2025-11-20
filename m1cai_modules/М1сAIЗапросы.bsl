// [NEXUS IDENTITY] ID: 879786252461695531 | DATE: 2025-11-19

﻿// Модуль: М1сAIЗапросы
// Назначение: Модуль работы с запросами
//
////////////////////////////////////////////////////////////////////////////////


#Region М1сAIЗапросы_ModuleMap
// Regions:
//   CreateQ           – Создаёт Query с опциональным текстом и TempTablesManager
//   GetParams         – Список параметров запроса
//   GetQParams        – Извлечение параметров из текста запроса
//   ParseParams       – Построение структуры параметров из ключей и значений
//   SetQParams        – Установка параметров в Query
//   BuildQ            – Комбинированное создание и заполнение Query
//   ExecuteQ          – Выполнение запроса и возвращение Выборки
//   IsEmptyResult     – Проверка пустоты результата
//   IsNotEmptyResult  – Обратная проверка
//   Unload            – Выгрузка ТаблицыЗначений
//   UnloadColumn      – Выгрузка массива значений колонки
//   QT                – Быстрая сборка текста запроса
//   BuildByQT         – Сборка Query на основе QT
//   ExecuteByQT       – Выполнение запроса через QT
//   UnloadByQT        – Выгрузка ТЗ через QT
//   EscapeLike        – Экранирование для LIKE
//   QuerySeparator/CombineQT – Вспомогательные функции для составления сложных запросов
//   GetTemps          – TempTablesManager
//   TemporaryTables   – Методы работы с временными таблицами
//   Misc (Region)     – Вспомогательные функции общего назначения
//   SelfTest          – Юнит-тесты модуля
#EndRegion


#Region М1сAIЗапросы_CreateQ
/// <summary>
/// Создаёт объект Query и задаёт текст и менеджер временных таблиц.
/// </summary>
/// <param name="QueryText" type="String" optional="True">Текст запроса.</param>
/// <param name="TempTablesManager" type="TempTablesManager" optional="True">Менеджер временных таблиц.</param>
/// <returns type="Query">Новый объект Query.</returns>
Function CreateQ(QueryText = Undefined, TempTablesManager = Undefined) Export
	
	Query = New Query;
	
	If ValueIsFilled(QueryText) Then
		Query.Text = QueryText;
	EndIf;
	
	If TempTablesManager <> Undefined Then
		Try
			Query.TempTablesManager = TempTablesManager;
		Except EndTry;
	EndIf;
	
	Return Query;
	
EndFunction
#Region examples_М1сAIЗапросы_CreateQ
// Пример:
// q = М1сAIЗапросы.CreateQ("SELECT * FROM Справочник.Номенклатура");
#EndRegion
#EndRegion       

#Region М1сAIЗапросы_NewQ
/// <summary>
/// Создаёт объект Query, устанавливает текст, менеджер временных таблиц и параметры.
/// При включенном AutoTemps создаёт TempTablesManager, если в тексте запроса есть ключевые слова (например, ПОМЕСТИТЬ или INTO).
/// </summary>
/// <param name="QueryText" type="String" optional="True">Текст запроса.</param>
/// <param name="TempTablesManager" type="TempTablesManager" optional="True">Менеджер временных таблиц.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <param name="AutoTemps" type="Boolean" optional="True">Автоматически создавать TempTablesManager, если в запросе есть ПОМЕСТИТЬ/INTO. По умолчанию — Ложь.</param>
/// <returns type="Query">Новый объект Query с установленными параметрами.</returns>
Function NewQ(QueryText = Undefined, TempTablesManager = Undefined, 
	Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, 
	Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined,
	AutoTemps = False) Export
	
	If TempTablesManager = Undefined And AutoTemps And ValueIsFilled(QueryText) Then
		If М1сAIСтроки.HasAny(QueryText, "ПОМЕСТИТЬ,INTO") Then
			TempTablesManager = GetTemps();
		EndIf;
	EndIf;
	
	Query = CreateQ(QueryText, TempTablesManager);
	
	If ValueIsFilled(QueryText) Then
		Parameters = GetQParams(QueryText);
		
		Values = New Array;
		Values.Add(Value1); Values.Add(Value2); Values.Add(Value3); Values.Add(Value4);
		Values.Add(Value5); Values.Add(Value6); Values.Add(Value7); Values.Add(Value8);
		
		ParameterIndex = 0;
		For Each ParameterName In Parameters Do
			If ParameterIndex < Values.Count() And Values[ParameterIndex] <> Undefined Then
				Query.SetParameter(ParameterName.Key, Values[ParameterIndex]);
			EndIf;
			ParameterIndex = ParameterIndex + 1;
		EndDo;
	EndIf;
	
	Return Query;
EndFunction

/// <summary>
/// Упрощённая обёртка для NewQ с автоматическим TempTablesManager (если есть ПОМЕСТИТЬ/INTO).
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <returns type="Query">Объект Query.</returns>
Function Q(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined,
	Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Return NewQ(QueryText, Undefined,
	Value1, Value2, Value3, Value4,
	Value5, Value6, Value7, Value8,
	True); // AutoTemps = True
EndFunction

#Region examples_М1сAIЗапросы_NewQ
// Пример 1: Простое создание
// q = М1сAIЗапросы.NewQ("ВЫБРАТЬ * ИЗ Справочник.Номенклатура");

// Пример 2: С параметром
// q = М1сAIЗапросы.NewQ("ВЫБРАТЬ * ИЗ Справочник.Номенклатура ГДЕ Ссылка = &Ref", , RefValue);

// Пример 3: Авто TempTablesManager по ключевым словам
// q = М1сAIЗапросы.NewQ("ВЫБРАТЬ ... ПОМЕСТИТЬ ВТ_Товары", , , , , , , , , Истина);

// Пример 4: Использование короткой обёртки Q
// q = М1сAIЗапросы.Q("ВЫБРАТЬ ... ПОМЕСТИТЬ ВТ_Результат", Параметр);

// Пример 5: Явное указание TempTablesManager
// tmp = М1сAIЗапросы.GetTemps();
// q = М1сAIЗапросы.NewQ("ВЫБРАТЬ * ИЗ ВТ_Данные ГДЕ Поле = &Value", tmp, "TestValue");

// Пример 6: Несколько параметров
// q = М1сAIЗапросы.NewQ("ВЫБРАТЬ * ИЗ Таблица ГДЕ Поле1 = &P1 И Поле2 = &P2", , Value1, Value2);
#EndRegion
#EndRegion

// Добавить в модуль М1сAIЗапросы

#Region М1сAIЗапросы_ValidateQuery
/// <summary>
/// Быстрая проверка синтаксиса запроса через QueryWizard.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <returns type="Boolean">Истина, если синтаксис корректен.</returns>
Function IsValid(QueryText) Export
	
	Try
		QW = New QueryWizard();
		QW.Text = QueryText;
		Return True;
	Except 
		Return False;
	EndTry;
	
EndFunction

/// <summary>
/// Проверяет запрос с выводом ошибки при необходимости.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="ShowError" type="Boolean" default="True">Показать ошибку.</param>
/// <returns type="Boolean">Истина, если синтаксис корректен.</returns>
Function Validate(QueryText, ShowError = True) Export
	
	QW = New QueryWizard;
	
	Try
		QW.Text = QueryText;
		Return True;
	Except 
		If ShowError Then
			М1сAIСтроки.Print("Query validation error: " + ErrorDescription());
		EndIf;
		Return False;
	EndTry;
	
EndFunction

#Region examples_М1сAIЗапросы_Validate
// Пример использования:
// If М1сAIЗапросы.Validate("ВЫБРАТЬ * ИЗ Справочник.Номенклатура") Then
//     М1сAIСтроки.Print("Запрос корректен");
// Else
//     М1сAIСтроки.Print("Запрос содержит ошибки");
// EndIf;
#EndRegion

#Region М1сAIЗапросы_TempTablesOptimization
/// <summary>
/// Создаёт Query с автоматическим созданием TempTablesManager.
/// </summary>
/// <param name="QueryText" type="String" optional="True">Текст запроса.</param>
/// <param name="CreateTempManager" type="Boolean" default="True">Создать новый менеджер временных таблиц.</param>
/// <returns type="Query">Query с настроенным TempTablesManager.</returns>
Function CreateQWithTemps(QueryText = Undefined, CreateTempManager = True) Export
	
	TempManager = ?(CreateTempManager, New TempTablesManager, Undefined);
	Return CreateQ(QueryText, TempManager);
	
EndFunction

/// <summary>
/// Создаёт Query, использующий существующий TempTablesManager из другого Query.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="SourceQuery" type="Query">Query, у которого берем TempTablesManager.</param>
/// <returns type="Query">Query с переданным TempTablesManager.</returns>
Function CreateAndLoad(QueryText, SourceQuery) Export
	
	If SourceQuery = Undefined Or TypeOf(SourceQuery) <> Type("Query") Then
		Return CreateQ(QueryText);
	EndIf;
	
	Return CreateQ(QueryText, SourceQuery.TempTablesManager);
	
EndFunction

/// <summary>
/// Улучшенная версия CreateQ с дополнительными проверками TempTablesManager.
/// </summary>
/// <param name="QueryText" type="String" optional="True">Текст запроса.</param>
/// <param name="TempTablesManager" type="TempTablesManager" optional="True">Менеджер временных таблиц.</param>
/// <param name="AutoCreateTemps" type="Boolean" default="False">Автоматически создать менеджер, если не передан.</param>
/// <returns type="Query">Новый объект Query.</returns>
Function CreateQEnhanced(QueryText = Undefined, TempTablesManager = Undefined, AutoCreateTemps = False) Export
	
	Query = New Query;
	
	If ValueIsFilled(QueryText) Then
		Query.Text = QueryText;
	EndIf;
	
	// Обработка TempTablesManager
	If TempTablesManager <> Undefined Then
		Try
			Query.TempTablesManager = TempTablesManager;
		Except 
			М1сAIСтроки.Print("CreateQEnhanced: Ошибка установки TempTablesManager: " + ErrorDescription());
		EndTry;
	ElsIf AutoCreateTemps Then
		// Автоматическое создание менеджера временных таблиц
		Try
			Query.TempTablesManager = New TempTablesManager;
		Except
			М1сAIСтроки.Print("CreateQEnhanced: Не удалось создать TempTablesManager: " + ErrorDescription());
		EndTry;
	EndIf;
	
	Return Query;
	
EndFunction

#Region examples_М1сAIЗапросы_TempTablesOptimization
// Пример 1: Автоматическое создание TempTablesManager
// q1 = М1сAIЗапросы.CreateQWithTemps("SELECT 1 AS Field INTO TempTable");

// Пример 2: Разделение TempTablesManager между запросами
// q1 = М1сAIЗапросы.CreateQWithTemps("SELECT 1 AS ID INTO TempTable");
// q2 = М1сAIЗапросы.CreateAndLoad("SELECT * FROM TempTable", q1);

// Пример 3: Улучшенное создание с автоматическим менеджером
// q = М1сAIЗапросы.CreateQEnhanced("SELECT * FROM TempTable", , True);
#EndRegion
#EndRegion
#EndRegion

#Region М1сAIЗапросы_CreateQSafe
/// <summary>
/// Создаёт Query с предварительной проверкой синтаксиса запроса.
/// </summary>
/// <param name="QueryText" type="String" optional="True">Текст запроса.</param>
/// <param name="TempTablesManager" type="TempTablesManager" optional="True">Менеджер временных таблиц.</param>
/// <param name="ValidateFirst" type="Boolean" default="True">Проверять синтаксис перед созданием.</param>
/// <returns type="Query">Новый Query или Undefined при ошибке валидации.</returns>
Function CreateQSafe(QueryText = Undefined, TempTablesManager = Undefined, ValidateFirst = True) Export
	
	// Если задан текст запроса и включена валидация
	If ValueIsFilled(QueryText) And ValidateFirst Then
		If Not Validate(QueryText, True) Then
			Return Undefined; // Возвращаем Undefined при некорректном запросе
		EndIf;
	EndIf;
	
	// Создаем обычный Query если валидация прошла успешно
	Return CreateQ(QueryText, TempTablesManager);
	
EndFunction
#EndRegion

#Region М1сAIЗапросы_GetParams

/// <summary>
/// Возвращает массив параметров у Query.
/// </summary>
/// <param name="Query" type="Query">Запрос для анализа.</param>
/// <param name="PrintParams" type="Boolean" default="False">Показать параметры через М1сAIСтроки.Print.</param>
/// <returns type="Array">Массив объектов Parameter.</returns>
Function GetParams(Query, PrintParams = False) Export
	Try    
		// IF Query.Text IS EMPTY ERROR:
		// {(1, 1)}: Ожидается выражение "ВЫБРАТЬ"
		Params = Query.FindParameters();   
		If PrintParams Then 
			ParamNum = 1;
			For Each qp In Params Do
				М1сAIСтроки.Print("Param #=" + ParamNum);
				М1сAIСтроки.Print("Name=" + qp.Имя + " Type=" + qp.ТипЗначения);
				ParamNum = ParamNum + 1;
			EndDo;
			
		EndIf;
		Return Params;
	Except 
		Params = Undefined;
		Return Params;
	EndTry;
EndFunction	
#Region examples_М1сAIЗапросы_GetParams
// Пример:
// q = М1сAIЗапросы.CreateQ("SELECT * FROM Таблица WHERE Поле = &Val");
// q = М1сAIЗапросы.NewQ("SELECT * FROM Таблица WHERE Поле = &Val");
// params = М1сAIЗапросы.GetParams(q, True);
#EndRegion
#EndRegion

#Region М1сAIЗапросы_GetQParams
/// <summary>
/// Извлекает имена параметров из текста запроса (&Param).
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <returns type="Structure">Структура ключ->Undefined по найденным именам.</returns>
Function GetQParams(QueryText) Export //⚙
	// Create a new structure to hold the parameters
	Parameters = New Structure;
	
	// Find all parameters in the format &parameter
	Position = 1;
	While Position <= StrLen(QueryText) Do //⟳
		// Find the position of the next parameter
		Position = StrFind(QueryText, "&", , Position);
		If Position = 0 Then //⚡
			Break; //✖
		EndIf;
		
		// Initialize the end position for extracting the parameter name
		EndPosition = Position + 1;
		IsAlphaNumChar = True;
		
		// Loop to find the end of the parameter name
		While EndPosition <= StrLen(QueryText) And IsAlphaNumChar Do //⟳
			Char = М1сAIСимволы.GetChar(QueryText, EndPosition); //▶️ Get the current character
			IsAlphaNumChar = М1сAIСимволы.IsAlphaNum(Char); //▶️ Check if the character is alphanumeric or underscore
			If IsAlphaNumChar Then //⚡
				EndPosition = EndPosition + 1; // Move to the next character
			EndIf;
		EndDo;
		
		// Extract the parameter name
		StartPos = Position + 1; // Start position for the parameter name
		Length = EndPosition - Position - 1; // Length of the parameter name
		ParameterName = Mid(QueryText, StartPos, Length); // Extract the parameter name
		
		// Insert the parameter name into the structure
		Parameters.Insert(ParameterName, Undefined);
		
		// Move to the next position
		Position = EndPosition;
	EndDo;
	
	// Return the structure with parameters
	Return Parameters; //↩
EndFunction

#Region examples_М1сAIЗапросы_GetQParams
// Пример:
// txt = "SELECT * FROM Т WHERE x=&X AND y=&Y";
// st = М1сAIЗапросы.GetQParams(txt);
// // st содержит {X:Undefined, Y:Undefined}
#EndRegion
#EndRegion

#Region М1сAIЗапросы_ParseParams

/// <summary>
/// Формирует структуру параметров по списку ключей и до 8 значений.
/// </summary>
/// <param name="KeyString" type="String">Запятая-разделённый список ключей.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Значения параметров.</param>
/// <returns type="Structure">Структура ключ->значение.</returns>
Function ParseParams(KeyString, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	// Split the key string into an array of keys
	Keys = StrSplit(KeyString, ",");
	
	// Create an array of values
	Values = New Array;
	Values.Add(Value1);
	Values.Add(Value2);
	Values.Add(Value3);
	Values.Add(Value4);
	Values.Add(Value5);
	Values.Add(Value6);
	Values.Add(Value7);
	Values.Add(Value8);
	
	// Create a structure to hold the parameters
	Parameters = New Structure;
	
	// Populate the structure with keys and values
	For i = 0 To Keys.Count() - 1 Do
		If Values[i] <> Undefined Then
			Parameters.Insert(Keys[i], Values[i]);
		EndIf;
	EndDo;
	
	// Return the structure with parameters
	Return Parameters;
EndFunction
#Region examples_М1сAIЗапросы_ParseParams
// Пример:
// st = М1сAIЗапросы.ParseParams("X,Y","a","b");
// // st={X:"a", Y:"b"}
#EndRegion
#EndRegion

#Region М1сAIЗапросы_SetQParams


/// <summary>
/// Устанавливает в Query параметры из структуры.
/// </summary>
/// <param name="Query" type="Query">Запрос.</param>
/// <param name="Parameters" type="Structure">Ключ->значение.</param>
/// <returns type="Query">Тот же Query.</returns>
Function SetQParams(Query, Parameters = Undefined) Export

	// Parameters = Key & Value Structure
	If Parameters <> Undefined Then
		
		// Set the parameters in the query
		For Each Parameter In Parameters Do
			Query.SetParameter(Parameter.Key, Parameter.Value);
		EndDo;
		
	EndIf;
	
	// Return the constructed query
	Return Query;
	
EndFunction

#Region examples_М1сAIЗапросы_SetQParams
// Пример:
// q = М1сAIЗапросы.CreateQ(txt);
// q2 = М1сAIЗапросы.SetQParams(q, Новый Структура("X,Y",1,2));
#EndRegion
#EndRegion

#Region М1сAIЗапросы_BuildQByParams
/// <summary>
/// Создаёт Query, анализирует параметры и присваивает им значения.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Query">Готовый Query.</returns>
Function BuildQByParams(QueryText, KeyString, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	// Create a new query
	Query = New Query;
	Query.Text = QueryText;

	// Get the parameters using ParseParams function
	Parameters = ParseParams(KeyString, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
	
	//// Set the parameters in the query
	//For Each Parameter In Parameters Do
	//	Query.SetParameter(Parameter.Key, Parameter.Value);
	//EndDo;
	
	Query = SetQParams(Query, Parameters);
	
	// Return the constructed query
	Return Query;
EndFunction

#Region examples_М1сAIЗапросы_BuildQ
// @example.1.М1сAIЗапросы.BuildQ {
// q = М1сAIЗапросы.BuildQ("SELECT * FROM T WHERE f=&F",123);
// }
// @example.2.М1сAIЗапросы.BuildQ {
// q = М1сAIЗапросы.BuildQ("SELECT * FROM T WHERE a=&A AND b=&B",1,2);
// }
#EndRegion
#EndRegion

#Region М1сAIЗапросы_BuildQ
/// <summary>
/// Выполняет запрос и возвращает выборку.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Selection">Результат выполнения Query.</returns>
Function BuildQ(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	// Извлечение параметров из текста запроса
	//Parameters = М1сAIЗапросы.ExtractParameters(QueryText);
	Parameters = М1сAIЗапросы.GetQParams(QueryText);
	
	// Создание нового запроса
	Query = New Query;
	Query.Text = QueryText;
	
	// Создание массива значений
	Values = New Array;
	Values.Add(Value1);
	Values.Add(Value2);
	Values.Add(Value3);
	Values.Add(Value4);
	Values.Add(Value5);
	Values.Add(Value6);
	Values.Add(Value7);
	Values.Add(Value8);
	
	// Задание параметров в запросе
	i = 0;
	For Each ParameterName In Parameters Do
		If i < Values.Count() Then
			Query.SetParameter(ParameterName.Ключ, Values[i]);            i = i + 1;
		EndIf;
	EndDo;
	
	// Возврат сконструированного запроса
	Return Query;
EndFunction

#Region examples_М1сAIЗапросы_BuildQ

#Region example_1_М1сAIЗапросы_BuildQ

// @example.1.М1сAIЗапросы.BuildQ {

//// Текст запроса
//QueryText = 
//"ВЫБРАТЬ
//|	АктивностьСеансовПользователей.ИдентификаторЗаданияДляОстановки КАК ИдентификаторЗаданияДляОстановки,
//|	АктивностьСеансовПользователей.ДатаПоследнейАктивностиУниверсальная КАК ДатаПоследнейАктивностиУниверсальная
//|ИЗ
//|	РегистрСведений.АктивностьСеансовПользователей КАК АктивностьСеансовПользователей
//|ГДЕ
//|	АктивностьСеансовПользователей.Организация = &Организация
//|	И АктивностьСеансовПользователей.Пользователь = &Пользователь";

//// Создание запроса с параметрами
//Query = BuildQ(QueryText, Источник.Организация, ТекущийПользователь);

//// Выполнение запроса
//Выборка = Query.Выполнить().Выбрать();

// @example.1.М1сAIЗапросы.BuildQ }

#EndRegion

#Region example_2_М1сAIЗапросы_BuildQ

// @example.2.М1сAIЗапросы.BuildQ {

//// Пример 2
//QueryText = 
//"ВЫБРАТЬ
//|	ДругаяТаблица.Параметр1 КАК Параметр1,
//|	ДругаяТаблица.Параметр2 КАК Параметр2
//|ИЗ
//|	РегистрСведений.ДругаяТаблица КАК ДругаяТаблица
//|ГДЕ
//|	ДругаяТаблица.Параметр1 = &Параметр1";

//// Создание запроса с параметрами
//Query = BuildQ(QueryText, ЗначениеПараметра1);

//// Выполнение запроса
//Выборка = Query.Выполнить().Выбрать();

// @example.2.М1сAIЗапросы.BuildQ }
#EndRegion

#EndRegion

#EndRegion

#Region М1сAIЗапросы_ExecuteQ
/// <summary>
/// Выполняет запрос и возвращает выборку.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Selection">Результат выполнения Query.</returns>
Function ExecuteQ(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	// Создание запроса с параметрами
	Query = BuildQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
	
	// Выполнение запроса
	Return Query.Выполнить().Выбрать();
EndFunction

#Region examples_М1сAIЗапросы_ExecuteQ

#Region example_1_М1сAIЗапросы_ExecuteQ

// @example.1.М1сAIЗапросы.ExecuteQ {

//// Текст запроса
//QueryText = 
//"ВЫБРАТЬ
//|	АктивностьСеансовПользователей.ИдентификаторЗаданияДляОстановки КАК ИдентификаторЗаданияДляОстановки,
//|	АктивностьСеансовПользователей.ДатаПоследнейАктивностиУниверсальная КАК ДатаПоследнейАктивностиУниверсальная
//|ИЗ
//|	РегистрСведений.АктивностьСеансовПользователей КАК АктивностьСеансовПользователей
//|ГДЕ
//|	АктивностьСеансовПользователей.Организация = &Организация
//|	И АктивностьСеансовПользователей.Пользователь = &Пользователь";

//// Выполнение запроса с параметрами
//Выборка = ExecuteQ(QueryText, Источник.Организация, ТекущийПользователь);

// @example.1.М1сAIЗапросы.ExecuteQ }

#EndRegion

#Region example_2_М1сAIЗапросы_ExecuteQ

// @example.2.М1сAIЗапросы.ExecuteQ {

//// Пример 2
//QueryText = 
//"ВЫБРАТЬ
//|	ДругаяТаблица.Параметр1 КАК Параметр1,
//|	ДругаяТаблица.Параметр2 КАК Параметр2
//|ИЗ
//|	РегистрСведений.ДругаяТаблица КАК ДругаяТаблица
//|ГДЕ
//|	ДругаяТаблица.Параметр1 = &Параметр1";

//// Выполнение запроса с параметрами
//Выборка = ExecuteQ(QueryText, ЗначениеПараметра1);

// @example.2.М1сAIЗапросы.ExecuteQ }

#EndRegion

#EndRegion

#EndRegion

#Region М1сAIСтроки_FirstRow
/// <summary>
/// Возвращает первую строку из выборки запроса.
/// </summary>
/// <param name="Selection" type="Selection">Объект ВыборкаИзРезультатаЗапроса.</param>
/// <returns type="Variant">Первая строка или Undefined, если выборка пуста.</returns>
Function FirstRow(Selection) Export //⚙
	If Selection.Следующий() Then
		Return Selection; //↩
	EndIf;
	Return Undefined; //↩
EndFunction

#Region examples_М1сAIСтроки_FirstRow
// Пример:
// s = М1сAIЗапросы.ExecuteQ("ВЫБРАТЬ 1 КАК Число"); //▶️
// r = М1сAIСтроки.FirstRow(s); //▶️
// If r <> Undefined Then //⚡
//     М1сAIСтроки.Print("Первое значение: " + r.Число); //▶️
// EndIf;
#EndRegion

#EndRegion

#Region М1сAIЗапросы_FirstRowQ
/// <summary>
/// Выполняет запрос и возвращает первую строку выборки или Undefined.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Selection">Первая строка выборки или Undefined.</returns>
Function FirstRowQ(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		Selection = ExecuteQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		If Selection.Следующий() Then
			Return Selection;
		EndIf;
	Except
		М1сAIСтроки.Print("FirstRowQ error: " + ErrorDescription());
	EndTry;
	
	Return Undefined;
	
EndFunction

#Region examples_М1сAIЗапросы_FirstRowQ
// Пример:
// row = М1сAIЗапросы.FirstRowQ("ВЫБРАТЬ ПЕРВЫЕ 1 Ссылка ИЗ Справочник.Пользователи ГДЕ ИдентификаторПользователяИБ = &UID", UserUID);
// Пользователь = ?(row = Undefined, Справочники.Пользователи.ПустаяСсылка(), row.Ссылка);
#EndRegion
#EndRegion


#Region М1сAIЗапросы_ValueQ
/// <summary>
/// Выполняет запрос и возвращает единственное значение из первой строки и первого столбца.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="DefaultValue" type="Variant" optional="True">Значение по умолчанию.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Variant">Значение из первой ячейки или DefaultValue.</returns>
Function ValueQ(QueryText, DefaultValue = Undefined, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		If VT.Количество() > 0 And VT.Колонки.Количество() > 0 Then
			Return VT[0][0];
		EndIf;
	Except
		М1сAIСтроки.Print("ValueQ error: " + ErrorDescription());
	EndTry;
	
	Return DefaultValue;
	
EndFunction

#Region examples_М1сAIЗапросы_ValueQ
// Пример:
// Count = М1сAIЗапросы.ValueQ("ВЫБРАТЬ КОЛИЧЕСТВО(*) ИЗ Справочник.Номенклатура", 0);
// MaxDate = М1сAIЗапросы.ValueQ("ВЫБРАТЬ МАКСИМУМ(Дата) ИЗ Документ.Продажа", '00010101');
#EndRegion
#EndRegion

#Region М1сAIЗапросы_GetTableStructure
// Функция возвращает структуру колонок таблицы или запроса (без данных)
// Параметр TableName - имя таблицы или запроса
// Параметр TTManager - МВТ
// Возвращает ТаблицаЗначений с колонками (без строк)

Функция GetTableStructure(TableName, TTManager = Неопределено) Экспорт
	Запрос = Новый Запрос;
	Если TTManager = Неопределено Тогда
		Запрос.Текст = "ВЫБРАТЬ ПЕРВЫЕ 0 * ИЗ " + TableName + " КАК T";
	Иначе
		Запрос.МенеджерВременныхТаблиц = TTManager;
		Запрос.Текст = "ВЫБРАТЬ ПЕРВЫЕ 0 * ИЗ " + TableName + " КАК T";
	КонецЕсли;
	
	Попытка
		Возврат Запрос.Выполнить().Выгрузить();
	Исключение
		Возврат Новый ТаблицаЗначений;
	КонецПопытки;
КонецФункции
#EndRegion

/// <summary>
/// Возвращает СписокЗначений из результата запроса.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="ValueField" type="String" default="Ссылка">Имя поля значения.</param>
/// <param name="PresentationField" type="String" default="">Имя поля представления (необязательно).</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <returns type="ValueList">СписокЗначений.</returns>
Function ValuesQ(QueryText, ValueField = "Ссылка", PresentationField = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Result = New ValueList;
		
		// Проверяем наличие полей
		HasValueField = (VT.Columns.Find(ValueField) <> Undefined);
		HasPresentationField = ValueIsFilled(PresentationField) And (VT.Columns.Find(PresentationField) <> Undefined);
		
		// Если нет указанного поля значения, берем первое
		If Not HasValueField And VT.Columns.Count() > 0 Then
			ValueField = VT.Columns[0].Name;
			HasValueField = True;
		EndIf;
		
		For Each Row In VT Do
			If HasValueField Then
				Value = Row[ValueField];
				Presentation = ?(HasPresentationField, Row[PresentationField], String(Value));
				Result.Add(Value, Presentation);
			EndIf;
		EndDo;
		
		Return Result;
		
	Except
		М1сAIСтроки.Print("ValuesQ error: " + ErrorDescription());
		Return New ValueList;
	EndTry;
	
EndFunction        

/// Возвращает Массив значений из указанного поля результата запроса.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="ColumnName" type="String" default="">Имя колонки (если пусто - первая колонка).</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <returns type="Array">Массив значений.</returns>
Function ArrayQ(QueryText, ColumnName = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		
		// Определяем имя колонки
		If Not ValueIsFilled(ColumnName) And VT.Columns.Count() > 0 Then
			ColumnName = VT.Columns[0].Name;
		EndIf;
		
		// Проверяем существование колонки
		If VT.Columns.Find(ColumnName) = Undefined Then
			М1сAIСтроки.Print("ArrayQ: Column '" + ColumnName + "' not found");
			Return New Array;
		EndIf;
		
		Return VT.UnloadColumn(ColumnName);
		
	Except
		М1сAIСтроки.Print("ArrayQ error: " + ErrorDescription());
		Return New Array;
	EndTry;
	
EndFunction

/// Возвращает Структуру из двух колонок результата запроса (ключ -> значение).
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="KeyField" type="String" default="">Имя поля ключа (если пусто - первая колонка).</param>
/// <param name="ValueField" type="String" default="">Имя поля значения (если пусто - вторая колонка).</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <returns type="Structure">Структура ключ -> значение.</returns>
Function StructureQ(QueryText, KeyField = "", ValueField = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Result = New Structure;
		
		// Определяем имена полей
		If Not ValueIsFilled(KeyField) And VT.Columns.Count() > 0 Then
			KeyField = VT.Columns[0].Name;
		EndIf;
		If Not ValueIsFilled(ValueField) And VT.Columns.Count() > 1 Then
			ValueField = VT.Columns[1].Name;
		EndIf;
		
		// Проверяем существование полей
		If VT.Columns.Find(KeyField) = Undefined Then
			М1сAIСтроки.Print("StructureQ: Key field '" + KeyField + "' not found");
			Return Result;
		EndIf;
		If VT.Columns.Find(ValueField) = Undefined Then
			М1сAIСтроки.Print("StructureQ: Value field '" + ValueField + "' not found");
			Return Result;
		EndIf;
		
		// Заполняем структуру
		For Each Row In VT Do
			Key = String(Row[KeyField]);
			Value = Row[ValueField];
			
			// Избегаем дублей ключей
			If Not Result.Property(Key) Then
				Result.Insert(Key, Value);
			EndIf;
		EndDo;
		
		Return Result;
		
	Except
		М1сAIСтроки.Print("StructureQ error: " + ErrorDescription());
		Return New Structure;
	EndTry;
	
EndFunction

/// Возвращает Соответствие из двух колонок результата запроса.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="KeyField" type="String" default="">Имя поля ключа.</param>
/// <param name="ValueField" type="String" default="">Имя поля значения.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <returns type="Map">Соответствие ключ -> значение.</returns>
Function MapQ(QueryText, KeyField = "", ValueField = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Result = New Map;
		
		// Определяем имена полей
		If Not ValueIsFilled(KeyField) And VT.Columns.Count() > 0 Then
			KeyField = VT.Columns[0].Name;
		EndIf;
		If Not ValueIsFilled(ValueField) And VT.Columns.Count() > 1 Then
			ValueField = VT.Columns[1].Name;
		EndIf;
		
		// Проверяем существование полей
		If VT.Columns.Find(KeyField) = Undefined Then
			М1сAIСтроки.Print("MapQ: Key field '" + KeyField + "' not found");
			Return Result;
		EndIf;
		If VT.Columns.Find(ValueField) = Undefined Then
			М1сAIСтроки.Print("MapQ: Value field '" + ValueField + "' not found");
			Return Result;
		EndIf;
		
		// Заполняем соответствие
		For Each Row In VT Do
			Key = Row[KeyField];
			Value = Row[ValueField];
			Result.Insert(Key, Value);
		EndDo;
		
		Return Result;
		
	Except
		М1сAIСтроки.Print("MapQ error: " + ErrorDescription());
		Return New Map;
	EndTry;
	
EndFunction

/// Возвращает ТаблицуЗначений, сгруппированную по указанному полю.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="GroupField" type="String">Поле для группировки.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры запроса.</param>
/// <returns type="Structure">Структура: ЗначениеГруппы -> ТаблицаЗначений.</returns>
Function GroupedQ(QueryText, GroupField, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Result = New Structure;
		
		// Проверяем существование поля группировки
		If VT.Columns.Find(GroupField) = Undefined Then
			М1сAIСтроки.Print("GroupedQ: Group field '" + GroupField + "' not found");
			Return Result;
		EndIf;
		
		// Группируем данные
		For Each Row In VT Do
			GroupValue = String(Row[GroupField]);
			
			If Not Result.Property(GroupValue) Then
				// Создаем новую таблицу для группы
				GroupTable = VT.Copy(New Array); // Копируем структуру без данных
				Result.Insert(GroupValue, GroupTable);
			EndIf;
			
			// Добавляем строку в группу
			NewRow = Result[GroupValue].Add();
			FillPropertyValues(NewRow, Row);
		EndDo;
		
		Return Result;
		
	Except
		М1сAIСтроки.Print("GroupedQ error: " + ErrorDescription());
		Return New Structure;
	EndTry;
	
EndFunction

// LIKE HANDLING

#Region М1сAIЗапросы_AutoEscaping
/// <summary>
/// Автоматически определяет необходимость экранирования параметров в запросе.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Parameters" type="Structure">Структура параметров.</param>
/// <param name="AutoEscape" type="Boolean" default="True">Автоматическое экранирование для LIKE/ПОДОБНО.</param>
/// <returns type="Structure">Обработанные параметры.</returns>
Function ProcessQueryParams(QueryText, Parameters, AutoEscape = True) Export
	
	If Not AutoEscape Or Parameters = Undefined Then
		Return Parameters;
	EndIf;
	
	ProcessedParams = New Structure;
	QueryTextUpper = Upper(QueryText);
	
	For Each Param In Parameters Do
		ParamValue = Param.Value;
		ParamName = Param.Key;
		
		// Проверяем, используется ли параметр с LIKE или ПОДОБНО
		If TypeOf(ParamValue) = Type("String") Then
			ParamPattern = "&" + ParamName;
			ParamPosition = StrFind(QueryTextUpper, Upper(ParamPattern));
			
			If ParamPosition > 0 Then
				// Ищем LIKE/ПОДОБНО в контексте параметра (в пределах 50 символов)
				ContextStart = Max(1, ParamPosition - 30);
				ContextEnd = Min(StrLen(QueryText), ParamPosition + 30);
				Context = Upper(Mid(QueryText, ContextStart, ContextEnd - ContextStart + 1));
				
				If StrFind(Context, "ПОДОБНО") > 0 Or StrFind(Context, "LIKE") > 0 Then
					// Экранируем значение для поиска
					ProcessedParams.Insert(ParamName, EscapeLike(ParamValue));
				Else
					ProcessedParams.Insert(ParamName, ParamValue);
				EndIf;
			Else
				ProcessedParams.Insert(ParamName, ParamValue);
			EndIf;
		Else
			ProcessedParams.Insert(ParamName, ParamValue);
		EndIf;
	EndDo;
	
	Return ProcessedParams;
	
EndFunction

/// <summary>
/// Безопасное выполнение запроса с автоэкранированием.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Parameters" type="Structure" optional="True">Параметры запроса.</param>
/// <param name="AutoEscape" type="Boolean" default="True">Автоматическое экранирование.</param>
/// <returns type="Selection">Результат выполнения запроса.</returns>
Function ExecuteQSafe(QueryText, Parameters = Undefined, AutoEscape = True) Export
	
	Try
		Query = CreateQ(QueryText);
		
		If Parameters <> Undefined Then
			ProcessedParams = ProcessQueryParams(QueryText, Parameters, AutoEscape);
			SetQParams(Query, ProcessedParams);
		EndIf;
		
		Return Query.Execute().Select();
		
	Except
		М1сAIСтроки.Print("ExecuteQSafe error: " + ErrorDescription());
		Return Undefined;
	EndTry;
	
EndFunction

/// <summary>
/// Безопасная выгрузка с автоэкранированием.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Parameters" type="Structure" optional="True">Параметры запроса.</param>
/// <param name="AutoEscape" type="Boolean" default="True">Автоматическое экранирование.</param>
/// <returns type="ValueTable">Результат выполнения запроса.</returns>
Function UnloadSafe(QueryText, Parameters = Undefined, AutoEscape = True) Export
	
	Try
		Selection = ExecuteQSafe(QueryText, Parameters, AutoEscape);
		If Selection <> Undefined Then
			Return Selection.Unload();
		EndIf;
	Except
		М1сAIСтроки.Print("UnloadSafe error: " + ErrorDescription());
	EndTry;
	
	Return New ValueTable;
	
EndFunction
#EndRegion

#Region М1сAIЗапросы_SearchQueries

/// <summary>
/// Универсальная функция поиска с автоматическим построением условий.
/// </summary>
/// <param name="TableName" type="String">Имя таблицы для поиска.</param>
/// <param name="SearchFields" type="String">Поля для поиска (через запятую).</param>
/// <param name="SearchString" type="String">Строка поиска.</param>
/// <param name="SearchMode" type="String" default="Contains">Режим поиска: "Contains", "StartsWith", "EndsWith", "Exact".</param>
/// <param name="TopCount" type="Number" default="20">Количество записей.</param>
/// <param name="AdditionalConditions" type="String" optional="True">Дополнительные условия WHERE.</param>
/// <param name="OrderBy" type="String" optional="True">Поля сортировки.</param>
/// <returns type="Structure">Структура с полями: QueryText, Parameters.</returns>
Function BuildSearchQuery(TableName, SearchFields, SearchString, SearchMode = "Contains", TopCount = 20, AdditionalConditions = "", OrderBy = "") Export
	
	Result = New Structure;
	Result.Insert("QueryText", "");
	Result.Insert("Parameters", New Structure);
	
	// Формируем базовый запрос
	QueryText = "ВЫБРАТЬ ПЕРВЫЕ " + TopCount + " * ИЗ " + TableName + " ГДЕ ";
	
	// Добавляем дополнительные условия
	If ValueIsFilled(AdditionalConditions) Then
		QueryText = QueryText + "(" + AdditionalConditions + ") И ";
	EndIf;
	
	// Если строка поиска пуста, возвращаем все записи
	If Not ValueIsFilled(SearchString) Then
		QueryText = QueryText + "TRUE";
	Else
		// Формируем условия поиска
		SearchConditions = New Array;
		Fields = StrSplit(SearchFields, ",");
		
		For Each Field In Fields Do
			FieldName = TrimAll(Field);
			
			SearchPattern = "";
			If SearchMode = "StartsWith" Then
				SearchPattern = EscapeLike(SearchString) + "%";
			ElsIf SearchMode = "EndsWith" Then
				SearchPattern = "%" + EscapeLike(SearchString);
			ElsIf SearchMode = "Contains" Then
				SearchPattern = "%" + EscapeLike(SearchString) + "%";
			ElsIf SearchMode = "Exact" Then
				SearchPattern = SearchString;
			EndIf;
			
			If SearchMode = "Exact" Then
				SearchConditions.Add(FieldName + " = &SearchString");
			Else
				SearchConditions.Add(FieldName + " ПОДОБНО &SearchPattern СПЕЦСИМВОЛ ""~""");
			EndIf;
		EndDo;
		
		QueryText = QueryText + "(" + StrConcat(SearchConditions, " ИЛИ ") + ")";
		
		// Добавляем параметры
		If SearchMode = "Exact" Then
			Result.Parameters.Insert("SearchString", SearchString);
		Else
			Result.Parameters.Insert("SearchPattern", SearchPattern);
		EndIf;
	EndIf;
	
	// Добавляем сортировку
	If ValueIsFilled(OrderBy) Then
		QueryText = QueryText + " УПОРЯДОЧИТЬ ПО " + OrderBy;
	EndIf;
	
	Result.QueryText = QueryText;
	Return Result;
	
EndFunction

/// <summary>
/// Выполняет поиск и возвращает ValueList для выбора.
/// </summary>
/// <param name="TableName" type="String">Имя таблицы.</param>
/// <param name="SearchFields" type="String">Поля поиска.</param>
/// <param name="ValueField" type="String">Поле значения (обычно "Ссылка").</param>
/// <param name="PresentationField" type="String">Поле представления.</param>
/// <param name="SearchString" type="String">Строка поиска.</param>
/// <param name="SearchMode" type="String" default="Contains">Режим поиска.</param>
/// <param name="TopCount" type="Number" default="20">Количество записей.</param>
/// <param name="AdditionalConditions" type="String" optional="True">Дополнительные условия.</param>
/// <returns type="ValueList">Список значений для выбора.</returns>
Function SearchForChoice(TableName, SearchFields, ValueField, PresentationField, SearchString, SearchMode = "Contains", TopCount = 20, AdditionalConditions = "") Export
	
	Try
		SearchQuery = BuildSearchQuery(TableName, SearchFields, SearchString, SearchMode, TopCount, AdditionalConditions);
		
		VT = UnloadSafe(SearchQuery.QueryText, SearchQuery.Parameters);
		Result = New ValueList;
		
		For Each Row In VT Do
			Value = Row[ValueField];
			Presentation = Row[PresentationField];
			Result.Add(Value, Presentation);
		EndDo;
		
		Return Result;
		
	Except
		М1сAIСтроки.Print("SearchForChoice error: " + ErrorDescription());
		Return New ValueList;
	EndTry;
	
EndFunction

/// <summary>
/// Автоматизированная функция для ОбработкаПолученияДанныхВыбора.
/// </summary>
/// <param name="TableName" type="String">Имя таблицы.</param>
/// <param name="SearchFields" type="String">Поля поиска.</param>
/// <param name="ValueField" type="String" default="Ссылка">Поле значения.</param>
/// <param name="PresentationFields" type="String">Поля для представления (через запятую).</param>
/// <param name="SearchParams" type="Structure">Параметры поиска (СтрокаПоиска, СпособПоискаСтроки).</param>
/// <param name="AdditionalConditions" type="String" optional="True">Дополнительные условия WHERE.</param>
/// <returns type="ValueList">Готовый список для ДанныеВыбора.</returns>
Function AutoChoiceData(TableName, SearchFields, ValueField = "Ссылка", PresentationFields, SearchParams, AdditionalConditions = "НЕ ПометкаУдаления") Export
	
	Try
		SearchString = "";
		SearchMode = "Contains";
		
		// Извлекаем параметры поиска
		If SearchParams.Property("СтрокаПоиска") Then
			SearchString = SearchParams.СтрокаПоиска;
		EndIf;
		
		If SearchParams.Property("СпособПоискаСтроки") Then
			If SearchParams.СпособПоискаСтроки = PredefinedValue("Enum.SearchStringInputMethod.Beginning") Then
				SearchMode = "StartsWith";
			EndIf;
		EndIf;
		
		// Формируем запрос с нужными полями
		Fields = ValueField;
		If ValueIsFilled(PresentationFields) Then
			Fields = Fields + ", " + PresentationFields;
		EndIf;
		
		SearchQuery = BuildSearchQuery(TableName, SearchFields, SearchString, SearchMode, 20, AdditionalConditions);
		
		// Заменяем SELECT * на нужные поля
		SearchQuery.QueryText = StrReplace(SearchQuery.QueryText, "ВЫБРАТЬ ПЕРВЫЕ 20 *", "ВЫБРАТЬ ПЕРВЫЕ 20 " + Fields);
		
		VT = UnloadSafe(SearchQuery.QueryText, SearchQuery.Parameters);
		Result = New ValueList;
		
		// Формируем представление
		PresentationFieldsArray = StrSplit(PresentationFields, ",");
		
		For Each Row In VT Do
			Value = Row[ValueField];
			
			// Составляем представление из нескольких полей
			PresentationParts = New Array;
			For Each PresentationField In PresentationFieldsArray Do
				FieldName = TrimAll(PresentationField);
				If VT.Columns.Find(FieldName) <> Undefined Then
					PresentationParts.Add(String(Row[FieldName]));
				EndIf;
			EndDo;
			
			Presentation = StrConcat(PresentationParts, " - ");
			Result.Add(Value, Presentation);
		EndDo;
		
		Return Result;
		
	Except
		М1сAIСтроки.Print("AutoChoiceData error: " + ErrorDescription());
		Return New ValueList;
	EndTry;
	
EndFunction

/// <summary>
/// Упрощённая функция для стандартной ОбработкаПолученияДанныхВыбора.
/// Использовать в процедуре: ДанныеВыбора = М1сAIЗапросы.StandardChoiceProcessing(Параметры, "Справочник.Номенклатура", "Наименование", "Наименование, Артикул");
/// </summary>
/// <param name="Parameters" type="Structure">Стандартные параметры от платформы.</param>
/// <param name="TableName" type="String">Имя таблицы/справочника.</param>
/// <param name="SearchFields" type="String">Поля для поиска.</param>
/// <param name="PresentationFields" type="String">Поля для отображения.</param>
/// <param name="ValueField" type="String" default="Ссылка">Поле значения.</param>
/// <param name="AdditionalConditions" type="String" optional="True">Дополнительные условия.</param>
/// <returns type="ValueList">Данные для выбора.</returns>
Function StandardChoiceProcessing(Parameters, TableName, SearchFields, PresentationFields, ValueField = "Ссылка", AdditionalConditions = "НЕ ПометкаУдаления") Export
	
	SearchParams = New Structure;
	
	If Parameters.Property("СтрокаПоиска") Then
		SearchParams.Insert("СтрокаПоиска", Parameters.СтрокаПоиска);
	EndIf;
	
	If Parameters.Property("СпособПоискаСтроки") Then
		SearchParams.Insert("СпособПоискаСтроки", Parameters.СпособПоискаСтроки);
	EndIf;
	
	Return AutoChoiceData(TableName, SearchFields, ValueField, PresentationFields, SearchParams, AdditionalConditions);
	
EndFunction
#EndRegion

#Region М1сAIЗапросы_QuickSearch
/// <summary>
/// Быстрый поиск по справочнику с минимальными параметрами.
/// </summary>
/// <param name="CatalogName" type="String">Имя справочника без "Справочник.".</param>
/// <param name="SearchString" type="String">Строка поиска.</param>
/// <param name="SearchMode" type="String" default="Contains">Режим поиска.</param>
/// <returns type="ValueList">Список найденных элементов.</returns>
Function QuickCatalogSearch(CatalogName, SearchString, SearchMode = "Contains") Export
	
	TableName = "Справочник." + CatalogName;
	
	// Стандартные поля для поиска
	SearchFields = "Наименование, Код";
	PresentationFields = "Наименование, Код";
	
	Return SearchForChoice(TableName, SearchFields, "Ссылка", "Наименование", SearchString, SearchMode, 20, "НЕ ПометкаУдаления И НЕ ЭтоГруппа");
	
EndFunction

/// <summary>
/// Быстрый поиск по документу.
/// </summary>
/// <param name="DocumentName" type="String">Имя документа без "Документ.".</param>
/// <param name="SearchString" type="String">Строка поиска.</param>
/// <param name="SearchMode" type="String" default="Contains">Режим поиска.</param>
/// <returns type="ValueList">Список найденных документов.</returns>
Function QuickDocumentSearch(DocumentName, SearchString, SearchMode = "Contains") Export
	
	TableName = "Документ." + DocumentName;
	
	// Стандартные поля для поиска в документах
	SearchFields = "Номер";
	PresentationFields = "Номер, Дата";
	
	Return SearchForChoice(TableName, SearchFields, "Ссылка", "Номер", SearchString, SearchMode, 20, "НЕ ПометкаУдаления");
	
EndFunction
#EndRegion

#Region М1сAIЗапросы_Examples
/// <summary>
/// Примеры использования новых функций поиска.
/// </summary>
Procedure ShowSearchExamples() Export
	
	// 1. Простейший поиск по справочнику
	// ChoiceList = М1сAIЗапросы.QuickCatalogSearch("Номенклатура", "товар");
	
	// 2. В ОбработкаПолученияДанныхВыбора
	// Procedure ОбработкаПолученияДанныхВыбора(ДанныеВыбора, Параметры, СтандартнаяОбработка) Export
	//     СтандартнаяОбработка = False;
	//     ДанныеВыбора = М1сAIЗапросы.StandardChoiceProcessing(Параметры, 
	//         "РегистрСведений.ЖурналМашиночитаемыхДоверенностей", 
	//         "Номер", 
	//         "ПредставлениеДоверенности, Номер");
	// EndProcedure
	
	// 3. Расширенный поиск с дополнительными условиями
	// SearchQuery = М1сAIЗапросы.BuildSearchQuery(
	//     "Справочник.Контрагенты",
	//     "Наименование, ИНН",
	//     "ООО Рога",
	//     "Contains",
	//     50,
	//     "НЕ ПометкаУдаления И ЮрЛицоФизЛицо = Значение(Перечисление.ЮрФизЛицо.ЮрЛицо)"
	// );
	
EndProcedure
#EndRegion

#Region М1сAIЗапросы_ExistsQ
/// <summary>
/// Проверяет существование записей по запросу (оптимизированная версия IsNotEmptyResult).
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Boolean">Истина, если записи найдены.</returns>
Function ExistsQ(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	// Добавляем ПЕРВЫЕ 1 если его нет
	OptimizedText = QueryText;
	If Upper(Left(TrimAll(QueryText), 7)) = "ВЫБРАТЬ" And StrFind(Upper(QueryText), "ПЕРВЫЕ") = 0 Then
		OptimizedText = StrReplace(QueryText, "ВЫБРАТЬ", "ВЫБРАТЬ ПЕРВЫЕ 1");
	EndIf;
	
	Return IsNotEmptyResult(OptimizedText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
	
EndFunction

#Region examples_М1сAIЗапросы_ExistsQ
// Пример:
// If М1сAIЗапросы.ExistsQ("ВЫБРАТЬ * ИЗ Справочник.Номенклатура ГДЕ Наименование = &Name", "Товар") Then
//     Message("Товар найден");
// EndIf;
#EndRegion
#EndRegion

#Region М1сAIЗапросы_CountQ
/// <summary>
/// Выполняет запрос подсчета количества записей.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса или имя таблицы.</param>
/// <param name="Condition" type="String" optional="True">Условие WHERE.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Number">Количество записей.</returns>
Function CountQ(QueryText, Condition = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	FinalQueryText = QueryText;
	
	// Если передано простое имя таблицы, формируем запрос
	If StrFind(Upper(QueryText), "ВЫБРАТЬ") = 0 Then
		FinalQueryText = QT("КОЛИЧЕСТВО(*)", QueryText, Condition);
	EndIf;
	
	Return ValueQ(FinalQueryText, 0, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
	
EndFunction

#Region examples_М1сAIЗапросы_CountQ
// Пример 1: По имени таблицы
// Count = М1сAIЗапросы.CountQ("Справочник.Номенклатура", "НЕ ПометкаУдаления");

// Пример 2: По готовому запросу
// Count = М1сAIЗапросы.CountQ("ВЫБРАТЬ КОЛИЧЕСТВО(*) ИЗ Справочник.Номенклатура ГДЕ Родитель = &Parent", , ParentRef);
#EndRegion
#EndRegion

#Region М1сAIЗапросы_ChainQ
/// <summary>
/// Цепочка запросов с передачей TempTablesManager между ними.
/// </summary>
/// <param name="Queries" type="Array">Массив структур {Text, Params}.</param>
/// <param name="ReturnResults" type="Boolean" default="False">Возвращать результаты всех запросов.</param>
/// <returns type="Array">Массив результатов (если ReturnResults=True).</returns>
Function ChainQ(Queries, ReturnResults = False) Export
	
	TempManager = GetTemps();
	Results = New Array;
	
	For Each QueryInfo In Queries Do
		Try
			Query = CreateQ(QueryInfo.Text, TempManager);
			
			If QueryInfo.Property("Params") And QueryInfo.Params <> Undefined Then
				SetQParams(Query, QueryInfo.Params);
			EndIf;
			
			QueryResult = Query.Execute();
			
			If ReturnResults Then
				Results.Add(QueryResult.Select());
			EndIf;
			
		Except
			М1сAIСтроки.Print("ChainQ error at query " + (Results.Count() + 1) + ": " + ErrorDescription());
			Break;
		EndTry;
	EndDo;
	
	Return Results;
	
EndFunction

#Region examples_М1сAIЗапросы_ChainQ
// Пример:
// QueriesArray = New Array;
// QueriesArray.Add(New Structure("Text", "ВЫБРАТЬ * ИЗ Справочник.Номенклатура ПОМЕСТИТЬ ВТ_Товары"));
// QueriesArray.Add(New Structure("Text,Params", "ВЫБРАТЬ * ИЗ ВТ_Товары ГДЕ Родитель = &Parent", New Structure("Parent", ParentRef)));
// Results = М1сAIЗапросы.ChainQ(QueriesArray, True);
#EndRegion
#EndRegion

#Region М1сAIЗапросы_BatchUnload
/// <summary>
/// Выполняет несколько запросов параллельно и возвращает результаты в структуре.
/// </summary>
/// <param name="QueriesMap" type="Structure">Структура "Имя" -> "Текст запроса".</param>
/// <param name="CommonParams" type="Structure" optional="True">Общие параметры для всех запросов.</param>
/// <returns type="Structure">Структура "Имя" -> ValueTable.</returns>
Function BatchUnload(QueriesMap, CommonParams = Undefined) Export
	
	Results = New Structure;
	
	For Each QueryPair In QueriesMap Do
		Try
			Query = CreateQ(QueryPair.Value);
			
			If CommonParams <> Undefined Then
				SetQParams(Query, CommonParams);
			EndIf;
			
			Results.Insert(QueryPair.Key, Query.Execute().Unload());
			
		Except
			М1сAIСтроки.Print("BatchUnload error for '" + QueryPair.Key + "': " + ErrorDescription());
			Results.Insert(QueryPair.Key, New ValueTable);
		EndTry;
	EndDo;
	
	Return Results;
	
EndFunction

#Region examples_М1сAIЗапросы_BatchUnload
// Пример:
// Queries = New Structure;
// Queries.Insert("Товары", "ВЫБРАТЬ * ИЗ Справочник.Номенклатура ГДЕ Родитель = &Parent");
// Queries.Insert("Услуги", "ВЫБРАТЬ * ИЗ Справочник.Номенклатура ГДЕ ЭтоГруппа = ЛОЖЬ И ВидНоменклатуры = &ServiceType");
// 
// Params = New Structure;
// Params.Insert("Parent", ParentRef);
// Params.Insert("ServiceType", ServiceTypeRef);
// 
// Results = М1сAIЗапросы.BatchUnload(Queries, Params);
// // Results.Товары - таблица товаров
// // Results.Услуги - таблица услуг
#EndRegion
#EndRegion

#Region М1сAIЗапросы_QueryBuilder
/// <summary>
/// Конструктор запросов в fluent-стиле.
/// </summary>
/// <param name="Fields" type="String">Поля для выборки.</param>
/// <returns type="QueryBuilder">Объект-построитель запроса.</returns>
Function Select(Fields) Export
	
	Builder = New Structure;
	Builder.Insert("Fields", Fields);
	Builder.Insert("FromClause", "");
	Builder.Insert("WhereClause", "");
	Builder.Insert("OrderClause", "");
	Builder.Insert("GroupClause", "");
	Builder.Insert("TopClause", "");
	Builder.Insert("Parameters", New Structure);
	
	Return Builder;
	
EndFunction

/// <summary>
/// Устанавливает источник данных для QueryBuilder.
/// </summary>
Function From(Builder, TableName) Export
	Builder.FromClause = TableName;
	Return Builder;
EndFunction

/// <summary>
/// Добавляет условие WHERE для QueryBuilder.
/// </summary>
Function Where(Builder, Condition) Export
	If ValueIsFilled(Builder.WhereClause) Then
		Builder.WhereClause = Builder.WhereClause + " И " + Condition;
	Else
		Builder.WhereClause = Condition;
	EndIf;
	Return Builder;
EndFunction

/// <summary>
/// Добавляет параметр для QueryBuilder.
/// </summary>
Function WithParam(Builder, ParamName, ParamValue) Export
	Builder.Parameters.Insert(ParamName, ParamValue);
	Return Builder;
EndFunction

/// <summary>
/// Добавляет сортировку для QueryBuilder.
/// </summary>
Function OrderBy(Builder, OrderFields) Export
	Builder.OrderClause = OrderFields;
	Return Builder;
EndFunction

/// <summary>
/// Добавляет ограничение ПЕРВЫЕ для QueryBuilder.
/// </summary>
Function Top(Builder, Count) Export
	Builder.TopClause = "ПЕРВЫЕ " + Count;
	Return Builder;
EndFunction

/// <summary>
/// Строит и выполняет запрос из QueryBuilder.
/// </summary>
Function Build(Builder) Export
	
	QueryText = "ВЫБРАТЬ ";
	
	If ValueIsFilled(Builder.TopClause) Then
		QueryText = QueryText + Builder.TopClause + " ";
	EndIf;
	
	QueryText = QueryText + Builder.Fields + " ИЗ " + Builder.FromClause;
	
	If ValueIsFilled(Builder.WhereClause) Then
		QueryText = QueryText + " ГДЕ " + Builder.WhereClause;
	EndIf;
	
	If ValueIsFilled(Builder.GroupClause) Then
		QueryText = QueryText + " СГРУППИРОВАТЬ ПО " + Builder.GroupClause;
	EndIf;
	
	If ValueIsFilled(Builder.OrderClause) Then
		QueryText = QueryText + " УПОРЯДОЧИТЬ ПО " + Builder.OrderClause;
	EndIf;
	
	Query = CreateQ(QueryText);
	SetQParams(Query, Builder.Parameters);
	
	Return Query;
	
EndFunction

#Region examples_М1сAIЗапросы_QueryBuilder
// Пример fluent-стиля:
// Query = М1сAIЗапросы.Select("Ссылка, Наименование")
//            .From("Справочник.Номенклатура")
//            .Where("НЕ ПометкаУдаления")
//            .Where("Родитель = &Parent")
//            .WithParam("Parent", ParentRef)
//            .OrderBy("Наименование")
//            .Top("10")
//            .Build();
// 
// Result = Query.Execute().Unload();
#EndRegion
#EndRegion

#Region М1сAIЗапросы_CachedQuery
/// <summary>
/// Кэшированное выполнение запроса (простой кэш в памяти на время сеанса).
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="CacheKey" type="String">Ключ для кэша.</param>
/// <param name="CacheTTL" type="Number" default="300">TTL кэша в секундах.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="ValueTable">Результат запроса.</returns>
//Function CachedUnload(QueryText, CacheKey, CacheTTL = 300, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
//	
//	// Инициализация глобального кэша, если нет
//	If Not М1сAIGlobal.Property("QueryCache") Then
//		М1сAIGlobal.Insert("QueryCache", New Map);
//	EndIf;
//	
//	Cache = М1сAIGlobal.QueryCache;
//	CurrentTime = CurrentUniversalDate();
//	
//	// Проверяем наличие в кэше и актуальность
//	If Cache.Get(CacheKey) <> Undefined Then
//		CacheItem = Cache.Get(CacheKey);
//		If (CurrentTime - CacheItem.Timestamp) < CacheTTL Then
//			Return CacheItem.Data;
//		EndIf;
//	EndIf;
//	
//	// Выполняем запрос
//	Try
//		Result = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
//		
//		// Сохраняем в кэш
//		CacheItem = New Structure;
//		CacheItem.Insert("Data", Result);
//		CacheItem.Insert("Timestamp", CurrentTime);
//		Cache.Insert(CacheKey, CacheItem);
//		
//		Return Result;
//		
//	Except
//		М1сAIСтроки.Print("CachedUnload error: " + ErrorDescription());
//		Return New ValueTable;
//	EndTry;
//	
//EndFunction

#Region examples_М1сAIЗапросы_CachedQuery
// Пример:
// Result = М1сAIЗапросы.CachedUnload(
//     "ВЫБРАТЬ * ИЗ Справочник.Валюты ГДЕ НЕ ПометкаУдаления",
//     "AllCurrencies", 
//     600  // кэшируем на 10 минут
// );
#EndRegion
#EndRegion

#Region М1сAIЗапросы_QueryPagination
/// <summary>
/// Постраничное выполнение запроса.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="PageSize" type="Number">Размер страницы.</param>
/// <param name="PageNumber" type="Number">Номер страницы (начиная с 1).</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Structure">Структура с полями: Data (ValueTable), HasMore (Boolean), Total (Number).</returns>
Function PagedUnload(QueryText, PageSize, PageNumber, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Result = New Structure;
	Result.Insert("Data", New ValueTable);
	Result.Insert("HasMore", False);
	Result.Insert("Total", 0);
	
	Try
		// Сначала получаем общее количество
		CountQuery = StrReplace(Upper(QueryText), "ВЫБРАТЬ", "ВЫБРАТЬ КОЛИЧЕСТВО(*) КАК Total ИЗ (ВЫБРАТЬ") + ") AS CountQuery";
		TotalCount = ValueQ(CountQuery, 0, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Result.Total = TotalCount;
		
		// Вычисляем ПРОПУСТИТЬ и ПЕРВЫЕ
		SkipCount = (PageNumber - 1) * PageSize;
		TopCount = PageSize;
		
		// Модифицируем основной запрос
		PagedQueryText = QueryText;
		If StrFind(Upper(QueryText), "УПОРЯДОЧИТЬ ПО") = 0 Then
			PagedQueryText = PagedQueryText + " УПОРЯДОЧИТЬ ПО 1"; // Добавляем сортировку, если нет
		EndIf;
		
		// Добавляем ПРОПУСТИТЬ и ПЕРВЫЕ через подзапрос
		PagedQueryText = "ВЫБРАТЬ ПЕРВЫЕ " + TopCount + " * ИЗ (" + PagedQueryText + ") T";
		If SkipCount > 0 Then
			PagedQueryText = StrReplace(PagedQueryText, "ВЫБРАТЬ ПЕРВЫЕ", "ВЫБРАТЬ ПРОПУСТИТЬ " + SkipCount + " ПЕРВЫЕ");
		EndIf;
		
		// Выполняем запрос страницы
		Result.Data = Unload(PagedQueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Result.HasMore = (SkipCount + PageSize) < TotalCount;
		
	Except
		М1сAIСтроки.Print("PagedUnload error: " + ErrorDescription());
	EndTry;
	
	Return Result;
	
EndFunction

#Region examples_М1сAIЗапросы_QueryPagination
// Пример:
// Page = М1сAIЗапросы.PagedUnload(
//     "ВЫБРАТЬ Ссылка, Наименование ИЗ Справочник.Номенклатура ГДЕ НЕ ПометкаУдаления",
//     20,  // размер страницы
//     1    // первая страница
// );
// 
// Message("Найдено записей: " + Page.Total);
// Message("Есть еще страницы: " + Page.HasMore);
// // Page.Data содержит ValueTable с результатами
#EndRegion
#EndRegion

#Region М1сAIЗапросы_JSONExport
/// <summary>
/// Экспорт результата запроса в JSON.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="String">JSON-представление результата.</returns>
Function UnloadToJSON(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	Try
		VT = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		
		JSONWriter = New JSONWriter;
		JSONWriter.SetString();
		
		JSONData = New Array;
		
		For Each Row In VT Do
			RowData = New Structure;
			For Each Column In VT.Columns Do
				RowData.Insert(Column.Name, Row[Column.Name]);
			EndDo;
			JSONData.Add(RowData);
		EndDo;
		
		WriteJSON(JSONWriter, JSONData);
		Return JSONWriter.Close();
		
	Except
		М1сAIСтроки.Print("UnloadToJSON error: " + ErrorDescription());
		Return "[]";
	EndTry;
	
EndFunction

#Region examples_М1сAIЗапросы_JSONExport
// Пример:
// JSON = М1сAIЗапросы.UnloadToJSON("ВЫБРАТЬ Ссылка, Наименование ИЗ Справочник.Валюты ГДЕ НЕ ПометкаУдаления");
// М1сAIСтроки.Print(JSON);
#EndRegion
#EndRegion

#Region М1сAIЗапросы_QueryProfiler
/// <summary>
/// Профилировщик запросов - измеряет время выполнения.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="ProfileName" type="String" optional="True">Имя для логирования.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="Structure">Структура с полями: Result (ValueTable), Duration (Number), ProfileName (String).</returns>
Function ProfiledUnload(QueryText, ProfileName = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	
	StartTime = CurrentUniversalDateInMilliseconds();
	
	Try
		Result = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Duration = CurrentUniversalDateInMilliseconds() - StartTime;
		
		ProfileResult = New Structure;
		ProfileResult.Insert("Result", Result);
		ProfileResult.Insert("Duration", Duration);
		ProfileResult.Insert("ProfileName", ?(ValueIsFilled(ProfileName), ProfileName, "Query"));
		
		// Логируем результат
		М1сAIСтроки.Print("Query profiling [" + ProfileResult.ProfileName + "]: " + Duration + "ms, rows: " + Result.Count());
		
		Return ProfileResult;
		
	Except
		М1сAIСтроки.Print("ProfiledUnload error: " + ErrorDescription());
		Return New Structure("Result,Duration,ProfileName", New ValueTable, 0, ProfileName);
	EndTry;
	
EndFunction

#Region examples_М1сAIЗапросы_QueryProfiler
// Пример:
// Profile = М1сAIЗапросы.ProfiledUnload(
//     "ВЫБРАТЬ * ИЗ Справочник.Номенклатура ГДЕ Родитель = &Parent",
//     "LoadNomenclature",
//     ParentRef
// );
// 
// If Profile.Duration > 1000 Then
//     Message("Медленный запрос: " + Profile.Duration + "мс");
// EndIf;
#EndRegion
#EndRegion


#Region М1сAIЗапросы_IsEmptyResult
/// <summary>
/// Проверяет, что результат запроса пуст.
/// </summary>
/// <param name="QueryText" type="String"/>
/// <param name="Value1..Value8" type="Variant" optional="True"/>
/// <returns type="Boolean">Истина, если пусто.</returns>
Function IsEmptyResult(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export

	Try //⚠
		Selection = ExecuteQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Return Not Selection.Следующий(); //↩
	Except 
		М1сAIСтроки.Print("IsEmptyResult: ошибка выполнения запроса: " + ErrorDescription());
		Return True; //↩ Считаем, что если ошибка — результата нет
	EndTry;

EndFunction


#Region example_1_М1сAIЗапросы_IsEmptyResult

//If IsEmptyResult("ВЫБРАТЬ ПЕРВЫЕ 1 * ИЗ Справочник.Номенклатура ГДЕ Наименование = &Наименование", "Тестовая номенклатура") Then
//    // Выборка пуста, записи не найдены
//    Сообщить("Записи с таким наименованием не найдены.");
//Else
//    // Выборка содержит данные
//    Сообщить("Записи с таким наименованием найдены.");
//EndIf

#EndRegion

#EndRegion

#Region М1сAIЗапросы_IsNotEmptyResult
/// <summary>
/// Проверяет, что результат запроса не пуст.
/// </summary>
/// <param name="QueryText" type="String"/>
/// <param name="Value1..Value8" type="Variant" optional="True"/>
/// <returns type="Boolean">Истина, если есть данные.</returns>
Function IsNotEmptyResult(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export

	Try
		Selection = ExecuteQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Return Selection.Следующий();
	Except
		М1сAIСтроки.Print("IsNotEmptyResult: ошибка выполнения запроса: " + ErrorDescription());
		Return False;
	EndTry;

EndFunction
#Region example_1_М1сAIЗапросы_IsNotEmptyResult

//If IsNotEmptyResult("ВЫБРАТЬ ПЕРВЫЕ 1 * ИЗ Справочник.Номенклатура ГДЕ Наименование = &Наименование", "Тестовая номенклатура") Then
//    // Выборка не пуста, записи найдены
//    Сообщить("Записи с таким наименованием найдены.");
//Else
//    // Выборка пуста, записи не найдены
//    Сообщить("Записи с таким наименованием не найдены.");
//EndIf

#EndRegion

#EndRegion

#Region М1сAIЗапросы_Unload
/// <summary>
/// Выполняет запрос и выгружает таблицу значений.
/// </summary>
/// <param name="QueryText" type="String">Текст запроса.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Параметры.</param>
/// <returns type="ValueTable">Выгруженная таблица.</returns>
Function Unload(QueryText, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	// Создание запроса с параметрами
	Query = BuildQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
	
	// Выполнение запроса и выгрузка данных
	Return Query.Выполнить().Выгрузить();
EndFunction

/// <summary>Выгружает из TempTablesManager одну временную таблицу по имени.</summary>
Функция UnloadTemp(TempManager, TableName) Экспорт
	
	Если ТипЗнч(TempManager) <> Тип("TempTablesManager") Тогда
		Возврат Неопределено;
	КонецЕсли;
	
	// Собираем текст запроса "ВЫБРАТЬ * ИЗ <TableName>"
	ТекстЗапроса = 
	"ВЫБРАТЬ
	|   *
	|ИЗ " + TableName + " КАК T";
	
	// Создаём Query, привязываем TempTablesManager из первого шага
	Запрос = CreateQ(ТекстЗапроса, TempManager);
	// Выполняем и выгружаем
	Таб = Запрос.Выполнить().Выгрузить();
	
	Возврат Таб;
КонецФункции

#Region М1сAIЗапросы_UnloadAllTemps
/// <summary>Выгружает все временные таблицы из TempTablesManager в структуру.</summary>
/// <param name="TempManager" type="TempTablesManager">Менеджер временных таблиц.</param>
/// <returns type="Structure">Ключ=имя Temp-таблицы, Значение=ValueTable.</returns>
Функция UnloadAllTemps(TempManager) Экспорт
	Результат = Новый Структура;
	
	Если ТипЗнч(TempManager) <> Тип("TempTablesManager") Тогда
		Возврат Результат;
	КонецЕсли;
	
	// Предполагаем, что TempTablesManager хранит список имён временных таблиц в свойстве TemporaryTables
	Для Каждого ИмяТаблицы Из TempManager.Tables Цикл
		// Формируем и выполняем запрос "ВЫБРАТЬ * ИЗ <ИмяТаблицы>"
		
		ПолноеИмяТаблицы = ИмяТаблицы.ПолноеИмя;
		
		ТекстЗапроса =
		"ВЫБРАТЬ
		|   *
		|ИЗ " + ПолноеИмяТаблицы + " КАК T";
		
		// Создаём Query, передаём тот же TempTablesManager
		Запрос = CreateQ(ТекстЗапроса, TempManager);
		// Выполняем и выгружаем таблицу значений
		VT = Запрос.Выполнить().Выгрузить();
		
		// Сохраняем в результат под ключом имени
		Результат.Вставить(ПолноеИмяТаблицы, VT);
	КонецЦикла;
	
	Возврат Результат;
КонецФункции
#EndRegion


#Region examples_М1сAIЗапросы_Unload

#Region example_1_М1сAIЗапросы_Unload

// @example.1.М1сAIЗапросы.Unload {

//// Текст запроса
//QueryText = 
//"ВЫБРАТЬ
//|	АктивностьСеансовПользователей.ИдентификаторЗаданияДляОстановки КАК ИдентификаторЗаданияДляОстановки,
//|	АктивностьСеансовПользователей.ДатаПоследнейАктивностиУниверсальная КАК ДатаПоследнейАктивностиУниверсальная
//|ИЗ
//|	РегистрСведений.АктивностьСеансовПользователей КАК АктивностьСеансовПользователей
//|ГДЕ
//|	АктивностьСеансовПользователей.Организация = &Организация
//|	И АктивностьСеансовПользователей.Пользователь = &Пользователь";

//// Выполнение запроса с параметрами и выгрузка данных
//ТаблицаЗначений = Unload(QueryText, Источник.Организация, ТекущийПользователь);

// @example.1.М1сAIЗапросы.Unload }

#EndRegion

#Region example_2_М1сAIЗапросы_Unload

// @example.2.М1сAIЗапросы.Unload {

//// Пример 2
//QueryText = 
//"ВЫБРАТЬ
//|	ДругаяТаблица.Параметр1 КАК Параметр1,
//|	ДругаяТаблица.Параметр2 КАК Параметр2
//|ИЗ
//|	РегистрСведений.ДругаяТаблица КАК ДругаяТаблица
//|ГДЕ
//|	ДругаяТаблица.Параметр1 = &Параметр1";

//// Выполнение запроса с параметрами и выгрузка данных
//ТаблицаЗначений = Unload(QueryText, ЗначениеПараметра1);

// @example.2.М1сAIЗапросы.Unload }

#EndRegion

#EndRegion
#EndRegion

#Region М1сAIЗапросы_IsEmptyTable
/// <summary>
/// Проверяет, пуста ли ТаблицаЗначений.
/// </summary>
/// <param name="Data" type="ValueTable">ТаблицаЗначений для проверки.</param>
/// <returns type="Boolean">Истина, если таблица пуста или не определена.</returns>
Function IsEmptyTable(Data) Export
	If Data = Undefined Then
		Return True;
	EndIf;

	If TypeOf(Data) <> Type("ValueTable") Then
		М1сAIСтроки.Print("IsEmptyTable: ожидалась ТаблицаЗначений, получено " + TypeOf(Data));
		Return True;
	EndIf;

	Return Data.Количество() = 0;
EndFunction

#Region examples_М1сAIЗапросы_IsEmptyTable
// Пример 1: Пустая таблица
// vt = Новый ТаблицаЗначений;
// М1сAIСтроки.Print(IsEmptyTable(vt)); // TRUE

// Пример 2: Таблица с данными
// vt = Новый ТаблицаЗначений;
// vt.Колонки.Добавить("Число");
// r = vt.Добавить(); r.Число = 1;
// М1сAIСтроки.Print(IsEmptyTable(vt)); // FALSE
#EndRegion

#EndRegion

#Region М1сAIЗапросы_UnloadColumn

/// <summary>
/// Выгружает из результата запроса один столбец в массив.
/// </summary>
/// <param name="QueryText" type="String"/>
/// <param name="ColumnName" type="String"/>
/// <param name="Value1..Value8" type="Variant" optional="True"/>
/// <returns type="Array">Массив значений столбца.</returns>
Function UnloadColumn(QueryText, ColumnName, Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
    // Выполнение запроса и выгрузка данных
    ResultTable = Unload(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);

    // Выгрузка колонки
    ColumnValues = ResultTable.ВыгрузитьКолонку(ColumnName);

    // Возврат массива значений колонки
    Return ColumnValues;
EndFunction

#Region examples_М1сAIЗапросы_UnloadColumn

//// Текст запроса
//QueryText =
//"ВЫБРАТЬ
//|  Хозрасчетный.Ссылка КАК СчетУчета
//|ИЗ
//|  ПланСчетов.Хозрасчетный КАК Хозрасчетный
//|ГДЕ
//|  НЕ Хозрасчетный.ЗапретитьИспользоватьВПроводках
//|  И Хозрасчетный.Ссылка В ИЕРАРХИИ(&СчетаУчета)
//|  И НЕ Хозрасчетный.Ссылка В ИЕРАРХИИ (&СчетаИсключений)
//|
//|УПОРЯДОЧИТЬ ПО
//|  Хозрасчетный.Порядок";

//// Выгрузка колонки
//ColumnValues = UnloadColumn(QueryText, "СчетУчета", СчетаУчета, СчетаИсключений);

//// Пример использования результата
//Для Каждого Значение Из ColumnValues Цикл
//    Сообщить(Значение);
//КонецЦикла;

#EndRegion

#EndRegion 

#Region ByQT

#Region М1сAIЗапросы_BuildByQT

/// <summary>
/// Собирает запрос через QT и устанавливает параметры.
/// </summary>
/// <param name="Fields" type="String">Список выбираемых полей.</param>
/// <param name="FromWhere" type="String">Имя таблицы или запроса.</param>
/// <param name="Condition" type="String" optional="True">Условие WHERE.</param>
/// <param name="Value1..Value8" type="Variant" optional="True">Значения параметров.</param>
/// <returns type="Query">Сконфигурированный объект Query.</returns>
Function BuildByQT(Fields, FromWhere, Condition = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	Try
		QueryText = QT(Fields, FromWhere, Condition);
		Return BuildQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
	Except
		М1сAIСтроки.Print("BuildByQT error: " + ErrorDescription(), "Ошибка", ":");
		Return Undefined;
	EndTry;
EndFunction
#Region examples_М1сAIЗапросы_BuildByQT
// Пример:
// q = М1сAIЗапросы.BuildByQT("Ссылка", "Справочник.Номенклатура", "Наименование = &Имя", "Товар");
#EndRegion
#EndRegion

#Region М1сAIЗапросы_ExecuteByQT
/// <summary>
/// Выполняет запрос, собранный через QT.
/// </summary>
/// <param name="Fields" type="String"/>
/// <param name="FromWhere" type="String"/>
/// <param name="Condition" type="String" optional="True"/>
/// <param name="Value1..Value8" type="Variant" optional="True"/>
/// <returns type="Selection">Результат выполнения запроса.</returns>
Function ExecuteByQT(Fields, FromWhere, Condition = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	Try
		Query = BuildByQT(Fields, FromWhere, Condition, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Return Query.Выполнить().Выбрать();
	Except
		М1сAIСтроки.Print("ExecuteByQT error: " + ErrorDescription(), "Ошибка", ":");
		Return Undefined;
	EndTry;
EndFunction
#Region examples_М1сAIЗапросы_ExecuteByQT
// Пример:
// s = М1сAIЗапросы.ExecuteByQT("Ссылка", "Справочник.Номенклатура", "ПометкаУдаления = ЛОЖЬ");
#EndRegion
#EndRegion

#Region М1сAIЗапросы_UnloadByQT

/// <summary>
/// Выполняет QT-запрос и выгружает таблицу значений.
/// </summary>
/// <param name="Fields" type="String"/>
/// <param name="FromWhere" type="String"/>
/// <param name="Condition" type="String" optional="True"/>
/// <param name="Value1..Value8" type="Variant" optional="True"/>
/// <returns type="ValueTable">Результат в виде таблицы значений.</returns>
Function UnloadByQT(Fields, FromWhere, Condition = "", Value1 = Undefined, Value2 = Undefined, Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined, Value7 = Undefined, Value8 = Undefined) Export
	Try
		Query = BuildByQT(Fields, FromWhere, Condition, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
		Return Query.Выполнить().Выгрузить();
	Except
		М1сAIСтроки.Print("UnloadByQT error: " + ErrorDescription(), "Ошибка", ":");
		Return Новый ТаблицаЗначений;
	EndTry;
EndFunction
#Region examples_М1сAIЗапросы_UnloadByQT
// Пример:
// ТЗ = М1сAIЗапросы.UnloadByQT("Ссылка", "Справочник.Номенклатура", "Наименование = &Имя", "Товар 1");
#EndRegion
#EndRegion

#EndRegion

#Region Misc

/// <summary>
/// Быстрая сборка текста запроса: SELECT WhatToSelect FROM FromWhereSelect [WHERE Condition].
/// </summary>
Function QT(WhatToSelect, FromWhereSelect, Condition = Undefined) Export
	
	QT = "ВЫБРАТЬ " + WhatToSelect + " ИЗ " + FromWhereSelect;
	
	If ValueIsFilled(Condition) Then
		QT = QT + " ГДЕ "+ Condition;
	EndIf;	
	
	Return QT;
    
EndFunction


/// <summary>
/// Экранирует специальные символы для оператора LIKE.
/// </summary>
Function EscapeLike(SearchString) Export
	Result = SearchString;
	Result = StrReplace(Result, "~", "~~");
	Result = StrReplace(Result, "%", "~%");
	Result = StrReplace(Result, "_", "~_");
	Result = StrReplace(Result, "[", "~[");
	Result = StrReplace(Result, "]", "~]");
	Result = StrReplace(Result, "^", "~^");
	Return Result;
EndFunction


/// <summary>
/// Формирует текст разделителя между частями запроса.
/// </summary>
Function QuerySeparator() Export
	Return "
	|;
	|
	|////////////////////////////////////////////////////////////////////////////////
	|";
EndFunction


/// <summary>
/// Формирует текст оператора UNION ALL между двумя запросами.
/// </summary>
Function CombineQT(QueryText1 = Undefined, QueryText2 = Undefined) Export
	
	UnionText = "
	|
	|ОБЪЕДИНИТЬ ВСЕ
	|
	|";
	
	If (QueryText1 = Undefined) And (QueryText2 = Undefined) Then
		
	Return UnionText;     
	
Else          
	
	Return QueryText1 + UnionText + QueryText2;     
	
	EndIf;
	
EndFunction

//
//Function UnionQueries(QueryText1, QueryText2) Export
//    Return QueryText1 + CombineQueries() + QueryText2;
//EndFunction

//

/// <summary>
/// Формирует шаблон LIKE с процентами и экранированием.
/// </summary>
Function LikePattern(SearchString) Export
	Return "%" + EscapeLike(SearchString) + "%";
EndFunction

/// <summary>
/// Собирает текст условия WHERE из массива строк-условий.
/// Фильтрует пустые строки, чтобы избежать некорректных конструкций типа "ГДЕ  И ".
/// </summary>
/// <param name="ConditionsArray" type="Array">Массив строк, каждая из которых - условие для WHERE.</param>
/// <param name="Operator" type="String" default="И">Логический оператор для соединения условий ("И" или "ИЛИ").</param>
/// <param name="AddWhereKeyword" type="Boolean" default="True">Добавлять ли ключевое слово "ГДЕ" в начало.</param>
/// <returns type="String">Собранный текст условия. Пустая строка, если массив пуст.</returns>
Function BuildWhere(ConditionsArray, Operator = "И", AddWhereKeyword = True) Export
	
	// 1. Фильтруем пустые строки, чтобы не было "ГДЕ  И ..."
	ValidConditions = Новый Массив;
	Для Каждого Condition Из ConditionsArray Цикл
		Если Не ПустаяСтрока(СокрЛП(Condition)) Тогда
			ValidConditions.Добавить(Condition);
		КонецЕсли;
	КонецЦикла;
	
	// 2. Если после фильтрации условий не осталось, возвращаем пустую строку
	Если ValidConditions.Количество() = 0 Тогда
		Возврат "";
	КонецЕсли;
	
	// 3. Соединяем условия через оператор
	Clause = СтрСоединить(ValidConditions, " " + Operator + " ");
	
	// 4. При необходимости добавляем "ГДЕ "
	Если AddWhereKeyword Тогда
		Возврат "ГДЕ " + Clause;
	Иначе
		Возврат Clause;
	КонецЕсли;
	
EndFunction

#EndRegion

// ----------------------------------------------------------
// TEMP TABLES MANAGEMENT
// ----------------------------------------------------------

#Region TemporaryTables
/// <summary>
/// Возвращает новый менеджер временных таблиц для использования в нескольких запросах.
/// </summary>
/// <returns type="TempTablesManager">Менеджер временных таблиц.</returns>
Function GetTemps() Export
	Return New TempTablesManager;
EndFunction

// Создает временную таблицу из запроса
//
// Параметры:
//  QueryText - Строка - Текст запроса
//  TempTableName - Строка - Имя временной таблицы
//  Value1...Value8 - Произвольный - Значения параметров запроса
//
// Возвращаемое значение:
//  РезультатЗапроса - Результат создания временной таблицы
//             

//
//Function CreateTempTable(QueryText, TempTableName, Value1 = Undefined, Value2 = Undefined,
//	Value3 = Undefined, Value4 = Undefined, Value5 = Undefined, Value6 = Undefined,
//	Value7 = Undefined, Value8 = Undefined) Export
//	
//	// Создаем запрос
//	Query = BuildQ(QueryText, Value1, Value2, Value3, Value4, Value5, Value6, Value7, Value8);
//	
//	// Добавляем в запрос создание временной таблицы
//	Query.TempTablesManager = New TempTablesManager;
//	Query.MoveToTempTable(TempTableName);   
//	
//	//q=new query;
//	//q.МенеджерВременныхТаблиц = Undefined;
//	
//	Return Query.Execute();
//EndFunction


#EndRegion

// ----------------------------------------------------------
// М1сAIЗапросы - Temp Table helpers                     
// ----------------------------------------------------------

Функция TT_Create(TTManager, Table, OptionalName = "") Экспорт
	// Проверка: таблица не задана или не инициализирована
	Если ТипЗнч(Table) <> Тип("ТаблицаЗначений") Тогда
		Возврат Неопределено;
	КонецЕсли;
	
	ИмяВТ = ?(ПустаяСтрока(OptionalName), "TT_" + СтрЗаменить(Новый УникальныйИдентификатор, "-", "_"), OptionalName);
	
	q = Новый Запрос;
	q.МенеджерВременныхТаблиц = TTManager;
	q.Текст =
	"ВЫБРАТЬ
	|  *
	|ПОМЕСТИТЬ " + ИмяВТ + "
	|ИЗ &Таблица КАК T";
	
	q.УстановитьПараметр("Таблица", Table);
	q.Выполнить();
	
	Возврат ИмяВТ;
КонецФункции

Функция TT_Columns(TTManager, TTName) Экспорт
	Запрос = Новый Запрос;
	Запрос.МенеджерВременныхТаблиц = TTManager;
	Запрос.Текст = "ВЫБРАТЬ ПЕРВЫЕ 0 * ИЗ " + TTName + " КАК T";
	
	Попытка
		Возврат Запрос.Выполнить().Выгрузить();
	Исключение
		Возврат Новый ТаблицаЗначений;
	КонецПопытки;
КонецФункции

Функция TT_Exists(TTManager, TTName) Экспорт
	Для каждого Таблица Из TTManager.Таблицы Цикл
		Если Таблица = TTName Тогда
			Возврат Истина;
		КонецЕсли;
	КонецЦикла;
	Возврат Ложь;
КонецФункции

Функция TT_HasColumn(TTManager, TTName, ColumnName) Экспорт
	Таблица = TT_Columns(TTManager, TTName);
	Возврат Таблица.Колонки.Найти(ColumnName) <> Неопределено;
КонецФункции

Функция TT_HasColumns(TTManager, TTName, ColumnNamesStr) Экспорт
	Если ПустаяСтрока(ColumnNamesStr) Тогда
		Возврат Ложь;
	КонецЕсли;
	
	// Разбиваем строку в массив
	Имена = СтрРазделить(ColumnNamesStr, ",");
	
	// Убираем пробелы — теперь через цикл Пока
	Индекс = 0;
	Пока Индекс < Имена.Количество() Цикл
		Имена[Индекс] = СтрЗаменить(Имена[Индекс], " ", "");
		Индекс = Индекс + 1;
	КонецЦикла;
	
	Cols = TT_Columns(TTManager, TTName);
	Колонки = Cols.Колонки;
	
	Для каждого ИмяКолонки Из Имена Цикл
		Если Колонки.Найти(ИмяКолонки) = Неопределено Тогда
			Возврат Ложь;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Истина;
КонецФункции

// ================================================
// TP_ — Метаданные Табличных Частей (Table Parts)
// Используется для анализа структуры табличных частей
// объектов метаданных (документов, справочников и т.д.)
// ================================================

Функция TP_HasField(Metadata, TPName, FieldName) Экспорт
	TPDesc = Metadata.ТабличныеЧасти[TPName];
	Если TPDesc = Неопределено Тогда
		Возврат Ложь;
	КонецЕсли;
	
	Для каждого R Из TPDesc.Реквизиты Цикл
		Если R.Имя = FieldName Тогда
			Возврат Истина;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Ложь;
КонецФункции

Функция TP_Fields(Metadata, TPName) Экспорт
	Fields = Новый Массив;
	TPDesc = Metadata.ТабличныеЧасти[TPName];
	Если TPDesc = Неопределено Тогда
		Возврат Fields;
	КонецЕсли;
	
	Для каждого R Из TPDesc.Реквизиты Цикл
		Fields.Добавить(R.Имя);
	КонецЦикла;
	
	Возврат Fields;
КонецФункции

#Region TP_ValidateFields
// <doc>
//   <summary>Проверяет, что строка табличной части содержит все необходимые реквизиты и обязательные поля заполнены.</summary>
//   <param i="1" name="Metadata"      type="MetadataObject">Метаданные объекта.</param>
//   <param i="2" name="TPName"        type="String">Имя табличной части.</param>
//   <param i="3" name="Row"           type="Structure">Строка табличной части для проверки.</param>
//   <param i="4" name="RequiredFields" type="Variant" default="Неопределено">Массив или строка с именами обязательных полей.</param>
//   <returns>Boolean — Истина, если все обязательные поля присутствуют и заполнены.</returns>
// </doc>
Функция TP_ValidateFields(Metadata, TPName, Row, RequiredFields = Неопределено) Экспорт
	TPDesc = Metadata.ТабличныеЧасти[TPName];
	Если TPDesc = Неопределено Тогда
		Возврат Истина;
	КонецЕсли;

	Если ТипЗнч(RequiredFields) = Тип("Строка") Тогда
		RequiredFields = СтрРазделить(RequiredFields, ",");
	КонецЕсли;

	Для каждого R Из TPDesc.Реквизиты Цикл
		ИмяПоля = R.Имя;
		Если Не Row.Свойство(ИмяПоля) Тогда
			Возврат Ложь;
		КонецЕсли;
		Если RequiredFields <> Неопределено И RequiredFields.Содержит(ИмяПоля) Тогда
			Если Не ЗначениеЗаполнено(Row[ИмяПоля]) Тогда
				Возврат Ложь;
			КонецЕсли;
		КонецЕсли;
	КонецЦикла;

	Возврат Истина;
КонецФункции

#Region examples_TP_ValidateFields
// Пример 1: Проверка строки с обязательными полями "Номенклатура,Количество"
//Строка = Новый Структура("Номенклатура,Количество", "Товар1", 5);
//Результат = М1сAIЗапросы.TP_ValidateFields(Метаданные.Документы.ЗаказПокупателя, "Товары", Строка, "Номенклатура,Количество");
// Ожидается Истина

// Пример 2: Обязательное поле "Количество" не заполнено
//Строка2 = Новый Структура("Номенклатура,Количество", "Товар1", Неопределено);
//Результат2 = М1сAIЗапросы.TP_ValidateFields(Метаданные.Документы.ЗаказПокупателя, "Товары", Строка2, "Номенклатура,Количество");
// Ожидается Ложь

// Пример 3: Отсутствует поле "Цена"
//Строка3 = Новый Структура("Номенклатура,Количество", "Товар1", 10);
//Результат3 = М1сAIЗапросы.TP_ValidateFields(Метаданные.Документы.ЗаказПокупателя, "Товары", Строка3, "Номенклатура,Количество,Цена");
// Ожидается Ложь
#EndRegion

#EndRegion


Функция TP_GetFieldType(Metadata, TPName, FieldName) Экспорт
	TPDesc = Metadata.ТабличныеЧасти[TPName];
	Если TPDesc = Неопределено Тогда
		Возврат Неопределено;
	КонецЕсли;
	
	Для каждого R Из TPDesc.Реквизиты Цикл
		Если R.Имя = FieldName Тогда
			Возврат ТипЗнч(R);
		КонецЕсли;
	КонецЦикла;
	
	Возврат Неопределено;
КонецФункции

Процедура Тест_TT_Функции() Экспорт
	Сообщить("== Тест TT_Columns, TT_HasColumn, TT_Keys ==");
	
	// Создаем временную таблицу
	ВТ = Новый ТаблицаЗначений;
	ВТ.Колонки.Добавить("Код", М1сAITypes.StringType(10));
	ВТ.Колонки.Добавить("Количество", М1сAITypes.NumberType(10,2));
	
	ВТ.Добавить().Код = "A01";
	ВТ.Добавить().Код = "B02";
	
	МенеджерВТ = Новый МенеджерВременныхТаблиц;

	ИмяВТ = М1сAIЗапросы.TT_Create(МенеджерВТ, ВТ);
	
	// TT_Columns
	cols = М1сAIЗапросы.TT_Columns(МенеджерВТ, ИмяВТ);
	Если cols.Колонки.Количество() <> 2 Тогда
		М1сAIСтроки.Print("TT_Columns не вернул правильную структуру колонок.");
	Иначе
		Сообщить("✔ TT_Columns: ОК");
	КонецЕсли;
	
	// ПРОВЕРИМ СРАЗУ ИМЕНА КОЛОНОК ПО ОДНОЙ
	// TT_HasColumn
	Если НЕ М1сAIЗапросы.TT_HasColumn(МенеджерВТ, ИмяВТ, "Код") Тогда
		М1сAIСтроки.Print("TT_HasColumn не нашел существующую колонку.");
	Иначе
		Сообщить("✔ TT_HasColumn (Код): ОК");
	КонецЕсли;
	
	Если М1сAIЗапросы.TT_HasColumn(МенеджерВТ, ИмяВТ, "НетТакой") Тогда
		М1сAIСтроки.Print("TT_HasColumn нашел несуществующую колонку.");
	Иначе
		Сообщить("✔ TT_HasColumn (НетТакой): ОК");
	КонецЕсли;

	// ПРОВЕРИМ СРАЗУ НЕСКОЛЬКО ИМЁН КОЛОНОК
	Если М1сAIЗапросы.TT_HasColumns(МенеджерВТ, ИмяВТ, "Код, Количество") Тогда
		Сообщить("✔ Все колонки есть");
	Иначе
		Сообщить("❌ Не все поля найдены");
	КонецЕсли;
	
	// TT_Keys (проверим на стандартном документе)
	// Пример: Документ "ПоступлениеТоваровУслуг" — замени на свой
	Попытка
		МетаданныеДокумента = Метаданные.Документы.ПоступлениеТоваровУслуг;
		keys = М1сAIЗапросы.TP_Fields(МетаданныеДокумента, "Товары");
		
		Если keys.Количество() = 0 Тогда
			М1сAIСтроки.Print("TT_Keys не нашел ключей у табличной части.");
		Иначе
			Сообщить("✔ TT_Keys (Товары): " + СтрСоединить(keys, ", "));
		КонецЕсли;
	Исключение
		Сообщить("⚠ TT_Keys: Пример документа не найден. Проверь имя.");
	КонецПопытки;
	
	Сообщить("== М1сAIЗапросы.TT_* тест завершен ==");
КонецПроцедуры

Процедура Тест_TP_Функции() Экспорт
	Сообщить("== Тест TP_* (табличные части метаданных) ==");

	Попытка
		MD = Метаданные.Документы.ПоступлениеТоваровУслуг;
		TPName = "Товары";

		// TP_Fields
		fields = М1сAIЗапросы.TP_Fields(MD, TPName);
		Если fields.Количество() > 0 Тогда
			Сообщить("✔ TP_Fields: " + СтрСоединить(fields, ", "));
		Иначе
			М1сAIСтроки.Print("✖ TP_Fields не вернул поля.");
		КонецЕсли;

		// TP_HasField
		Если М1сAIЗапросы.TP_HasField(MD, TPName, "Номенклатура") Тогда
			Сообщить("✔ TP_HasField (Номенклатура): ОК");
		Иначе
			М1сAIСтроки.Print("✖ TP_HasField не нашел поле 'Номенклатура'");
		КонецЕсли;

		// TP_Keys
		keys = М1сAIЗапросы.TP_Fields(MD, TPName);
		Если keys.Количество() > 0 Тогда
			Сообщить("✔ TP_Keys: " + СтрСоединить(keys, ", "));
		Иначе
			М1сAIСтроки.Print("✖ TP_Keys не вернул ключи.");
		КонецЕсли;

		// TP_ValidateRequiredFields
		Строка = Новый Структура;
		Строка.Вставить("Номенклатура", Справочники.Номенклатура.ПустаяСсылка());

		Результат = М1сAIЗапросы.TP_ValidateFields(MD, TPName, Строка);
		Если НЕ Результат Тогда
			Сообщить("✔ TP_ValidateRequiredFields: нашел ошибку — ОК");
		Иначе
			М1сAIСтроки.Print("✖ TP_ValidateRequiredFields не сработал на пустом значении.");
		КонецЕсли;

	Исключение
		М1сAIСтроки.Print("Ошибка выполнения TP_ теста. Проверь наличие документа 'ПоступлениеТоваровУслуг'.");
	КонецПопытки;

	Сообщить("== Тест TP_* завершен ==");
КонецПроцедуры



#Region М1сAIОбщие_GetBalances
/// <summary>
/// Формирует текст запроса для получения остатков по указанному бухгалтерскому регистру и дополнительному условию.
/// </summary>
/// <param name="WhereConditionText" type="String" optional="True">
/// Дополнительное условие WHERE (текст SQL-условия после ключевого слова WHERE).</param>
/// <param name="НазваниеРегистраБухгалтерии" type="String" default="Хозрасчетный">
/// Имя регистра бухгалтерии (например, «Хозрасчетный» или «Валютный»).</param>
/// <returns type="String">
/// Текст запроса SELECT … FROM РегистрБухгалтерии.&lt;НазваниеРегистраБухгалтерии&gt;.Остатки.</returns>
Функция GetBalancesQueryText(WhereConditionText = Неопределено, НазваниеРегистраБухгалтерии = "Хозрасчетный") Экспорт  
	
	// Проверяем существование регистра бухгалтерии
	Try
		
		// Формируем текст запроса
		QueryText = 
		"ВЫБРАТЬ
		|   Остатки.Субконто1 КАК Субконто1,
		|   Остатки.Субконто2 КАК Субконто2,
		|   Остатки.Субконто3 КАК Субконто3,
		|   Остатки.Счет КАК СчетУчета,
		|   Остатки.СуммаОстатокДт КАК СуммаДт,
		|   Остатки.СуммаОстатокКт КАК СуммаКт
		|ИЗ
		|   РегистрБухгалтерии." + НазваниеРегистраБухгалтерии + ".Остатки(
		|           &Период,
		|           Счет В ИЕРАРХИИ (&Счета),
		|           ,
		|           Организация = &Организация
		|       ) КАК Остатки
		| ";
		
		// Если есть дополнительные параметры, добавляем их в условие WHERE
		Если ValueIsFilled(WhereConditionText) Тогда
			
			QueryText = QueryText + " " + WhereConditionText;
			
		КонецЕсли;
		
	Except 
	EndTry;
	
	Возврат QueryText;
	
КонецФункции
 
#Region examples_М1сAIОбщие_GetBalancesQueryText
// Пример 1: стандартный остаток за период
// txt = М1сAIОбщие.GetBalancesQueryText("", "Хозрасчетный");
// Message(txt);

// Пример 2: с дополнительным условием (по складу)
// condition = "И Остатки.Склад = &Склад";
// txt = М1сAIОбщие.GetBalancesQueryText(condition, "Хозрасчетный");
// Message(txt);
#EndRegion
#EndRegion

#Region Tests

#Region М1сAIЗапросы_SelfTest
/// <summary>Выполняет тесты для М1сAIЗапросы.</summary>
/// <returns type="Boolean">Истина при успешном прохождении тестов.</returns>
Function SelfTest() Export
    // Проверка CreateQ
    q = CreateQ(); If q = Undefined Тогда М1сAIСтроки.Print("SelfTest FAILED: CreateQ"); Return False; EndIf;
    // Проверка GetParams
    q2 = CreateQ("SELECT &X AS X"); params = GetParams(q2); If params.Count()<>1 Тогда М1сAIСтроки.Print("SelfTest FAILED: GetParams"); Return False; EndIf;
    // Проверка BuildQ/ExecuteQ
    // Создадим временную таблицу данных
    tmp = М1сAIЗапросы.GetTemps();
    q3 = CreateQ("SELECT 1 AS a", tmp);
    
    res = ExecuteQ("ВЫБРАТЬ 1 КАК a");
    
    If res.Следующий() Then
	    If res.a <> 1 Then
		    М1сAIСтроки.Print("SelfTest FAILED: ExecuteQ — res.a ≠ 1");
		    Return False;
	    EndIf;
    Else
	    М1сAIСтроки.Print("SelfTest FAILED: ExecuteQ — empty");
	    Return False;
    EndIf;

    // Проверка Unload
    vt = Unload("ВЫБРАТЬ 1 КАК a");
    If IsEmptyTable(vt) Тогда
	    М1сAIСтроки.Print("SelfTest FAILED: Unload");
	    Return False;
    EndIf;
    
    // Проверка UnloadColumn
    arr = UnloadColumn("SELECT 1 AS a", "a"); If arr.Count()<>1 Тогда М1сAIСтроки.Print("SelfTest FAILED: UnloadColumn"); Return False; EndIf;
    // Проверка пустоты
    empty = IsEmptyResult("SELECT * FROM (SELECT 1 AS a) T WHERE a=0"); If Not empty Тогда М1сAIСтроки.Print("SelfTest FAILED: IsEmptyResult"); Return False; EndIf;
    // Проверка непустоты
    notEmpty = IsNotEmptyResult("SELECT 1 AS a"); If Not notEmpty Тогда М1сAIСтроки.Print("SelfTest FAILED: IsNotEmptyResult"); Return False; EndIf;
    
    // byQT test
    ByQTTestPassed = SelfTest_ByQT();
    If Not ByQTTestPassed Тогда М1сAIСтроки.Print("SelfTest FAILED: ByQTTestPassed"); Return False; EndIf;
    
    М1сAIСтроки.Print("М1сAIЗапросы: SelfTest passed");
    Return True;
EndFunction
#EndRegion

#Region М1сAIЗапросы_ByQT_SelfTest
/// <summary>
/// Самотестирование функций ByQT (Build/Execute/Unload).
/// </summary>
Function SelfTest_ByQT() Export
	Try
		// Build
		Query = BuildByQT("Ссылка", "Справочник.Номенклатура", "ПометкаУдаления = ЛОЖЬ");
		If Query = Undefined Then Return False; EndIf;

		// Execute
		Sel = ExecuteByQT("Ссылка", "Справочник.Номенклатура");
		If Sel = Undefined Тогда Return False;  EndIf;

		// Unload
		TZ = UnloadByQT("Ссылка", "Справочник.Номенклатура");
		If TZ = Undefined Тогда Return False;  EndIf;

		Return True;
	Except
		М1сAIСтроки.Print("SelfTest_ByQT failed: " + ErrorDescription(), "SelfTest", ":");
		Return False;
	EndTry;
EndFunction
#EndRegion

#EndRegion                                                                

#Region М1сAIЗапросы_DestroyTemp
/// <summary>Гарантированно очищает (FASTTRUNCATE) одну временную таблицу.</summary>
/// <param name="TempManager" type="TempTablesManager">Менеджер временных таблиц.</param>
/// <param name="TableName" type="String">Имя Temp-таблицы.</param>
Функция DestroyTemp(TempManager, TableName) Экспорт
    Если ТипЗнч(TempManager) <> Тип("TempTablesManager") Тогда
        Возврат Ложь;
    КонецЕсли;
    // Пакет с одной инструкцией УНИЧТОЖИТЬ
    Текст = "УНИЧТОЖИТЬ " + TableName + ";";
    Запрос = М1сAIЗапросы.CreateQWithTemps(Текст, TempManager);
    Запрос.ВыполнитьПакет();
    Возврат Истина;
КонецФункции
#EndRegion

#Region М1сAIЗапросы_DestroyAllTemps
/// <summary>Гарантированно очищает (FASTTRUNCATE) все временные таблицы в менеджере.</summary>
/// <param name="TempManager" type="TempTablesManager">Менеджер временных таблиц.</param>
Функция DestroyAllTemps(TempManager) Экспорт
    Если ТипЗнч(TempManager) <> Тип("TempTablesManager") Тогда
        Возврат Ложь;
    КонецЕсли;
    // Собираем имена через запятую
    Список = "";
    Для Каждого ИмяТаблицы Из TempManager.TemporaryTables Цикл
        Если Список = "" Тогда
            Список = ИмяТаблицы;
        Иначе
            Список = Список + ", " + ИмяТаблицы;
        КонецЕсли;
    КонецЦикла;
    Если Список = "" Тогда
        Возврат Ложь;
    КонецЕсли;
    // Пакет для всех таблиц
    Текст = "УНИЧТОЖИТЬ " + Список + ";";
    Запрос = М1сAIЗапросы.CreateQWithTemps(Текст, TempManager);
    Запрос.ВыполнитьПакет();
    Возврат Истина;
КонецФункции
#EndRegion

#Region М1сAIЗапросы_ResetTempManager
/// <summary>
/// Очищает все временные таблицы и сбрасывает TempTablesManager, освобождая ресурсы.
/// </summary>
/// <param name="ByRef TempManager" type="TempTablesManager">Менеджер временных таблиц.</param>
Процедура ResetTempManager(Знач TempManager) Экспорт
    Если ТипЗнч(TempManager) = Тип("TempTablesManager") Тогда
        // Сначала уничтожаем все временные таблицы
        М1сAIЗапросы.DestroyAllTemps(TempManager);
    КонецЕсли;
    // Затем сбрасываем сам менеджер
    TempManager = Неопределено;
КонецПроцедуры
#EndRegion             
#Region М1сAIЗапросы_ExecuteBatch
/// <summary>Выполняет пакет запросов и возвращает массив выборок (Selection).</summary>
/// <param name="QueryText" type="String">Текст пакетного запроса.</param>
/// <param name="TempManager" type="TempTablesManager">Менеджер временных таблиц.</param>
/// <param name="Params" type="Structure" optional="True">Структура параметров.</param>
/// <returns type="Array">Массив объектов Selection.</returns>
Функция ExecuteBatch(QueryText, TempManager = Undefined, Params = Неопределено) Экспорт
	
	If TempManager = Undefined Then
		TempManager = New TempTablesManager;
	EndIf;
	
	// Создаём Query с TempTablesManager
	Запрос = М1сAIЗапросы.CreateQ(QueryText, TempManager);
	// Устанавливаем параметры, если переданы
	Если Params <> Неопределено Тогда
		М1сAIЗапросы.SetQParams(Запрос, Params);
	КонецЕсли;
	// Выполняем пакет и возвращаем массив выборок
	Возврат Запрос.ВыполнитьПакет();
КонецФункции
#EndRegion

#Region М1сAIЗапросы_UnloadBatch
/// <summary>Выполняет пакет запросов и выгружает каждый результат в таблицу значений.</summary>
/// <param name="QueryText" type="String">Текст пакетного запроса.</param>
/// <param name="TempManager" type="TempTablesManager">Менеджер временных таблиц.</param>
/// <param name="Params" type="Structure" optional="True">Структура параметров.</param>
/// <returns type="Array">Массив ValueTable.</returns>
Функция UnloadBatch(QueryText, TempManager = Undefined, Params = Неопределено) Экспорт
	// Сначала получаем массив выборок через ExecuteBatch
	BatchResult = М1сAIЗапросы.ExecuteBatch(QueryText, TempManager, Params);
	// Выгружаем каждую выборку в ValueTable
	ValueTables = Новый Массив;
	Для Каждого Sel Из BatchResult Цикл
		If ЗначениеЗаполнено(Sel) Then
			ValueTables.Add(Sel.Выгрузить());
		EndIf;	
	КонецЦикла;
	Возврат ValueTables;
КонецФункции
#EndRegion


// ---------------------------- EOF М1сAIЗапросы ---------------------------------
