# Следующие шаги для завершения доработки плагина EDT

## ✅ Что уже сделано

1. ✅ **Analysis Dashboard View** - отображение результатов оркестратора
2. ✅ **Orchestrator Runner** - запуск оркестратора из EDT
3. ✅ **Quick Analysis Action** - быстрый анализ функций
4. ✅ **plugin.xml** - обновлен с новыми views/actions
5. ✅ **Документация** - ENHANCEMENT_PROPOSALS.md (43 стр) + IMPROVEMENT_SUMMARY.md

---

## 🔨 Что нужно доделать для MVP

### Шаг 1: Создать недостающие Action классы (1-2 дня)

Нужно создать файлы для actions, объявленных в `plugin.xml`:

```bash
edt-plugin/src/com/1cai/edt/actions/
├── RunFullAnalysisAction.java        # TODO
├── RunQuickAnalysisAction.java       # TODO
├── RefreshDependenciesAction.java    # TODO
├── UpdateBestPracticesAction.java    # TODO
└── GenerateCodeAction.java           # TODO
```

#### Шаблон для реализации:

**Файл**: `RunFullAnalysisAction.java`
```java
package com.onecai.edt.actions;

import org.eclipse.jface.action.IAction;
import org.eclipse.jface.dialogs.InputDialog;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.IWorkbenchWindowActionDelegate;

import com.onecai.edt.services.OrchestratorRunner;

public class RunFullAnalysisAction implements IWorkbenchWindowActionDelegate {
    private IWorkbenchWindow window;

    @Override
    public void run(IAction action) {
        Shell shell = window.getShell();
        
        // Диалог выбора конфигурации
        InputDialog dialog = new InputDialog(
            shell,
            "Run Full Analysis",
            "Enter configuration name:",
            "ERPCPM",
            null
        );
        
        if (dialog.open() == Window.OK) {
            String configName = dialog.getValue();
            
            // Запустить оркестратор
            OrchestratorRunner.runFullAnalysis(configName, () -> {
                // Callback: обновить Dashboard
                // TODO: найти и обновить AnalysisDashboardView
            });
        }
    }

    @Override
    public void init(IWorkbenchWindow window) {
        this.window = window;
    }

    @Override
    public void dispose() {}

    @Override
    public void selectionChanged(IAction action, 
        org.eclipse.jface.viewers.ISelection selection) {}
}
```

Аналогично создать остальные 4 файла.

---

### Шаг 2: Создать Command handlers для горячих клавиш (1 день)

В `plugin.xml` объявлены key bindings, но нужны commands:

```xml
<!-- Добавить в plugin.xml перед bindings -->
<extension point="org.eclipse.ui.commands">
   <command
      id="com.1cai.edt.commands.openAIAssistant"
      name="Open AI Assistant"
      description="Открыть AI Assistant">
   </command>
   
   <command
      id="com.1cai.edt.commands.semanticSearch"
      name="Semantic Search"
      description="Открыть Semantic Search">
   </command>
   
   <command
      id="com.1cai.edt.commands.quickAnalysis"
      name="Quick Analysis"
      description="Быстрый анализ функции">
   </command>
   
   <command
      id="com.1cai.edt.commands.optimize"
      name="Optimize Code"
      description="Оптимизировать код">
   </command>
</extension>

<!-- Связать с handlers -->
<extension point="org.eclipse.ui.handlers">
   <handler
      commandId="com.1cai.edt.commands.openAIAssistant"
      class="com.1cai.edt.handlers.OpenAIAssistantHandler">
   </handler>
   <!-- ... остальные handlers -->
</extension>
```

Создать классы handlers:

```bash
edt-plugin/src/com/1cai/edt/handlers/
├── OpenAIAssistantHandler.java       # TODO
├── SemanticSearchHandler.java        # TODO
├── QuickAnalysisHandler.java         # TODO
└── OptimizeCodeHandler.java          # TODO
```

**Шаблон**:
```java
package com.onecai.edt.handlers;

import org.eclipse.core.commands.*;
import org.eclipse.ui.*;

public class OpenAIAssistantHandler extends AbstractHandler {
    @Override
    public Object execute(ExecutionEvent event) throws ExecutionException {
        try {
            IWorkbenchPage page = PlatformUI.getWorkbench()
                .getActiveWorkbenchWindow()
                .getActivePage();
            
            page.showView("com.1cai.edt.views.AIAssistant");
            
        } catch (PartInitException e) {
            throw new ExecutionException("Failed to open view", e);
        }
        
        return null;
    }
}
```

---

### Шаг 3: Исправить импорты в существующих файлах (30 мин)

В созданных файлах используются классы без полного import:

#### AnalysisDashboardView.java:
```java
// Добавить в начало файла:
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.widgets.Group;
import org.eclipse.swt.widgets.Canvas;
import org.eclipse.swt.widgets.Link;
```

#### QuickAnalysisAction.java:
```java
// Добавить:
import org.eclipse.jface.viewers.ISelection;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Text;
import org.eclipse.swt.widgets.Group;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.widgets.Shell;
```

#### OrchestratorRunner.java:
```java
// Добавить:
import org.eclipse.swt.widgets.Display;
```

---

### Шаг 4: Добавить иконки (1 час)

Создать или найти иконки 16x16 для views/actions:

```bash
edt-plugin/icons/
├── ai-assistant.png     # ✅ (если есть)
├── graph.png            # ✅ (если есть)
├── search.png           # ✅ (если есть)
├── optimize.png         # ✅ (если есть)
├── dashboard.png        # TODO - новая иконка
├── quick-analysis.png   # TODO - новая иконка
├── analyze.png          # ✅ (если есть)
└── ...
```

Если иконок нет, можно использовать Unicode emoji или стандартные Eclipse иконки:
```java
// В коде можно использовать без иконок:
// Eclipse автоматически покажет текст
```

---

### Шаг 5: Интеграция с 1C EDT API (2-3 дня)

**Проблема**: Текущий код использует заглушки для извлечения информации о функциях:

```java
// Сейчас (заглушка):
private String extractFunctionName(Object element) {
    return "TestFunction";
}

// Нужно (реальная интеграция):
private String extractFunctionName(Object element) {
    if (element instanceof Method) {
        Method method = (Method) element;
        return method.getName();
    }
    return null;
}
```

**Что нужно**:

1. Добавить зависимость на 1C EDT API в `pom.xml`:
```xml
<dependency>
    <groupId>com._1c.g5.v8.dt</groupId>
    <artifactId>bsl</artifactId>
    <version>LATEST</version>
    <scope>provided</scope>
</dependency>
```

2. Обновить методы в `QuickAnalysisAction.java`:
```java
import com._1c.g5.v8.dt.bsl.model.Method;
import com._1c.g5.v8.dt.bsl.model.Module;

private String extractFunctionName(Object element) {
    if (element instanceof Method) {
        return ((Method) element).getName();
    }
    return null;
}

private String extractModuleName(Object element) {
    if (element instanceof Method) {
        Module module = (Module) ((Method) element).eContainer();
        return module.getName();
    }
    return null;
}

private String extractFunctionBody(Object element) {
    if (element instanceof Method) {
        Method method = (Method) element;
        return method.getBody().getText();
    }
    return "";
}
```

---

### Шаг 6: Тестирование в EDT (1-2 дня)

#### 6.1 Локальная сборка и установка:
```bash
cd edt-plugin
mvn clean package

# Проверить что jar создался:
ls -lh target/com.1cai.edt-1.0.0-SNAPSHOT.jar
```

#### 6.2 Установка в EDT:
```
1. Открыть EDT
2. Help → Install New Software
3. Add → Local → Browse: edt-plugin/target/repository
4. Выбрать "1C AI Assistant"
5. Next → Finish
6. Restart EDT
```

#### 6.3 Проверка установки:
```
1. Window → Show View → Other...
   → Должна быть категория "1C AI Assistant"
   → Должно быть 5 views

2. Открыть BSL модуль
   → Правая кнопка на функции
   → Должно быть подменю "1C AI Assistant"

3. Проверить меню
   → В главном меню должен быть "1C AI Assistant"
```

#### 6.4 Функциональное тестирование:

**Тест 1: Analysis Dashboard**
```
1. Window → Show View → Analysis Dashboard
2. Выбрать конфигурацию: ERPCPM
3. Проверить что загружаются данные из JSON
4. Кликнуть "Обновить анализ" - должен запуститься оркестратор
```

**Тест 2: Quick Analysis**
```
1. Открыть любой BSL модуль
2. Поставить курсор на функцию
3. Ctrl+Alt+Q (или правая кнопка → Quick Analysis)
4. Проверить что показываются метрики
```

**Тест 3: Orchestrator Runner**
```
1. Меню: 1C AI Assistant → Run Full Analysis
2. Ввести: ERPCPM
3. Проверить:
   - Появился Job в Progress View
   - Логи выводятся
   - После завершения - уведомление
   - Dashboard обновился
```

---

### Шаг 7: Обработка ошибок (1 день)

Добавить проверки и fallback:

#### В AnalysisDashboardView.java:
```java
private void loadAnalysisResults() {
    String configName = configCombo.getText();
    
    try {
        String archPath = "output/analysis/architecture_analysis.json";
        File archFile = Paths.get(archPath).toFile();
        
        if (!archFile.exists()) {
            showWarning(
                "Analysis results not found",
                "Please run orchestrator first:\n" +
                "1C AI Assistant → Run Full Analysis"
            );
            return;
        }
        
        // ... остальной код
        
    } catch (FileNotFoundException e) {
        showError("File not found: " + e.getMessage());
    } catch (JsonSyntaxException e) {
        showError("Invalid JSON format: " + e.getMessage());
    } catch (Exception e) {
        showError("Unexpected error: " + e.getMessage());
        e.printStackTrace();
    }
}
```

#### В OrchestratorRunner.java:
```java
private static Path getProjectRoot() {
    String workspaceRoot = System.getProperty("user.dir");
    Path path = Paths.get(workspaceRoot);
    
    // Проверяем наличие скрипта
    File scriptFile = path.resolve(ORCHESTRATOR_SCRIPT).toFile();
    if (!scriptFile.exists()) {
        // Пытаемся найти в родительской директории
        path = path.getParent();
        scriptFile = path.resolve(ORCHESTRATOR_SCRIPT).toFile();
        
        if (!scriptFile.exists()) {
            throw new IllegalStateException(
                "Orchestrator script not found: " + ORCHESTRATOR_SCRIPT + "\n" +
                "Please ensure you are in the project root directory."
            );
        }
    }
    
    return path;
}
```

---

### Шаг 8: Документация пользователя (1 день)

Обновить `README.md` с инструкциями для пользователей:

```markdown
## Quick Start

### 1. Установка плагина

### 2. Настройка

Window → Preferences → 1C AI Assistant

- MCP Server URL: http://localhost:6001
- Graph API URL: http://localhost:8080
- Нажать "Test Connection"

### 3. Запуск анализа

1C AI Assistant → Run Full Analysis → Введите конфигурацию: ERPCPM

### 4. Просмотр результатов

Window → Show View → Other → 1C AI Assistant → Analysis Dashboard

### 5. Быстрый анализ функции

- Открыть BSL модуль
- Курсор на функцию
- Ctrl+Alt+Q

## Горячие клавиши

- Ctrl+Alt+A - AI Assistant
- Ctrl+Alt+S - Semantic Search
- Ctrl+Alt+Q - Quick Analysis
- Ctrl+Alt+O - Optimize Code

## Troubleshooting

### "Connection refused"
→ Убедитесь что backend запущен: docker-compose up

### "Analysis results not found"
→ Запустите оркестратор: 1C AI Assistant → Run Full Analysis

### "Orchestrator script not found"
→ Проверьте что скрипт существует: scripts/orchestrate_edt_analysis.sh
```

---

## 📋 Чек-лист MVP

Отметьте выполненные задачи:

### Код:
- [x] AnalysisDashboardView.java
- [x] OrchestratorRunner.java
- [x] QuickAnalysisAction.java
- [x] plugin.xml updated
- [ ] RunFullAnalysisAction.java
- [ ] RunQuickAnalysisAction.java
- [ ] RefreshDependenciesAction.java
- [ ] UpdateBestPracticesAction.java
- [ ] GenerateCodeAction.java
- [ ] Handlers (4 файла)
- [ ] Commands в plugin.xml
- [ ] Исправить импорты
- [ ] Интеграция с EDT API

### Ресурсы:
- [ ] Иконки (dashboard.png, quick-analysis.png)

### Тестирование:
- [ ] Сборка (mvn clean package)
- [ ] Установка в EDT
- [ ] Функциональные тесты
- [ ] Обработка ошибок

### Документация:
- [ ] README.md обновлен
- [ ] Примеры использования
- [ ] Troubleshooting guide

---

## 🚀 Запуск после завершения

```bash
# 1. Сборка
cd edt-plugin
mvn clean package

# 2. Проверка результата
ls -lh target/com.1cai.edt-1.0.0-SNAPSHOT.jar

# 3. Запуск backend
cd ..
docker-compose up -d

# 4. Установка в EDT
# (через GUI - см. шаг 6.2)

# 5. Тестирование
# (см. шаг 6.4)
```

---

## 📞 Если возникли проблемы

### Ошибки компиляции:
1. Проверить версию Java: `java -version` (должна быть 17+)
2. Проверить Maven: `mvn -version` (должна быть 3.8+)
3. Очистить кеш: `mvn clean`
4. Пересобрать: `mvn package -U`

### Плагин не появляется в EDT:
1. Проверить Error Log: Window → Show View → Error Log
2. Проверить что jar создался: `ls target/*.jar`
3. Перезапустить EDT с флагом: `edt.exe -clean`

### Backend не отвечает:
1. Проверить что запущен: `docker-compose ps`
2. Проверить порты: `curl http://localhost:8080/health`
3. Проверить логи: `docker-compose logs`

---

## 💡 Советы

### Быстрая разработка:
```bash
# Terminal 1: Auto-rebuild при изменениях
cd edt-plugin
mvn compile -Dmaven.compiler.showCompilerWarnings=true

# Terminal 2: Watch логи
tail -f logs/edt_analysis/*.log
```

### Debug плагина:
```
1. В EDT: Run → Debug Configurations
2. Eclipse Application → New
3. Workspace Data: указать тестовый workspace
4. Run
```

### Hot Reload (без перезапуска EDT):
```
Некоторые изменения можно применить без перезапуска:
- Изменения в Java классах (если используется DCEVM)
- Изменения в resource файлах

НО: Изменения в plugin.xml требуют перезапуска!
```

---

## 📚 Полезные ссылки

- Eclipse Plugin Development: https://www.eclipse.org/articles/
- 1C EDT API: (если есть документация)
- Maven Tycho: https://www.eclipse.org/tycho/
- SWT Widgets: https://www.eclipse.org/swt/widgets/

---

## ✅ Когда MVP готов

Когда все пункты в чек-листе отмечены:

1. Протестировать все функции
2. Создать демо-видео
3. Написать release notes
4. Опубликовать (если нужно)
5. Собрать обратную связь от пользователей
6. Перейти к Фазе 2 (см. ENHANCEMENT_PROPOSALS.md)

---

**Удачи в разработке! 🚀**


