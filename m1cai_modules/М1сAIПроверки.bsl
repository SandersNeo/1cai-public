// [NEXUS IDENTITY] ID: 8665404960063247719 | DATE: 2025-11-19

﻿// Модуль: М1сAIПроверки
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region BasicChecks
// Basic type checking functions
Функция IsNumber(Value) Экспорт
	Возврат TypeOf(Value) = Type("Number");
КонецФункции

Функция IsString(Value) Экспорт
	Возврат TypeOf(Value) = Type("String");
КонецФункции

Функция IsDate(Value) Экспорт
	Возврат TypeOf(Value) = Type("Date");
КонецФункции

Функция IsBoolean(Value) Экспорт
	Возврат TypeOf(Value) = Type("Boolean");
КонецФункции

Функция IsUndefined(Value) Экспорт
	Возврат Value = Undefined;
КонецФункции

Функция IsNull(Value) Экспорт
	Возврат Value = Null;
КонецФункции

Функция IsType(Value, ValueType) Экспорт
	Возврат TypeOf(Value) = Type(ValueType);
КонецФункции

Функция IsOneOfType(Value, TypeList) Экспорт
	Для Каждого T Из TypeList Цикл
		Если TypeOf(Value) = Type(T) Тогда
			Возврат True;
		КонецЕсли;
	КонецЦикла;
	Возврат False;
КонецФункции

// Enhanced type checking with support for complex scenarios
Функция IsComplexType(Value, TypePattern) Экспорт
	// Support patterns like "String|Number", "Ref.*", etc.
	
	Если Find(TypePattern, "|") > 0 Тогда
		// Multiple types separated by |
		TypeOptions = StrSplit(TypePattern, "|", False);
		Для Каждого TypeOption Из TypeOptions Цикл
			Если IsType(Value, TrimAll(TypeOption)) Тогда
				Возврат True;
			КонецЕсли;
		КонецЦикла;
		Возврат False;
	КонецЕсли;
	
	Если Find(TypePattern, "*") > 0 Тогда
		// Wildcard matching
		Возврат MatchesTypePattern(TypeOf(Value).Name, TypePattern);
	КонецЕсли;
	
	Возврат IsType(Value, TypePattern);
КонецФункции

Функция MatchesTypePattern(TypeName, Pattern) Экспорт
	// Simple wildcard matching for type patterns
	Если Pattern = "*" Тогда
		Возврат True;
	КонецЕсли;
	
	Если Right(Pattern, 1) = "*" Тогда
		Prefix = Left(Pattern, StrLen(Pattern) - 1);
		Возврат Left(TypeName, StrLen(Prefix)) = Prefix;
	КонецЕсли;
	
	Если Left(Pattern, 1) = "*" Тогда
		Suffix = Right(Pattern, StrLen(Pattern) - 1);
		Возврат Right(TypeName, StrLen(Suffix)) = Suffix;
	КонецЕсли;
	
	Возврат TypeName = Pattern;
КонецФункции

// Utility function to validate 1C identifiers
Функция IsValidIdentifier(Name) Экспорт
	Если IsBlankString(Name) Тогда
		Возврат False;
	КонецЕсли;
	
	// Check if starts with letter or underscore
	FirstChar = Left(Name, 1);
	Если НЕ (М1сAIСимволы.IsLetter(FirstChar) ИЛИ FirstChar = "_") Тогда
		Возврат False;
	КонецЕсли;
	
	// Check remaining characters
	Для i = 2 По StrLen(Name) Цикл
		Char = Mid(Name, i, 1);
		Если НЕ (М1сAIСимволы.IsLetter(Char) ИЛИ М1сAIСимволы.IsDigit(Char) ИЛИ Char = "_") Тогда
			Возврат False;
		КонецЕсли;
	КонецЦикла;
	
	Возврат True;
КонецФункции

// GUID/UUID specific checks
Функция IsGUID(Value) Экспорт
	Если НЕ IsString(Value) Тогда
		Возврат False;
	КонецЕсли;
	
	// Basic GUID format check: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
	Если StrLen(Value) <> 36 Тогда
		Возврат False;
	КонецЕсли;
	
	// Check for hyphens in correct positions
	Если Mid(Value, 9, 1) <> "-" ИЛИ Mid(Value, 14, 1) <> "-" ИЛИ
		Mid(Value, 19, 1) <> "-" ИЛИ Mid(Value, 24, 1) <> "-" Тогда
		Возврат False;
	КонецЕсли;
	
	// Check that other characters are hex digits
	CheckPositions = "12345678ABCDEFGHIJKLMNOPQRSTUVWXYZ"; // Positions without hyphens
	Для i = 1 По StrLen(CheckPositions) Цикл
		Pos = Find(CheckPositions, Mid(CheckPositions, i, 1));
		Если Pos = 9 ИЛИ Pos = 14 ИЛИ Pos = 19 ИЛИ Pos = 24 Тогда
			Продолжить; // Skip hyphen positions
		КонецЕсли;
		
		Char = Upper(Mid(Value, Pos, 1));
		Если Find("0123456789ABCDEF", Char) = 0 Тогда
			Возврат False;
		КонецЕсли;
	КонецЦикла;
	
	Возврат True;
КонецФункции

// Reference type checks
Функция IsReference(Value) Экспорт
	Попытка
		Возврат TypeOf(Value).Name.EndsWith("Ref");
	Исключение
		Возврат False;
	КонецПопытки;
КонецФункции

Функция IsCatalogRef(Value) Экспорт
	Попытка
		Возврат Left(TypeOf(Value).Name, 10) = "CatalogRef";
	Исключение
		Возврат False;
	КонецПопытки;
КонецФункции

Функция IsDocumentRef(Value) Экспорт
	Попытка
		Возврат Left(TypeOf(Value).Name, 11) = "DocumentRef";
	Исключение
		Возврат False;
	КонецПопытки;
КонецФункции

// Batch validation
Функция ValidateStructureTypes(Structure, TypeMap) Экспорт
	Errors = Новый Array;
	
	Для Каждого Item Из Structure Цикл
		FieldName = Item.Key;
		FieldValue = Item.Value;
		
		Если TypeMap.Property(FieldName) Тогда
			ExpectedType = TypeMap[FieldName];
			Если НЕ ValueMatchesType(FieldValue, ExpectedType) Тогда
				Errors.Add(StrTemplate("Field '%1' has incorrect type. Expected: %2, Actual: %3",
						FieldName, ExpectedType, TypeOf(FieldValue)));
			КонецЕсли;
		КонецЕсли;
	КонецЦикла;
	
	Возврат Errors;
КонецФункции

Функция ValueMatchesType(Value, TypeDescription) Экспорт
	Попытка
		// Attempt to check if value matches type description
		ValueType = TypeOf(Value);
		AllowedTypes = TypeDescription.Types();
		
		Для Каждого AllowedType Из AllowedTypes Цикл
			Если ValueType = AllowedType Тогда
				Возврат True;
			КонецЕсли;
		КонецЦикла;
		
		Возврат False;
	Исключение
		Возврат False;
	КонецПопытки;
КонецФункции

#Region BasicExamples

// Example 1: Simple usage with cached GetTypesMap
//Table = М1сAITypes.BuildTable("ID,TDGUID;Name,TDStr150;Amount,TDNum15_2");

// Example 2: Type checking with М1сAIПроверки
//If М1сAIПроверки.IsGUID(SomeValue) Then
//    // Handle GUID
//ElsIf М1сAIПроверки.IsString(SomeValue) Then
//    // Handle string
//EndIf;

// Example 3: Complex type validation
//If М1сAIПроверки.IsComplexType(Value, "String|Number") Then
//    // Handle string or number
//EndIf;

//If М1сAIПроверки.IsComplexType(RefValue, "Ref*") Then
//    // Handle any reference type
//EndIf;

// Example 4: Structure validation
//Errors = М1сAIПроверки.ValidateStructureTypes(MyStructure, ExpectedTypes);
//If Errors.Count() > 0 Then
//    For Each Error In Errors Do
//        Message(Error);
//    EndDo;
//EndIf;

// Example 5: Advanced identifier validation
//If М1сAIПроверки.IsValidIdentifier("MyField123") Then
//    // Valid 1C identifier
//EndIf;

#EndRegion

#EndRegion

#Region ValueChecks

Функция Empty(Value, Log = False) Экспорт
	Если Log Тогда
		Попытка
			М1сAIEventLog.WriteInformation("Empty function called with parameter: " + Value);
		Исключение
			// Handle exception if necessary
		КонецПопытки;
	КонецЕсли;
	Если Value = Undefined ИЛИ Value = "" Тогда
		Возврат True
	Иначе
		Возврат False
	КонецЕсли;
КонецФункции

Функция NotEmpty(Value, Log = False) Экспорт
	Если Log Тогда
		Попытка
			М1сAIEventLog.WriteInformation("NotEmpty function called with parameter: " + Value);
		Исключение
			// Handle exception if necessary
		КонецПопытки;
	КонецЕсли;
	Возврат НЕ Empty(Value);
КонецФункции

Функция Blank(Value, Log = False) Экспорт
	Если Log Тогда
		Попытка
			М1сAIЛогирование.Info("Blank function called with parameter: " + Value);
		Исключение
			// Handle exception if necessary
		КонецПопытки;
	КонецЕсли;
	Если Empty(Value) ИЛИ TrimAll(Value) = "" Тогда
		Возврат True;
	Иначе
		Возврат False;
	КонецЕсли;
КонецФункции

Функция Present(Value, Log = False) Экспорт
	Если Log Тогда
		Попытка
			М1сAIЛогирование.Info("Present function called with parameter: " + Value);
		Исключение
			// Handle exception if necessary
		КонецПопытки;
	КонецЕсли;
	Возврат НЕ Blank(Value);
КонецФункции

Функция Nil(Value, Log = False) Экспорт
	Если Log Тогда
		Попытка
			М1сAIЛогирование.Info("Nil function called with parameter: " + Value);
		Исключение
			// Handle exception if necessary
		КонецПопытки;
	КонецЕсли;
	Если Value = Undefined Тогда
		Возврат True;
	Иначе
		Возврат False;
	КонецЕсли;
КонецФункции

// Safe Assigning
Процедура Assign(Знач Object, DefaultValue, Message = "") Экспорт
	Если НЕ ValueIsFilled(Object) Тогда
		Object = DefaultValue;
		Если Message <> "" Тогда
			Message(Message);
		КонецЕсли;
	КонецЕсли;
КонецПроцедуры

#EndRegion

// NUMBERS

//see: https://1c-dn.com/forum/forum12/topic111/
Функция IsInRange(Value, Min, Max) Экспорт
	Если Value >= Min И Value <= Max Тогда
		Возврат True;
	Иначе
		Возврат False;
	КонецЕсли;
КонецФункции

Функция GetAbs(Number) Экспорт
	Возврат Max(-1 * Number, Number);
КонецФункции

Функция IsAboutZero(Value, Threshold = 0.01) Экспорт
	Если Value = 0 Тогда
		Возврат False;
	ИначеЕсли GetAbs(Value) < Threshold Тогда
		Возврат True;
	Иначе
		Возврат False;
	КонецЕсли;
КонецФункции

Функция CreateAllowedTypesMap() Экспорт
	AllowedTypes = Новый Map;
	AllowedTypes.Insert(Type("String"), True);
	AllowedTypes.Insert(Type("Number"), True);
	AllowedTypes.Insert(Type("Date"), True);
	AllowedTypes.Insert(Type("Boolean"), True);
	// Add other types as needed
	Возврат AllowedTypes;
КонецФункции

Процедура CheckValueTable(ValueTable) Экспорт
	AllowedTypes = CreateAllowedTypesMap();
	
	Для Каждого Row Из ValueTable Цикл
		Для Каждого Column Из ValueTable.Columns Цикл
			Value = Row[Column.Name];
			Если AllowedTypes.Get(TypeOf(Value)) = Undefined Тогда
				Message("The value table contains a value of type " + TypeOf(Value) + " which cannot be passed from the server to the client.");
				Возврат;
			КонецЕсли;
		КонецЦикла;
	КонецЦикла;
	
	Message("The value table contains only values of types that can be passed from the server to the client.");
КонецПроцедуры

//-------------------------------------------------------------------
// TYPE CHECKING IsType...
//-------------------------------------------------------------------

Функция IsTypeOf(Variable, Types) Экспорт
	
	TypeArray = Новый Array();
	
	Если М1сAIПроверки.IsString(Types) Тогда
		TypeArray = StrSplit(Types, ","); // Предполагается, что типы разделены запятыми
		Для i = 0 По TypeArray.Count() - 1 Цикл
			TypeArray[i] = TrimAll(TypeArray[i]);
		КонецЦикла
	ИначеЕсли
		// value list
		М1сAIПроверки.IsValueList(Types) Тогда
		Для Каждого el Из Types Цикл
			TypeArray.Add(el);
		КонецЦикла;
		
	Иначе
		/// array
		Если М1сAIПроверки.IsArray(Types) Тогда
			TypeArray = Types;
		КонецЕсли;
	КонецЕсли;
	
	Для Каждого Type Из TypeArray Цикл
		Если TypeOf(Variable) = Type(TrimAll(Type)) Тогда
			Возврат True;
		КонецЕсли;
	КонецЦикла;
	
	Возврат False;
	
КонецФункции

Функция IsBasicType(Variable) Экспорт
	Возврат IsTypeOf(Variable, "String, Date, Number, Boolean");
КонецФункции

Функция IsArray(Variable) Экспорт
	Возврат IsTypeOf(Variable, "Array");
КонецФункции

Функция IsMap(Variable) Экспорт
	Возврат IsTypeOf(Variable, "Map");
КонецФункции

Функция IsStructure(Variable) Экспорт
	Возврат IsTypeOf(Variable, "Structure");
КонецФункции

Функция IsValueList(Variable) Экспорт
	Возврат IsTypeOf(Variable, "ValueList");
КонецФункции

Функция IsValueTable(Variable) Экспорт
	Возврат IsTypeOf(Variable, "ValueTable");
КонецФункции

Функция IsFixedString(Variable) Экспорт
	Возврат IsTypeOf(Variable, "FixedString");
КонецФункции

Функция IsFixedArray(Variable) Экспорт
	Возврат IsTypeOf(Variable, "FixedArray");
КонецФункции

Функция IsFileStream(Variable) Экспорт
	Возврат IsTypeOf(Variable, "FileStream");
КонецФункции

Функция IsUUID(Variable) Экспорт
	Возврат IsTypeOf(Variable, "UUID");
КонецФункции

Функция IsMemoryStream(Variable) Экспорт
	Возврат IsTypeOf(Variable, "MemoryStream");
КонецФункции

Функция IsKeyAndValue(Variable) Экспорт
	Возврат IsTypeOf(Variable, "KeyAndValue");
КонецФункции

Функция IsFixedStructure(Variable) Экспорт
	Возврат IsTypeOf(Variable, "FixedStructure");
КонецФункции

Функция IsBinaryData(Variable) Экспорт
	Возврат IsTypeOf(Variable, "BinaryData");
КонецФункции

Функция IsErrorInfo(Variable) Экспорт
	Возврат IsTypeOf(Variable, "ErrorInfo");
КонецФункции

Функция IsXDTOObject(Variable) Экспорт
	Возврат IsTypeOf(Variable, "XDTOObject");
КонецФункции

Функция IsFixedMap(Variable) Экспорт
	Возврат IsTypeOf(Variable, "FixedMap");
КонецФункции

Функция IsDocumentObj(Variable, DocName) Экспорт
	Возврат IsTypeOf(Variable, "DocumentObject." + DocName);
КонецФункции

Функция IsEnumRef(Variable, EnumName) Экспорт
	Возврат IsTypeOf(Variable, "EnumRef." + EnumName);
КонецФункции

Функция IsCatalogObj(Variable, CatalogName) Экспорт
	Возврат IsTypeOf(Variable, "CatalogObject." + CatalogName);
КонецФункции
