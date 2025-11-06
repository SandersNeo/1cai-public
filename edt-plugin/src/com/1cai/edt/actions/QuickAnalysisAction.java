package com.onecai.edt.actions;

import org.eclipse.jface.action.IAction;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.swt.SWT;
import org.eclipse.swt.layout.*;
import org.eclipse.swt.widgets.*;
import org.eclipse.ui.IObjectActionDelegate;
import org.eclipse.ui.IWorkbenchPart;

import com.google.gson.JsonObject;
import com.onecai.edt.services.BackendConnector;

/**
 * Quick Analysis Action
 * Быстрый анализ функции из контекстного меню
 * 
 * Показывает:
 * - Статистика (LOC, сложность, параметры)
 * - Зависимости (кто вызывает, кого вызывает)
 * - Документация
 * - Проблемы (потенциальные баги, anti-patterns)
 * - Best Practices (соответствие стандартам)
 * - Предложения (как улучшить)
 */
public class QuickAnalysisAction implements IObjectActionDelegate {

    private IWorkbenchPart targetPart;
    private Object selectedElement;

    @Override
    public void setActivePart(IAction action, IWorkbenchPart targetPart) {
        this.targetPart = targetPart;
    }

    @Override
    public void run(IAction action) {
        if (selectedElement == null) {
            showWarning("No function selected");
            return;
        }

        // TODO: Extract real function info from selectedElement
        String functionName = extractFunctionName(selectedElement);
        String moduleName = extractModuleName(selectedElement);
        String functionBody = extractFunctionBody(selectedElement);

        if (functionName == null || moduleName == null) {
            showWarning("Could not determine function info");
            return;
        }

        // Показываем диалог с результатами
        performQuickAnalysis(moduleName, functionName, functionBody);
    }

    @Override
    public void selectionChanged(IAction action, ISelection selection) {
        selectedElement = selection;
    }

    /**
     * Выполнение быстрого анализа
     */
    private void performQuickAnalysis(String moduleName, String functionName, String functionBody) {
        // Анализируем локально + запрашиваем backend
        QuickAnalysisResult result = new QuickAnalysisResult();
        
        // Локальный анализ
        result.lines = countLines(functionBody);
        result.complexity = calculateComplexity(functionBody);
        result.parameters = countParameters(functionBody);
        result.hasErrorHandling = checkErrorHandling(functionBody);
        result.hasDocumentation = checkDocumentation(functionBody);
        result.problems = findProblems(functionBody);
        result.suggestions = generateSuggestions(result);
        
        // Backend анализ (async)
        new Thread(() -> {
            try {
                BackendConnector backend = new BackendConnector();
                JsonObject depsResult = backend.analyzeDependencies(moduleName, functionName);
                
                if (depsResult != null) {
                    // TODO: Parse dependencies
                    result.calledFrom = 15; // placeholder
                    result.calls = 4; // placeholder
                }
                
                // Показываем результаты в UI thread
                Display.getDefault().asyncExec(() -> {
                    showQuickAnalysisDialog(moduleName, functionName, result);
                });
                
            } catch (Exception e) {
                Display.getDefault().asyncExec(() -> {
                    showError("Analysis error: " + e.getMessage());
                });
            }
        }).start();
    }

    /**
     * Отображение диалога с результатами
     */
    private void showQuickAnalysisDialog(String moduleName, String functionName, QuickAnalysisResult result) {
        Dialog dialog = new Dialog(targetPart.getSite().getShell()) {
            @Override
            protected Control createDialogArea(Composite parent) {
                Composite container = (Composite) super.createDialogArea(parent);
                GridLayout layout = new GridLayout(1, false);
                layout.marginWidth = 15;
                layout.marginHeight = 15;
                container.setLayout(layout);

                // Title
                Label titleLabel = new Label(container, SWT.NONE);
                titleLabel.setText("Quick Analysis: " + moduleName + "." + functionName + "()");
                Font boldFont = new Font(parent.getDisplay(), "Arial", 12, SWT.BOLD);
                titleLabel.setFont(boldFont);
                titleLabel.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

                // Separator
                Label separator1 = new Label(container, SWT.SEPARATOR | SWT.HORIZONTAL);
                separator1.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

                // Metrics section
                createSection(container, "📊 Метрики", 
                    "Строк кода: " + result.lines + "\n" +
                    "Сложность: " + result.complexity + " (средняя)\n" +
                    "Параметров: " + result.parameters);

                // Dependencies section
                createSection(container, "🔗 Зависимости",
                    "Вызывается из: " + result.calledFrom + " мест\n" +
                    "Вызывает: " + result.calls + " функций");

                // Problems section
                if (!result.problems.isEmpty()) {
                    StringBuilder problems = new StringBuilder();
                    for (String problem : result.problems) {
                        problems.append("• ").append(problem).append("\n");
                    }
                    createSection(container, "⚠️ Проблемы", problems.toString());
                }

                // Suggestions section
                if (!result.suggestions.isEmpty()) {
                    StringBuilder suggestions = new StringBuilder();
                    for (String suggestion : result.suggestions) {
                        suggestions.append("• ").append(suggestion).append("\n");
                    }
                    createSection(container, "💡 Рекомендации", suggestions.toString());
                }

                return container;
            }

            @Override
            protected void createButtonsForButtonBar(Composite parent) {
                createButton(parent, IDialogConstants.OK_ID, "Оптимизировать", false);
                createButton(parent, IDialogConstants.DETAILS_ID, "Подробный отчет", false);
                createButton(parent, IDialogConstants.CLOSE_ID, "Закрыть", true);
            }

            @Override
            protected void configureShell(Shell newShell) {
                super.configureShell(newShell);
                newShell.setText("Quick Analysis");
                newShell.setSize(600, 500);
            }
        };

        dialog.open();
    }

    private void createSection(Composite parent, String title, String content) {
        Group group = new Group(parent, SWT.NONE);
        group.setText(title);
        group.setLayout(new GridLayout(1, false));
        group.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));

        Text text = new Text(group, SWT.MULTI | SWT.READ_ONLY | SWT.WRAP);
        text.setText(content);
        GridData textData = new GridData(SWT.FILL, SWT.FILL, true, true);
        textData.heightHint = 60;
        text.setLayoutData(textData);
        text.setBackground(parent.getDisplay().getSystemColor(SWT.COLOR_WHITE));
    }

    // ========================================================================
    // LOCAL ANALYSIS METHODS
    // ========================================================================

    private int countLines(String code) {
        if (code == null) return 0;
        return code.split("\n").length;
    }

    private int calculateComplexity(String code) {
        if (code == null) return 1;
        
        // Простой подсчет цикломатической сложности
        int complexity = 1;
        
        // Условия
        complexity += countOccurrences(code, "Если");
        complexity += countOccurrences(code, "ИначеЕсли");
        complexity += countOccurrences(code, "If");
        complexity += countOccurrences(code, "ElseIf");
        
        // Циклы
        complexity += countOccurrences(code, "Для");
        complexity += countOccurrences(code, "Пока");
        complexity += countOccurrences(code, "For");
        complexity += countOccurrences(code, "While");
        
        // Исключения
        complexity += countOccurrences(code, "Попытка");
        complexity += countOccurrences(code, "Try");
        
        return complexity;
    }

    private int countParameters(String code) {
        if (code == null) return 0;
        
        // Ищем объявление функции и считаем параметры
        // Паттерн: Функция ИмяФункции(Параметр1, Параметр2, ...)
        String firstLine = code.split("\n")[0];
        if (firstLine.contains("(") && firstLine.contains(")")) {
            String params = firstLine.substring(
                firstLine.indexOf("(") + 1,
                firstLine.indexOf(")")
            ).trim();
            
            if (params.isEmpty()) return 0;
            return params.split(",").length;
        }
        
        return 0;
    }

    private boolean checkErrorHandling(String code) {
        if (code == null) return false;
        return code.contains("Попытка") || code.contains("Try") ||
               code.contains("Исключение") || code.contains("Except");
    }

    private boolean checkDocumentation(String code) {
        if (code == null) return false;
        // Проверяем наличие комментариев перед функцией
        String[] lines = code.split("\n");
        for (int i = 0; i < Math.min(3, lines.length); i++) {
            if (lines[i].trim().startsWith("//")) {
                return true;
            }
        }
        return false;
    }

    private java.util.List<String> findProblems(String code) {
        java.util.List<String> problems = new java.util.ArrayList<>();
        
        if (!checkErrorHandling(code)) {
            problems.add("Нет обработки ошибок");
        }
        
        if (!checkDocumentation(code)) {
            problems.add("Отсутствует документация");
        }
        
        // Проверка на магические числа
        if (containsMagicNumbers(code)) {
            problems.add("Магические числа в коде");
        }
        
        // Проверка длины
        if (countLines(code) > 100) {
            problems.add("Функция слишком длинная (>" + countLines(code) + " строк)");
        }
        
        // Проверка сложности
        int complexity = calculateComplexity(code);
        if (complexity > 15) {
            problems.add("Высокая сложность (" + complexity + ")");
        }
        
        return problems;
    }

    private java.util.List<String> generateSuggestions(QuickAnalysisResult result) {
        java.util.List<String> suggestions = new java.util.ArrayList<>();
        
        if (!result.hasErrorHandling) {
            suggestions.add("Добавить Try...Except для обработки ошибок");
        }
        
        if (!result.hasDocumentation) {
            suggestions.add("Добавить комментарии с описанием функции");
        }
        
        if (result.lines > 100) {
            suggestions.add("Разбить на подфункции (слишком длинная)");
        }
        
        if (result.complexity > 15) {
            suggestions.add("Упростить логику (высокая сложность)");
        }
        
        if (result.parameters > 5) {
            suggestions.add("Уменьшить количество параметров");
        }
        
        return suggestions;
    }

    private boolean containsMagicNumbers(String code) {
        // Простая проверка на числа (кроме 0, 1, -1)
        return code.matches(".*\\b[2-9]\\d*\\b.*");
    }

    private int countOccurrences(String text, String pattern) {
        int count = 0;
        int index = 0;
        while ((index = text.indexOf(pattern, index)) != -1) {
            count++;
            index += pattern.length();
        }
        return count;
    }

    // ========================================================================
    // TODO: EXTRACTION FROM EDT MODEL
    // ========================================================================

    private String extractFunctionName(Object element) {
        // TODO: Extract from 1C BSL model
        return "TestFunction";
    }

    private String extractModuleName(Object element) {
        // TODO: Extract from 1C BSL model
        return "TestModule";
    }

    private String extractFunctionBody(Object element) {
        // TODO: Extract from 1C BSL model
        return "Функция TestFunction(Параметр1, Параметр2)\n" +
               "  // TODO: implementation\n" +
               "  Результат = 0;\n" +
               "  Возврат Результат;\n" +
               "КонецФункции";
    }

    private void showWarning(String message) {
        org.eclipse.jface.dialogs.MessageDialog.openWarning(
            targetPart.getSite().getShell(),
            "Quick Analysis",
            message
        );
    }

    private void showError(String message) {
        org.eclipse.jface.dialogs.MessageDialog.openError(
            targetPart.getSite().getShell(),
            "Error",
            message
        );
    }

    /**
     * Результат быстрого анализа
     */
    static class QuickAnalysisResult {
        int lines;
        int complexity;
        int parameters;
        int calledFrom;
        int calls;
        boolean hasErrorHandling;
        boolean hasDocumentation;
        java.util.List<String> problems = new java.util.ArrayList<>();
        java.util.List<String> suggestions = new java.util.ArrayList<>();
    }
}


