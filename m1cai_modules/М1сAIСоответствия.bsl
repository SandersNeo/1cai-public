// [NEXUS IDENTITY] ID: 205667271840422786 | DATE: 2025-11-19

﻿// Модуль: М1сAIСоответствия
// Назначение: Библиотека модулей 1С AI Stack.
//
////////////////////////////////////////////////////////////////////////////////


#Region PublicInterface

// Создает новый объект Map
//
// Возвращаемое значение:
//   Map - новый пустой объект Map
//
Функция NewMap() Экспорт
	
	Возврат Новый Map;
	
КонецФункции

// Создает Map и заполняет его одним значением по всем ключам из строки
//
// Параметры:
//   KeysString - Строка - ключи через запятую
//   Value - Произвольный - значение для всех ключей
//
// Возвращаемое значение:
//   Map - заполненный объект Map
//
Функция NewFilled(KeysString, Value = Undefined) Экспорт
	
	Map = Новый Map;
	KeysArray = StrSplit(KeysString, ",", True);
	
	Для Каждого Key Из KeysArray Цикл
		Map.Insert(TrimAll(Key), Value);
	КонецЦикла;
	
	Возврат Map;
	
КонецФункции

// Создает Map из двух строк - ключей и значений
//
// Параметры:
//   KeysString - Строка - ключи через разделитель
//   ValuesString - Строка - значения через разделитель
//   Delimiter - Строка - разделитель (по умолчанию запятая)
//   FilterBy - Строка - фильтр по содержимому в ключе
//
// Возвращаемое значение:
//   Map - заполненный объект Map
//
Функция NewFromStrings(KeysString, ValuesString, Delimiter = ",", FilterBy = "") Экспорт
	
	Map = Новый Map;
	
	Если IsBlankString(KeysString) ИЛИ IsBlankString(ValuesString) Тогда
		Возврат Map;
	КонецЕсли;
	
	KeysArray = StrSplit(KeysString, Delimiter, True);
	ValuesArray = StrSplit(ValuesString, Delimiter, True);
	
	MaxIndex = Min(KeysArray.Count(), ValuesArray.Count()) - 1;
	
	Для Index = 0 По MaxIndex Цикл
		
		Key = TrimAll(KeysArray[Index]);
		Value = TrimAll(ValuesArray[Index]);
		
		Если IsBlankString(FilterBy) ИЛИ StrFind(Key, FilterBy) > 0 Тогда
			Map.Insert(Key, Value);
		КонецЕсли;
		
	КонецЦикла;
	
	Возврат Map;
	
КонецФункции

// Создает Map из массива ключей с одинаковым значением
//
// Параметры:
//   KeysArray - Массив - массив ключей
//   Value - Произвольный - значение для всех ключей
//
// Возвращаемое значение:
//   Map - заполненный объект Map
//
Функция NewFromArray(KeysArray, Value = Undefined) Экспорт
	
	Map = Новый Map;
	
	Для Каждого Key Из KeysArray Цикл
		Map.Insert(Key, Value);
	КонецЦикла;
	
	Возврат Map;
	
КонецФункции

// Создает копию существующего Map
//
// Параметры:
//   SourceMap - Map - исходный Map для копирования
//
// Возвращаемое значение:
//   Map - копия исходного Map
//
Функция Copy(SourceMap) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(SourceMap) Тогда
		Возврат Новый Map;
	КонецЕсли;
	
	NewMap = Новый Map;
	
	Для Каждого KeyValue Из SourceMap Цикл
		NewMap.Insert(KeyValue.Key, KeyValue.Value);
	КонецЦикла;
	
	Возврат NewMap;
	
КонецФункции

// Объединяет несколько Map в один
//
// Параметры:
//   Maps - Массив из Map - массив Map для объединения
//   OverwriteValues - Булево - перезаписывать существующие ключи (по умолчанию Истина)
//
// Возвращаемое значение:
//   Map - объединенный Map
//
Функция Merge(Maps, OverwriteValues = True) Экспорт
	
	ResultMap = Новый Map;
	
	Для Каждого MapItem Из Maps Цикл
		
		Если НЕ М1сAIПроверки.IsMap(MapItem) Тогда
			Продолжить;
		КонецЕсли;
		
		Для Каждого KeyValue Из MapItem Цикл
			
			Если OverwriteValues ИЛИ НЕ ResultMap.Get(KeyValue.Key) <> Undefined Тогда
				ResultMap.Insert(KeyValue.Key, KeyValue.Value);
			КонецЕсли;
			
		КонецЦикла;
		
	КонецЦикла;
	
	Возврат ResultMap;
	
КонецФункции

#EndRegion

#Region DataManipulation

// Вставляет значение в Map по ключу или создает новый Map
//
// Параметры:
//   Map - Map, Неопределено - Map для вставки (создается новый если Неопределено)
//   Key - Произвольный - ключ
//   Value - Произвольный - значение
//
// Возвращаемое значение:
//   Map - Map с добавленным значением
//
Функция Insert(Map, Key, Value) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Map = Новый Map;
	КонецЕсли;
	
	Map.Insert(Key, Value);
	
	Возврат Map;
	
КонецФункции

// Вставляет несколько значений в Map по ключам из строки
//
// Параметры:
//   Map - Map - Map для заполнения
//   KeysString - Строка - ключи через запятую
//   Value - Произвольный - значение для всех ключей
//
Функция InsertByKeys(Map, KeysString, Value) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Map = Новый Map;
	КонецЕсли;
	
	KeysArray = StrSplit(KeysString, ",", True);
	
	Для Каждого Key Из KeysArray Цикл
		Map.Insert(TrimAll(Key), Value);
	КонецЦикла;
	
	Возврат Map;
	
КонецФункции

// Удаляет элементы из Map по ключам из строки
//
// Параметры:
//   Map - Map - исходный Map
//   KeysString - Строка - ключи через запятую
//
Функция DeleteByKeys(Map, KeysString) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат Map;
	КонецЕсли;
	
	KeysArray = StrSplit(KeysString, ",", True);
	
	Для Каждого Key Из KeysArray Цикл
		Map.Delete(TrimAll(Key));
	КонецЦикла;
	
	Возврат Map;
	
КонецФункции

// Очищает Map от всех элементов
//
// Параметры:
//   Map - Map - Map для очистки
//
Функция Clear(Map) Экспорт
	
	Если М1сAIПроверки.IsMap(Map) Тогда
		Map.Clear();
	КонецЕсли;
	
	Возврат Map;
	
КонецФункции

#EndRegion

#Region DataRetrieval

// Получает значение из Map с возможностью указать значение по умолчанию
//
// Параметры:
//   Map - Map - исходный Map
//   Key - Произвольный - ключ для поиска
//   DefaultValue - Произвольный - значение по умолчанию
//
// Возвращаемое значение:
//   Произвольный - найденное значение или значение по умолчанию
//
Функция Get(Map, Key, DefaultValue = Undefined) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат DefaultValue;
	КонецЕсли;
	
	Value = Map.Get(Key);
	
	Если Value = Undefined Тогда
		Возврат DefaultValue;
	КонецЕсли;
	
	Возврат Value;
	
КонецФункции

// Получает все ключи Map в виде массива
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Массив - массив всех ключей
//
Функция Keys(Map) Экспорт
	
	KeysArray = Новый Array;
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат KeysArray;
	КонецЕсли;
	
	Для Каждого KeyValue Из Map Цикл
		KeysArray.Add(KeyValue.Key);
	КонецЦикла;
	
	Возврат KeysArray;
	
КонецФункции

// Получает все значения Map в виде массива
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Массив - массив всех значений
//
Функция Values(Map) Экспорт
	
	ValuesArray = Новый Array;
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат ValuesArray;
	КонецЕсли;
	
	Для Каждого KeyValue Из Map Цикл
		ValuesArray.Add(KeyValue.Value);
	КонецЦикла;
	
	Возврат ValuesArray;
	
КонецФункции

// Проверяет наличие ключа в Map
//
// Параметры:
//   Map - Map - исходный Map
//   Key - Произвольный - искомый ключ
//
// Возвращаемое значение:
//   Булево - Истина если ключ существует
//
Функция HasKey(Map, Key) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат False;
	КонецЕсли;
	
	Возврат Map.Get(Key) <> Undefined;
	
КонецФункции

// Получает количество элементов в Map
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Число - количество элементов
//
Функция Count(Map) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат 0;
	КонецЕсли;
	
	Возврат Map.Count();
	
КонецФункции

// Проверяет, пустой ли Map
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Булево - Истина если Map пустой
//
Функция IsEmpty(Map) Экспорт
	
	Возврат Count(Map) = 0;
	
КонецФункции

#EndRegion

#Region Filtering

// Фильтрует Map по ключам, содержащим указанную подстроку
//
// Параметры:
//   Map - Map - исходный Map
//   FilterText - Строка - текст для поиска в ключах
//   CaseSensitive - Булево - учитывать регистр (по умолчанию Ложь)
//
// Возвращаемое значение:
//   Map - отфильтрованный Map
//
Функция FilterByKeys(Map, FilterText, CaseSensitive = False) Экспорт
	
	FilteredMap = Новый Map;
	
	Если НЕ М1сAIПроверки.IsMap(Map) ИЛИ IsBlankString(FilterText) Тогда
		Возврат FilteredMap;
	КонецЕсли;
	
	SearchText = ?(CaseSensitive, FilterText, Upper(FilterText));
	
	Для Каждого KeyValue Из Map Цикл
		
		KeyText = ?(CaseSensitive, String(KeyValue.Key), Upper(String(KeyValue.Key)));
		
		Если StrFind(KeyText, SearchText) > 0 Тогда
			FilteredMap.Insert(KeyValue.Key, KeyValue.Value);
		КонецЕсли;
		
	КонецЦикла;
	
	Возврат FilteredMap;
	
КонецФункции

// Фильтрует Map по значениям, содержащим указанную подстроку
//
// Параметры:
//   Map - Map - исходный Map
//   FilterText - Строка - текст для поиска в значениях
//   CaseSensitive - Булево - учитывать регистр (по умолчанию Ложь)
//
// Возвращаемое значение:
//   Map - отфильтрованный Map
//
Функция FilterByValues(Map, FilterText, CaseSensitive = False) Экспорт
	
	FilteredMap = Новый Map;
	
	Если НЕ М1сAIПроверки.IsMap(Map) ИЛИ IsBlankString(FilterText) Тогда
		Возврат FilteredMap;
	КонецЕсли;
	
	SearchText = ?(CaseSensitive, FilterText, Upper(FilterText));
	
	Для Каждого KeyValue Из Map Цикл
		
		ValueText = ?(CaseSensitive, String(KeyValue.Value), Upper(String(KeyValue.Value)));
		
		Если StrFind(ValueText, SearchText) > 0 Тогда
			FilteredMap.Insert(KeyValue.Key, KeyValue.Value);
		КонецЕсли;
		
	КонецЦикла;
	
	Возврат FilteredMap;
	
КонецФункции

#EndRegion

#Region Conversion

// Преобразует Map в структуру
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Структура - структура с теми же ключами и значениями
//
Функция ToStructure(Map) Экспорт
	
	Structure = Новый Structure;
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат Structure;
	КонецЕсли;
	
	Для Каждого KeyValue Из Map Цикл
		
		Key = String(KeyValue.Key);
		// Заменяем недопустимые символы для имен свойств структуры
		Key = StrReplace(Key, " ", "_");
		Key = StrReplace(Key, "-", "_");
		Key = StrReplace(Key, ".", "_");
		
		Structure.Insert(Key, KeyValue.Value);
		
	КонецЦикла;
	
	Возврат Structure;
	
КонецФункции

// Преобразует структуру в Map
//
// Параметры:
//   Structure - Структура - исходная структура
//
// Возвращаемое значение:
//   Map - Map с теми же ключами и значениями
//
Функция FromStructure(Structure) Экспорт
	
	Map = Новый Map;
	
	Если TypeOf(Structure) <> Type("Structure") Тогда
		Возврат Map;
	КонецЕсли;
	
	Для Каждого KeyValue Из Structure Цикл
		Map.Insert(KeyValue.Key, KeyValue.Value);
	КонецЦикла;
	
	Возврат Map;
	
КонецФункции

// Преобразует Map в JSON строку
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Строка - JSON представление Map
//
Функция ToJSON(Map) Экспорт
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат "{}";
	КонецЕсли;
	
	Возврат М1сAIJSON.ToJSON(Map);
	
КонецФункции

// Преобразует Map в строку для отладки
//
// Параметры:
//   Map - Map - исходный Map
//   MapName - Строка - имя Map для вывода
//   FilterText - Строка - фильтр по ключам
//
// Возвращаемое значение:
//   Строка - текстовое представление Map
//
Функция ToString(Map, MapName = "Map", FilterText = "") Экспорт
	
	Result = "";
	
	Если НЕ М1сAIПроверки.IsMap(Map) Тогда
		Возврат MapName + " = Не Map или Неопределено" + Chars.CR;
	КонецЕсли;
	
	Если IsEmpty(Map) Тогда
		Возврат MapName + " = Пустой Map" + Chars.CR;
	КонецЕсли;
	
	Для Каждого KeyValue Из Map Цикл
		
		KeyString = String(KeyValue.Key);
		
		Если IsBlankString(FilterText) ИЛИ StrFind(KeyString, FilterText) > 0 Тогда
			Result = Result + MapName + "[" + KeyString + "] = " + String(KeyValue.Value) + Chars.CR;
		КонецЕсли;
		
	КонецЦикла;
	
	Возврат Result;
	
КонецФункции

#EndRegion

#Region Information

// Получает подробную информацию о Map
//
// Параметры:
//   Map - Map - исходный Map
//
// Возвращаемое значение:
//   Структура - структура с информацией о Map:
//     * View - Строка - строковое представление
//     * InternalView - Строка - внутреннее представление
//     * JSONView - Строка - JSON представление
//     * KeyCount - Число - количество ключей
//     * KeyList - Массив - список ключей
//     * IsEmpty - Булево - признак пустоты
//
Функция Info(Map) Экспорт
	
	MapInfo = Новый Structure;
	MapInfo.Insert("View", String(Map));
	MapInfo.Insert("InternalView", ValueToStringInternal(Map));
	MapInfo.Insert("JSONView", ToJSON(Map));
	MapInfo.Insert("KeyCount", Count(Map));
	MapInfo.Insert("KeyList", Keys(Map));
	MapInfo.Insert("IsEmpty", IsEmpty(Map));
	
	Возврат MapInfo;
	
КонецФункции

#EndRegion

#Region Examples

////////////////////////////////////////////////////////////////////////////////
// ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
////////////////////////////////////////////////////////////////////////////////

// Пример 1: Создание простого Map
// Map = М1сAIСоответствия.NewMap();
// М1сAIСоответствия.Insert(Map, "Ключ1", "Значение1");

// Пример 2: Создание Map с заполнением одинаковых значений
// StatusMap = М1сAIСоответствия.NewFilled("Новый,Обработан,Закрыт", "Активен");
// // Результат: ["Новый" = "Активен", "Обработан" = "Активен", "Закрыт" = "Активен"]

// Пример 3: Создание Map из строк
// NamesMap = М1сAIСоответствия.NewFromStrings("Иван,Петр,Сидор", "Иванов,Петров,Сидоров");
// // Результат: ["Иван" = "Иванов", "Петр" = "Петров", "Сидор" = "Сидоров"]

// Пример 4: Создание Map из массива с одним значением
// KeysArray = New Array;
// KeysArray.Add("Клиент1");
// KeysArray.Add("Клиент2");
// KeysArray.Add("Клиент3");
// ClientsMap = М1сAIСоответствия.NewFromArray(KeysArray, "VIP");

// Пример 5: Работа с получением значений
// Value = М1сAIСоответствия.GetValue(Map, "Ключ1", "Значение по умолчанию");
// If М1сAIСоответствия.HasKey(Map, "ИскомыйКлюч") Then
//     // Ключ найден
// EndIf;

// Пример 6: Копирование и объединение Map
// Map1 = М1сAIСоответствия.NewFromStrings("А,Б", "1,2");
// Map2 = М1сAIСоответствия.NewFromStrings("В,Г", "3,4");
// CopiedMap = М1сAIСоответствия.CopyMap(Map1);
//
// MapsArray = New Array;
// MapsArray.Add(Map1);
// MapsArray.Add(Map2);
// MergedMap = М1сAIСоответствия.MergeMaps(MapsArray);
// // Результат: ["А" = "1", "Б" = "2", "В" = "3", "Г" = "4"]

// Пример 7: Фильтрация Map
// ProductsMap = М1сAIСоответствия.NewFromStrings("iPhone13,iPhone14,Samsung,Nokia", "Apple,Apple,Samsung,Nokia");
// AppleProducts = М1сAIСоответствия.FilterByValues(ProductsMap, "Apple");
// // Результат: только товары Apple

// Пример 8: Преобразования
// JSONString = М1сAIСоответствия.ToJSON(Map);
// Structure = М1сAIСоответствия.ToStructure(Map);
// MapFromStruct = М1сAIСоответствия.FromStructure(Structure);

// Пример 9: Получение информации о Map
// MapInfo = М1сAIСоответствия.Info(Map);
// KeysCount = MapInfo.KeyCount;
// IsEmpty = MapInfo.IsEmpty;
// JSONView = MapInfo.JSONView;

// Пример 10: Отладочный вывод
// DebugText = М1сAIСоответствия.ToString(Map, "МойMap");
// Message(DebugText);

// Пример 11: Сложный пример - обработка справочника
// Function ProcessCatalogToMap()
//
//     ResultMap = М1сAIСоответствия.NewMap();
//
//     Query = New Query;
//     Query.Text = "SELECT Name, Code FROM Catalog.Products";
//     Selection = Query.Execute().Select();
//
//     While Selection.Next() Do
//         М1сAIСоответствия.Insert(ResultMap, Selection.Code, Selection.Name);
//     EndDo;
//
//     // Фильтруем только товары, содержащие "Телефон" в названии
//     PhoneProducts = М1сAIСоответствия.FilterByValues(ResultMap, "Телефон");
//
//     // Получаем отладочную информацию
//     DebugInfo = М1сAIСоответствия.ToString(PhoneProducts, "ТелефонныеТовары");
//     М1сAIEventLog.Write(DebugInfo);
//
//     Return PhoneProducts;
//
// EndFunction

// Пример 12: Работа с настройками пользователя
// Function GetUserSettings(UserRef)
//
//     // Значения по умолчанию
//     DefaultSettings = М1сAIСоответствия.NewFromStrings(
//         "Theme,Language,TimeZone,ShowNotifications",
//         "Light,Russian,UTC+3,True"
//     );
//
//     // Загружаем пользовательские настройки
//     UserSettings = LoadUserSettingsFromDB(UserRef);
//     UserSettingsMap = М1сAIСоответствия.FromStructure(UserSettings);
//
//     // Объединяем с значениями по умолчанию (пользовательские перекрывают дефолтные)
//     MapsArray = New Array;
//     MapsArray.Add(DefaultSettings);
//     MapsArray.Add(UserSettingsMap);
//     FinalSettings = М1сAIСоответствия.MergeMaps(MapsArray, True);
//
//     Return FinalSettings;
//
// EndFunction

// Пример 13: Кэширование данных
// CacheMap = М1сAIСоответствия.NewMap();
//
// Function GetCachedData(Key)
//
//     // Проверяем наличие в кэше
//     If М1сAIСоответствия.HasKey(CacheMap, Key) Then
//         Return М1сAIСоответствия.GetValue(CacheMap, Key);
//     EndIf;
//
//     // Загружаем данные
//     Data = LoadExpensiveData(Key);
//
//     // Сохраняем в кэш
//     М1сAIСоответствия.Insert(CacheMap, Key, Data);
//
//     Return Data;
//
// EndFunction

// Пример 14: Группировка данных
// Function GroupOrdersByStatus()
//
//     StatusGroups = М1сAIСоответствия.NewMap();
//
//     Query = New Query;
//     Query.Text = "SELECT Number, Status FROM Document.Order";
//     Selection = Query.Execute().Select();
//
//     While Selection.Next() Do
//
//         Status = String(Selection.Status);
//         OrderNumber = Selection.Number;
//
//         // Получаем существующий массив или создаем новый
//         OrdersArray = М1сAIСоответствия.GetValue(StatusGroups, Status, New Array);
//         OrdersArray.Add(OrderNumber);
//
//         // Обновляем Map
//         М1сAIСоответствия.Insert(StatusGroups, Status, OrdersArray);
//
//     EndDo;
//
//     Return StatusGroups;
//
// EndFunction

// Пример 15: Валидация и очистка данных
// Function ValidateAndCleanMap(SourceMap, RequiredKeys)
//
//     CleanMap = М1сAIСоответствия.CopyMap(SourceMap);
//
//     // Проверяем наличие обязательных ключей
//     For Each RequiredKey In RequiredKeys Do
//         If Not М1сAIСоответствия.HasKey(CleanMap, RequiredKey) Then
//             М1сAIEventLog.Write("Отсутствует обязательный ключ: " + RequiredKey);
//             Return Undefined;
//         EndIf;
//     EndDo;
//
//     // Удаляем ключи с пустыми значениями
//     KeysToDelete = New Array;
//     For Each KeyValue In CleanMap Do
//         If IsBlankString(KeyValue.Value) Then
//             KeysToDelete.Add(KeyValue.Key);
//         EndIf;
//     EndDo;
//
//     For Each Key In KeysToDelete Do
//         CleanMap.Delete(Key);
//     EndDo;
//
//     Return CleanMap;
//
// EndFunction

#EndRegion