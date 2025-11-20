// [NEXUS IDENTITY] ID: 3628642438753530926 | DATE: 2025-11-19

﻿// Модуль: М1сAIСимволы
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region М1сAIСимволы_ModuleMap 
// М1сAIСимволы – Модуль работы с символами в библиотеке A1s
// Flags    : Server + External connection + Client
// Requires : -
//
// Regions:
//   CharacterSets       – Наборы символов (латиница, кириллица, цифры, hex)
//   CharacterArrays     – Те же наборы, но в виде массивов
//   Checks              – Проверки символов (буква, цифра, hex, и пр.)
//   Service             – Служебные утилиты (повтор строки и т.п.)
//   М1сAIСимволы_Dividers   – Разделители и визуальное оформление
//   Symbols             – Генераторы специальных символов (пробелы, табуляции)
//   Chars               – Работа с отдельными символами (GetChar и др.)
//   Transformations     – Обработка текста, парсинг, трансформация, маскирование
//   SelfTest            – Самотест модуля
#EndRegion

#Region CharacterSets

#Region М1сAIСимволы_LatinLetters
/// <summary>Возвращает строку латинских букв. При True включает строчные буквы.</summary>
/// <param name="IncludeLower" type="Boolean" default="Истина">Включить строчные</param>
/// <returns type="String">Латинский алфавит</returns>
Function LatinLetters(IncludeLower = Истина) Export
    If IncludeLower Then
        Return "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    Else
        Return "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    EndIf;
EndFunction

#Region examples_М1сAIСимволы_LatinLetters
// Example: М1сAIСимволы.LatinLetters() // "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
#EndRegion
#EndRegion

#Region М1сAIСимволы_CyrillicLetters
/// <summary>Возвращает строку кириллических букв. При True включает строчные буквы.</summary>
/// <param name="IncludeLower" type="Boolean" default="Истина">Включить строчные</param>
/// <returns type="String">Кириллический алфавит</returns>
Function CyrillicLetters(IncludeLower = Истина) Export
    If IncludeLower Then
        Return "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя";
    Else
        Return "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ";
    EndIf;
EndFunction

#Region examples_М1сAIСимволы_CyrillicLetters
// Example: М1сAIСимволы.CyrillicLetters() // "АБВГ...я"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Digits
/// <summary>Возвращает строку цифр 0-9.</summary>
/// <returns type="String">0123456789</returns>
Function Digits() Export
	Возврат "0123456789";
EndFunction

#Region examples_М1сAIСимволы_Digits
// Example: М1сAIСимволы.Digits() // "0123456789"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Hex
/// <summary>Возвращает строку шестнадцатеричных символов.</summary>
/// <returns type="String">0123456789ABCDEFabcdef</returns>
Function Hex() Export
	Возврат "0123456789ABCDEFabcdef";
EndFunction

#Region examples_М1сAIСимволы_Hex
// Example: М1сAIСимволы.Hex() // "0123456789ABCDEFabcdef"
#EndRegion
#EndRegion

#EndRegion

#Region CharacterArrays

#Region М1сAIСимволы_DigitsArray
/// <summary>Возвращает массив цифр как строк.</summary>
/// <returns type="Array">["0", "1", ..., "9"]</returns>
Function DigitsArray() Export
	Return StrSplit(Digits(), "");
EndFunction

#Region examples_М1сAIСимволы_DigitsArray
// Example: Result = М1сAIСимволы.DigitsArray(); // => ["0", "1", ..., "9"]
#EndRegion
#EndRegion

#Region М1сAIСимволы_HexArray
/// <summary>Возвращает массив шестнадцатеричных символов как строк.</summary>
/// <returns type="Array">["0", ..., "9", "A", ..., "F", "a", ..., "f"]</returns>
Function HexArray() Export
	Return StrSplit(Hex(), "");
EndFunction

#Region examples_М1сAIСимволы_HexArray
// Example: Result = М1сAIСимволы.HexArray();
// => ["0", ..., "9", "A", ..., "F", "a", ..., "f"]
#EndRegion
#EndRegion

#Region М1сAIСимволы_LatinLettersArray
/// <summary>Возвращает массив латинских букв.</summary>
/// <param name="IncludeLower" type="Boolean" default="True">Включить строчные</param>
/// <returns type="Array">["A", ..., "Z", "a", ..., "z"]</returns>
Function LatinLettersArray(IncludeLower = True) Export
	Return StrSplit(LatinLetters(IncludeLower), "");
EndFunction

#Region examples_М1сAIСимволы_LatinLettersArray
// Example:
// Result = М1сAIСимволы.LatinLettersArray();
// => ["A", ..., "Z", "a", ..., "z"]
#EndRegion
#EndRegion

#Region М1сAIСимволы_CyrillicLettersArray
/// <summary>Возвращает массив кириллических букв.</summary>
/// <param name="IncludeLower" type="Boolean" default="True">Включить строчные</param>
/// <returns type="Array">["А", ..., "Я", "а", ..., "я"]</returns>
Function CyrillicLettersArray(IncludeLower = True) Export
	Return StrSplit(CyrillicLetters(IncludeLower), "");
EndFunction

#Region examples_М1сAIСимволы_CyrillicLettersArray
// Example:
// Result = М1сAIСимволы.CyrillicLettersArray();
// => ["А", ..., "Я", "а", ..., "я"]
#EndRegion
#EndRegion

#EndRegion


#region Checks

#Region М1сAIСимволы_IsLatinLetter
/// <summary>Проверяет, является ли символ латинской буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если латинская</returns>
Function IsLatinLetter(Char) Export
    Return IsUpperLatin(Char) Or IsLowerLatin(Char);
EndFunction

#Region examples_М1сAIСимволы_IsLatinLetter
// Example: М1сAIСимволы.IsLatinLetter("A") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsCyrillicLetter
/// <summary>Проверяет, является ли символ кириллической буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если кириллическая</returns>
Function IsCyrillicLetter(Char) Export
    Return IsUpperCyrillic(Char) Or IsLowerCyrillic(Char);
EndFunction

#Region examples_М1сAIСимволы_IsCyrillicLetter
// Example: М1сAIСимволы.IsCyrillicLetter("Б") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsDigit
/// <summary>Проверяет, является ли символ цифрой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если цифра (0–9)</returns>
Function IsDigit(Char) Export
    Return (Char >= "0") And (Char <= "9");
EndFunction

#Region examples_М1сAIСимволы_IsDigit
// Example: М1сAIСимволы.IsDigit("3") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsUpperLatin
/// <summary>Проверяет, является ли символ заглавной латинской буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если A-Z</returns>
Function IsUpperLatin(Char) Export
    Return (Char >= "A" And Char <= "Z");
EndFunction

#Region examples_М1сAIСимволы_IsUpperLatin
// Example: М1сAIСимволы.IsUpperLatin("G") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsLowerLatin
/// <summary>Проверяет, является ли символ строчной латинской буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если a-z</returns>
Function IsLowerLatin(Char) Export
    Return (Char >= "a" And Char <= "z");
EndFunction

#Region examples_М1сAIСимволы_IsLowerLatin
// Example: М1сAIСимволы.IsLowerLatin("q") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsUpperCyrillic
/// <summary>Проверяет, является ли символ заглавной кириллической буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если А-Я или Ѐ-Џ</returns>
Function IsUpperCyrillic(Char) Export
    Return (Char >= "А" And Char <= "Я") Or (Char >= "Ѐ" And Char <= "Џ");
EndFunction

#Region examples_М1сAIСимволы_IsUpperCyrillic
// Example: М1сAIСимволы.IsUpperCyrillic("Ж") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsLowerCyrillic
/// <summary>Проверяет, является ли символ строчной кириллической буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если а-я или ѐ-џ</returns>
Function IsLowerCyrillic(Char) Export
    Return (Char >= "а" And Char <= "я") Or (Char >= "ѐ" And Char <= "џ");
EndFunction

#Region examples_М1сAIСимволы_IsLowerCyrillic
// Example: М1сAIСимволы.IsLowerCyrillic("ю") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsUpperRussian
/// <summary>Проверяет, является ли символ заглавной русской буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если А-Я</returns>
Function IsUpperRussian(Char) Export
    Return (Char >= "А" And Char <= "Я");
EndFunction

#Region examples_М1сAIСимволы_IsUpperRussian
// Example: М1сAIСимволы.IsUpperRussian("Ф") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsLowerRussian
/// <summary>Проверяет, является ли символ строчной русской буквой.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если а-я</returns>
Function IsLowerRussian(Char) Export
    Return (Char >= "а" And Char <= "я");
EndFunction

#Region examples_М1сAIСимволы_IsLowerRussian
// Example: М1сAIСимволы.IsLowerRussian("я") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsLatinAlpha
/// <summary>Проверяет, является ли символ латинской буквой (строчной или заглавной).</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если латинская</returns>
Function IsLatinAlpha(Char) Export
    Return IsUpperLatin(Char) Or IsLowerLatin(Char);
EndFunction

#Region examples_М1сAIСимволы_IsLatinAlpha
// Example: М1сAIСимволы.IsLatinAlpha("b") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsCyrillicAlpha
/// <summary>Проверяет, является ли символ кириллической буквой (строчной или заглавной).</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если кириллическая</returns>
Function IsCyrillicAlpha(Char) Export
    Return IsUpperCyrillic(Char) Or IsLowerCyrillic(Char);
EndFunction

#Region examples_М1сAIСимволы_IsCyrillicAlpha
// Example: М1сAIСимволы.IsCyrillicAlpha("Я") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsRussianAlpha
/// <summary>Проверяет, является ли символ русской буквой (А-Я, а-я).</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если русская буква</returns>
Function IsRussianAlpha(Char) Export
    Return IsUpperRussian(Char) Or IsLowerRussian(Char);
EndFunction

#Region examples_М1сAIСимволы_IsRussianAlpha
// Example: М1сAIСимволы.IsRussianAlpha("ж") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsAlpha
/// <summary>Проверяет, является ли символ буквой (латиница или кириллица).</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если буква</returns>
Function IsAlpha(Char) Export
    Return IsLatinAlpha(Char) Or IsCyrillicAlpha(Char);
EndFunction

#Region examples_М1сAIСимволы_IsAlpha
// Example: М1сAIСимволы.IsAlpha("Б") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsAlphaNum
/// <summary>Проверяет, является ли символ буквой, цифрой или подчёркиванием.</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если буква, цифра или "_"</returns>
Function IsAlphaNum(Char) Export
    Return IsAlpha(Char) Or IsDigit(Char) Or (Char = "_");
EndFunction

#Region examples_М1сAIСимволы_IsAlphaNum
// Example: М1сAIСимволы.IsAlphaNum("_") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsHex
/// <summary>Проверяет, является ли символ шестнадцатеричным (0-9, A-F, a-f).</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если hex-цифра</returns>
Function IsHex(Char) Export
    Return (Char >= "0" And Char <= "9") Or (Char >= "A" And Char <= "F") Or (Char >= "a" And Char <= "f");
EndFunction

#Region examples_М1сAIСимволы_IsHex
// Example: М1сAIСимволы.IsHex("F") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_IsBinary
/// <summary>Проверяет, является ли символ двоичной цифрой (0 или 1).</summary>
/// <param name="Char" type="String">Символ</param>
/// <returns type="Boolean">Истина, если "0" или "1"</returns>
Function IsBinary(Char) Export
    Return (Char = "0") Or (Char = "1");
EndFunction

#Region examples_М1сAIСимволы_IsBinary
// Example: М1сAIСимволы.IsBinary("1") // Истина
#EndRegion
#EndRegion

#EndRegion

#Область СлужебныеФункции

#Region М1сAIСимволы_Repeat
/// <summary>Повторяет строку N раз.</summary>
/// <param name="Строка" type="String">Что повторить</param>
/// <param name="Количество" type="Number">Сколько раз</param>
/// <returns type="String">Повторённая строка</returns>
Function Repeat(Знач Строка, Знач Количество) Export
    
    Если Количество <= 0 Тогда
        Возврат "";
    КонецЕсли;
    
    Результат = "";
    Для Счетчик = 1 По Количество Цикл
        Результат = Результат + Строка;
    КонецЦикла;
    
    Возврат Результат;
    
EndFunction

#Region examples_М1сAIСимволы_Repeat
// Example: М1сAIСимволы.Repeat("-", 5) // "-----"
#EndRegion
#EndRegion

#КонецОбласти

#Region М1сAIСимволы_Divider
/// <summary>Возвращает строку-разделитель из заданного символа и длины.</summary>
/// <param name="Len" type="Number" default="32">Длина строки</param>
/// <param name="Symbol" type="String" default="-">Символ-разделитель</param>
/// <returns type="String">Строка из повторяющегося символа</returns>
Function Divider(Len = 32, Symbol = "-") Export
	// Используем уже существующую Repeat
	Return Repeat(Symbol, Len);
EndFunction

#Region examples_М1сAIСимволы_Divider
// Example: М1сAIСимволы.Divider(10, "=") // "=========="
#EndRegion
#EndRegion

#Region М1сAIСимволы_DividerText
/// <summary>Формирует разделитель с центрированным текстом.</summary>
/// <param name="Text" type="String">Вставляемый текст</param>
/// <param name="Total" type="Number" default="50">Общая длина строки</param>
/// <param name="Symbol" type="String" default="-">Символ-разделитель</param>
/// <returns type="String">Строка с текстом по центру</returns>
Function DividerText(Text, Total = 50, Symbol = "-") Export
	// Центрируем текст по ширине Total
	Local = StrLen(Text);
	LeftPart = Цел((Total - Local) / 2);
	If LeftPart < 0 Then LeftPart = 0; EndIf;

	Return Divider(LeftPart, Symbol)
	     + Text
	     + Divider(Total - LeftPart - Local, Symbol);
EndFunction

#Region examples_М1сAIСимволы_DividerText
// Example: М1сAIСимволы.DividerText(" HELLO ", 20, "*") // "****** HELLO *******"
#EndRegion
#EndRegion

#Region Symbols

#Region М1сAIСимволы_LineBreak
/// <summary>Возвращает строку из N переводов строки (по умолчанию 1).</summary>
/// <param name="N" type="Number" default="1">Количество переводов строки</param>
/// <returns type="String">Строка с переводами строки</returns>
Function LineBreak(N = 1) Export
    Возврат Repeat(Символы.ПС, Макс(N, 0)); 
EndFunction

#Region examples_М1сAIСимволы_LineBreak
// Example: М1сAIСимволы.LineBreak(2) // "\n\n"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Tab
/// <summary>Возвращает строку из N символов табуляции.</summary>
/// <param name="N" type="Number" default="1">Количество табуляций</param>
/// <returns type="String">Строка табуляций</returns>
Function Tab(N = 1) Export
    Возврат Repeat(Символы.Таб, Макс(N, 0)); 
EndFunction

#Region examples_М1сAIСимволы_Tab
// Example: М1сAIСимволы.Tab(3) // "\t\t\t"
#EndRegion
#EndRegion

#Region М1сAIСимволы_NonBreakingSpace
/// <summary>Возвращает строку из N неразрывных пробелов.</summary>
/// <param name="N" type="Number" default="1">Количество неразрывных пробелов</param>
/// <returns type="String">Строка с НПП</returns>
Function NonBreakingSpace(N = 1) Export
    Возврат Repeat(Символы.НПП, Макс(N, 0)); 
EndFunction

#Region examples_М1сAIСимволы_NonBreakingSpace
// Example: М1сAIСимволы.NonBreakingSpace(2) // "\u00A0\u00A0"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Space
/// <summary>Возвращает строку из N обычных пробелов.</summary>
/// <param name="N" type="Number" default="1">Количество пробелов</param>
/// <returns type="String">Строка пробелов</returns>
Function Space(N = 1) Export
    Возврат Repeat(" ", Макс(N, 0)); 
EndFunction

#Region examples_М1сAIСимволы_Space
// Example: М1сAIСимволы.Space(4) // "    "
#EndRegion
#EndRegion

#Region М1сAIСимволы_Dash
/// <summary>Возвращает строку из N дефисов.</summary>
/// <param name="N" type="Number" default="1">Количество дефисов</param>
/// <returns type="String">"-" повторённый N раз</returns>
Function Dash(N = 1) Export
    Возврат Repeat("-", Макс(N, 0)); 
EndFunction

#Region examples_М1сAIСимволы_Dash
// Example: М1сAIСимволы.Dash(5) // "-----"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Asterisk
/// <summary>Возвращает строку из N звёздочек.</summary>
/// <param name="N" type="Number" default="1">Количество звёздочек</param>
/// <returns type="String">"*" повторённый N раз</returns>
Function Asterisk(N = 1) Export
    Возврат Repeat("*", Макс(N, 0)); 
EndFunction

#Region examples_М1сAIСимволы_Asterisk
// Example: М1сAIСимволы.Asterisk(3) // "***"
#EndRegion
#EndRegion

#EndRegion
    
#Region Chars

#Region М1сAIСимволы_GetChar
/// <summary>Возвращает символ из строки по позиции.</summary>
/// <param name="Text" type="String">Строка</param>
/// <param name="Position" type="Number">Позиция (начиная с 1)</param>
/// <returns type="String">Один символ</returns>
Function GetChar(Text, Position) Export
    Return Mid(Text, Position, 1);
EndFunction

#Region examples_М1сAIСимволы_GetChar
// Example: М1сAIСимволы.GetChar("ABC", 2) // "B"
#EndRegion
#EndRegion

#Region М1сAIСимволы_RemoveUnwantedChars
/// <summary>Удаляет указанные символы из строки.</summary>
/// <param name="InputStr" type="String">Исходная строка</param>
/// <param name="UnwantedChars" type="String" default=" !@#$%^&*()_+-=[]{}|;:'\"\",.<>/?`~">Нежелательные символы</param>
/// <returns type="String">Очищенная строка</returns>
Function RemoveUnwantedChars(InputStr, UnwantedChars = " !@#$%^&*()_+-=[]{}|;:'\"",.<>/?`~") Export
    // Initialize cleaned string
    CleanStr = "";
    
    // Loop through each character in the input string
    For i = 1 To StrLen(InputStr) Do
        Char = Mid(InputStr, i, 1);
        If StrFind(UnwantedChars, Char) = 0 Then
            CleanStr = CleanStr + Char;
        EndIf;
    EndDo;
    
    // Return cleaned string
    Return CleanStr;
EndFunction

#Region examples_М1сAIСимволы_RemoveUnwantedChars
// Example: М1сAIСимволы.RemoveUnwantedChars("Name@123") // "Name123"
#EndRegion
#EndRegion

#EndRegion

#Region Transformations

#Region М1сAIСимволы_GetCharMap
/// <summary>Создаёт карту символов из строки (символ → Истина).</summary>
/// <param name="CharString" type="String">Исходная строка</param>
/// <returns type="Map">Карта символов</returns>
Function GetCharMap(CharString) Export
    CharMap = New Map();
    For i = 1 To StrLen(CharString) Do
        Char = Mid(CharString, i, 1);
        CharMap.Insert(Char, True);
    EndDo;
    Return CharMap;
EndFunction

#Region examples_М1сAIСимволы_GetCharMap
// Example: М1сAIСимволы.GetCharMap("abc") // {"a":Истина,"b":Истина,"c":Истина}
#EndRegion
#EndRegion

#Region М1сAIСимволы_FilterByCharMap
/// <summary>Фильтрует строку по карте разрешённых символов.</summary>
/// <param name="Str" type="String">Исходная строка</param>
/// <param name="AllowedMap" type="Map">Карта разрешённых символов</param>
/// <returns type="String">Строка, содержащая только допустимые символы</returns>
Function FilterByCharMap(Str, AllowedMap) Export
    Result = "";
    For i = 1 To StrLen(Str) Do
        Char = Mid(Str, i, 1);
	If AllowedMap[Char]<>Undefined Then
            Result = Result + Char;
        EndIf;
    EndDo;
    Return Result;
EndFunction

#Region examples_М1сAIСимволы_FilterByCharMap
// Пример:
// Allowed = М1сAIСимволы.GetCharMap("abc");
// Result = М1сAIСимволы.FilterByCharMap("abracadabra", Allowed); // => "abacaba"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Consonate
/// <summary>Возвращает строку, оставляя только согласные символы (кириллица, латиница, знаки).</summary>
/// <param name="Str" type="String">Исходная строка</param>
/// <returns type="String">Только согласные символы строки</returns>
Function Consonate(Str) Export
	// ib = "ФИЛЬТРАЦИЯ СТРОКИ ПО НАБОРУ СОГЛАСНЫХ СИМВОЛОВ";
	Try
		Allowed = "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ" 
		        + "бвгджзйклмнпрстфхцчшщБВГДЖЗЙКЛМНПРСТФХЦЧШЩ"
		        + ".,!?;:()[]{}<>\""'\\/-_+=*&^%$#@!~`| \t";

		AllowedMap = GetCharMap(Allowed); // МАПА ДОПУСТИМЫХ СИМВОЛОВ
		Result = FilterByCharMap(Str, AllowedMap); // ФИЛЬТРАЦИЯ СТРОКИ

		Return Result;
	Except
		М1сAIСтроки.Print("Ошибка в Consonate: " + ОписаниеОшибки());
		Return "";
	EndTry;
EndFunction

#Region examples_М1сAIСимволы_Consonate
// Example: М1сAIСимволы.Consonate("Привет, мир!") // "Првт, мр!"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Vowelate
/// <summary>Возвращает строку, оставляя только гласные символы (кириллица, латиница, знаки и пробелы).</summary>
/// <param name="Str" type="String">Исходная строка</param>
/// <returns type="String">Только гласные символы строки</returns>
Function Vowelate(Str) Export
	// ib = "ФИЛЬТРАЦИЯ СТРОКИ ПО НАБОРУ ГЛАСНЫХ СИМВОЛОВ";
	Try
		Allowed = "aeiouAEIOUаеёиоуыэюяАЕЁИОУЫЭЮЯ"
		        + ".,!?;:()[]{}<>\""'\\/-_+=*&^%$#@!~`| \t";

		AllowedMap = GetCharMap(Allowed); // МАПА ДОПУСТИМЫХ СИМВОЛОВ
		Result = FilterByCharMap(Str, AllowedMap); // ФИЛЬТРАЦИЯ СТРОКИ

		Return Result;
	Except
		М1сAIСтроки.Print("Ошибка в Vowelate: " + ОписаниеОшибки());
		Return "";
	EndTry;
EndFunction

#Region examples_М1сAIСимволы_Vowelate
// Example: М1сAIСимволы.Vowelate("Привет, мир!") // "ие, и!"
#EndRegion
#EndRegion

#Region М1сAIСимволы_SplitBy
/// <summary>Разбивает строку на слова по нескольким разделителям.</summary>
/// <param name="Str" type="String">Исходная строка</param>
/// <param name="Delimiters" type="String" default=" ">Разделители</param>
/// <returns type="Array">Массив слов</returns>
Function SplitBy(Str, Delimiters = " ") Export
    WordsArray = New Array();
    StartPos = 1;
    LengthStr = StrLen(Str);
    
    While StartPos <= LengthStr Do
        MinDelimPos = LengthStr + 1;
        For i = 1 To StrLen(Delimiters) Do
            Delim = Mid(Delimiters, i, 1);
            DelimPos = StrFind(Str, Delim, , StartPos);
            If DelimPos > 0 And DelimPos < MinDelimPos Then
                MinDelimPos = DelimPos;
            EndIf;
        EndDo;
        
        If MinDelimPos <= LengthStr Then
            Word = Mid(Str, StartPos, MinDelimPos - StartPos);
            If StrLen(Word) > 0 Then
                WordsArray.Add(Word);
            EndIf;
            StartPos = MinDelimPos + 1;
        Else
            Word = Mid(Str, StartPos);
            If StrLen(Word) > 0 Then
                WordsArray.Add(Word);
            EndIf;
            Break;
        EndIf;
    EndDo;
    
    Return WordsArray;
EndFunction

#Region examples_М1сAIСимволы_SplitBy
// Example: М1сAIСимволы.SplitBy("a,b;c", ",;") // ["a", "b", "c"]
#EndRegion
#EndRegion

#Region М1сAIСимволы_GetWordMap
/// <summary>Строит карту слов и количества их повторений.</summary>
/// <param name="Text" type="String">Входной текст</param>
/// <param name="Delimiters" type="String" default=" ">Разделители</param>
/// <returns type="Map">Карта слово → число</returns>
Function GetWordMap(Text, Delimiters = " ") Export
    WordsArray = SplitBy(Text, Delimiters);
    WordMap = New Map();

    For Each Word In WordsArray Do
	Current = WordMap[Word];
        If Current <> Неопределено Then
            WordMap[Word] = Current + 1;
        Else
            WordMap.Insert(Word, 1);
        EndIf;
    EndDo;

    Return WordMap;
EndFunction
#Region examples_М1сAIСимволы_GetWordMap
// Example: М1сAIСимволы.GetWordMap("a b a") // {a:2, b:1}
#EndRegion
#EndRegion

#Region М1сAIСимволы_Lorem
/// <summary>Генерирует псевдотекст на английском или русском языке.</summary>
/// <param name="N" type="Number" default="10">Количество слов</param>
/// <param name="Language" type="String" default="En">Язык ("En" или "Ru")</param>
/// <returns type="String">Сгенерированная строка</returns>
Function Lorem(N = 10, Language = "En") Export
    LatinWords = "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua Ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur Excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum";
    RussianWords = "Лорем ипсум долор сит амет консектетур адиписцинг элит сед до эиусмод темпор инцидидунт ут лаборе эт долоре магна аликва Ут эним ад миним веням квис ноструд эксерцитацион улламко лаборис ниси ут аликип экс эа коммодо консеквант Дуйс ауте ируре долор ин репрехендерит ин волуптате велит эссе циллум долоре еу фугиат нулла париатур Эксцептеур синт occaecat купидатат нон проидент сунт ин culpa qui officia deserunt моллит аним ид эст laborum";
    
    If Language = "En" Then
        WordsArray = SplitBy(LatinWords, " ");
    ElsIf Language = "Ru" Then
        WordsArray = SplitBy(RussianWords, " ");
    Else
        WordsArray = SplitBy(LatinWords, " ");
    EndIf;
    
    Result = "";   

	For i = 1 To N Do                                       
	    Result = Result + WordsArray[i] + " ";
	EndDo; 
	
	// maybe return Capitalized as sentence?

	Return TrimAll(Result);
EndFunction

#Region examples_М1сAIСимволы_Lorem
// Example: М1сAIСимволы.Lorem(5, "Ru") // "Лорем ипсум долор сит амет"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Translit
/// <summary>Выполняет транслитерацию строки с кириллицы на латиницу.</summary>
/// <param name="SourceString" type="String">Исходная строка</param>
/// <returns type="String">Транслитерированная строка</returns>
Function Translit(SourceString) Export
    Try
        TransliterationRules = New Map;
        TransliterationRules.Insert("А", "A");
        TransliterationRules.Insert("Б", "B");
        TransliterationRules.Insert("В", "V");
        TransliterationRules.Insert("Г", "G");
        TransliterationRules.Insert("Д", "D");
        TransliterationRules.Insert("Е", "E");
        TransliterationRules.Insert("Ё", "Yo");
        TransliterationRules.Insert("Ж", "Zh");
        TransliterationRules.Insert("З", "Z");
        TransliterationRules.Insert("И", "I");
        TransliterationRules.Insert("Й", "Y");
        TransliterationRules.Insert("К", "K");
        TransliterationRules.Insert("Л", "L");
        TransliterationRules.Insert("М", "M");
        TransliterationRules.Insert("Н", "N");
        TransliterationRules.Insert("О", "O");
        TransliterationRules.Insert("П", "P");
        TransliterationRules.Insert("Р", "R");
        TransliterationRules.Insert("С", "S");
        TransliterationRules.Insert("Т", "T");
        TransliterationRules.Insert("У", "U");
        TransliterationRules.Insert("Ф", "F");
        TransliterationRules.Insert("Х", "Kh");
        TransliterationRules.Insert("Ц", "Ts");
        TransliterationRules.Insert("Ч", "Ch");
        TransliterationRules.Insert("Ш", "Sh");
        TransliterationRules.Insert("Щ", "Shch");
        TransliterationRules.Insert("Ъ", "");
        TransliterationRules.Insert("Ы", "Y");
        TransliterationRules.Insert("Ь", "");
        TransliterationRules.Insert("Э", "E");
        TransliterationRules.Insert("Ю", "Yu");
        TransliterationRules.Insert("Я", "Ya");

	// FILL IN SMALL LETTERS
	For Each El in TransliterationRules Do
		TransliterationRules.Insert(НРег(El.Ключ), НРег(El.Значение));
	EndDo;	

        ResultString = "";
        For i = 1 To StrLen(SourceString) Do
            Character = Mid(SourceString, i, 1);
	    Translited = TransliterationRules[Character];
            If Translited <> Неопределено Then
                ResultString = ResultString + Translited;
            Else
                ResultString = ResultString + Character;
            EndIf;
        EndDo;

        Return ResultString;
    Except
        М1сAIСтроки.Print("Ошибка в Translit: " + ОписаниеОшибки());
        Return "";
    EndTry;
EndFunction

#Region examples_М1сAIСимволы_Translit
// Example: М1сAIСимволы.Translit("Юлия") // "Yuliya"
#EndRegion
#EndRegion

#Region М1сAIСимволы_Anonymize
/// <summary>Маскирует строку, оставляя заданное количество символов в начале и конце.</summary>
/// <param name="Str" type="String">Исходная строка</param>
/// <param name="KeepFirst" type="Number" default="0">Оставить в начале</param>
/// <param name="KeepLast" type="Number" default="0">Оставить в конце</param>
/// <returns type="String">Маскированная строка</returns>
Function Anonymize(Str, KeepFirst = 0, KeepLast = 0) Export
    Result = "";
    LengthStr = StrLen(Str);
    
    // Check for invalid parameters
    If KeepFirst + KeepLast > LengthStr Then
        Return "Error: KeepFirst and KeepLast exceed string length";
    EndIf;
    
    // Add the first N characters to the result
    If KeepFirst > 0 Then
        Result = Left(Str, KeepFirst);
    EndIf;
    
    // Add '*' for the middle characters
    For i = KeepFirst + 1 To LengthStr - KeepLast Do
        Result = Result + "*";
    EndDo;
    
    // Add the last N characters to the result
    If KeepLast > 0 Then
        Result = Result + Right(Str, KeepLast);
    EndIf;
    
    Return Result;
EndFunction

#Region examples_М1сAIСимволы_Anonymize
// Example: М1сAIСимволы.Anonymize("Shchetinkin", 2, 2) // "Sh********in"
#EndRegion
#EndRegion

#EndRegion

#Region М1сAIСимволы_StartsWithDigit
/// <summary>Проверяет, начинается ли строка с цифры.</summary>
/// <param name="String" type="String">Исходная строка</param>
/// <returns type="Boolean">Истина, если первый символ — цифра</returns>
Function StartsWithDigit(String) Export
    TrimmedString = TrimAll(String);
    If TrimmedString = "" Then
        Return False;
    EndIf;
    FirstChar = Mid(TrimmedString, 1, 1);
    Return IsDigit(FirstChar);
EndFunction

#Region examples_М1сAIСимволы_StartsWithDigit
// Example: М1сAIСимволы.StartsWithDigit(" 123abc") // Истина
#EndRegion
#EndRegion

#Region М1сAIСимволы_SelfTest
/// <summary>Тестирование основных функций М1сAIСимволы.</summary>
Function SelfTest() Export
	Тест = New Map;

	// LATIN
	Тест.Вставить("LatinLetters", LatinLetters(Ложь) = "ABCDEFGHIJKLMNOPQRSTUVWXYZ");
	Тест.Вставить("IsLatinLetter", IsLatinLetter("B") = Истина);

	// CYRILLIC
	Тест.Вставить("CyrillicLetters", СтрНайти(CyrillicLetters(), "Я") > 0);
	Тест.Вставить("IsCyrillicLetter", IsCyrillicLetter("Ё") = Истина);

	// DIGITS
	Тест.Вставить("Digits", Digits() = "0123456789");
	Тест.Вставить("IsDigit", IsDigit("7") = Истина);

	// SYMBOL GENERATORS
	Тест.Вставить("Dash", Dash(4) = "----");
	Тест.Вставить("LineBreak", LineBreak(2) = Символы.ПС + Символы.ПС);

	// TEXT UTILITIES
	Тест.Вставить("Anonymize", Anonymize("TestString", 2, 2) = "Te******ng");
	Тест.Вставить("StartsWithDigit", StartsWithDigit(" 7abc") = Истина);
	Тест.Вставить("RemoveUnwantedChars", RemoveUnwantedChars("A@B#C") = "ABC");
	Тест.Вставить("Consonate", Consonate("Привет!") = "Првт!");
	Тест.Вставить("Vowelate", Vowelate("Привет!") = "ие!");

	// SPLIT / MAP
	Тест.Вставить("SplitBy", ТипЗнч(SplitBy("a,b", ",")) = Тип("Массив"));
	Тест.Вставить("GetWordMap", GetWordMap("a b a").Получить("a") = 2);

	// TRANSFORMATION
	Тест.Вставить("Translit", Translit("Юлия") = "Yuliya");

	// ПЕЧАТЬ НЕУДАЧ
	ВсеОК = Истина;
	Для Каждого El Из Тест Цикл
		Если НЕ El.Значение Тогда
			М1сAIСтроки.Print("❌ FAIL: " + EL.Ключ);
			ВсеОК = Ложь;
		КонецЕсли;
	КонецЦикла;
	
	Если ВсеОК Тогда
		М1сAIСтроки.Print("✅ М1сAIСимволы: SelfTest passed");
	КонецЕсли;

	Возврат Тест;
EndFunction

#Region examples_М1сAIСимволы_SelfTest
// Example: Result = М1сAIСимволы.SelfTest();
// Если всё ОК, возвращает структуру с Истина по всем ключам
#EndRegion
#EndRegion




// ---------------------------- EOF М1сAIСимволы ---------------------------------
