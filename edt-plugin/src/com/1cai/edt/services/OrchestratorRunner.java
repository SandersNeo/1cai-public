package com.onecai.edt.services;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.core.runtime.ILog;
import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.swt.widgets.Display;
import org.eclipse.ui.console.ConsolePlugin;
import org.eclipse.ui.console.IConsole;
import org.eclipse.ui.console.IConsoleManager;
import org.eclipse.ui.console.MessageConsole;
import org.eclipse.ui.console.MessageConsoleStream;

import com.onecai.edt.Activator;

/**
 * Orchestrator Runner
 * Запускает оркестратор анализа EDT из плагина
 * 
 * Функции:
 * - Запуск скрипта orchestrate_edt_analysis.sh
 * - Отслеживание прогресса
 * - Парсинг логов
 * - Уведомление о завершении
 */
public class OrchestratorRunner {

    private static final String ORCHESTRATOR_SCRIPT = "scripts/orchestrate_edt_analysis.sh";
    private static final Pattern STEP_PATTERN = Pattern.compile("Step (\\d+)/(\\d+): (.+)");
    private static final Pattern SUCCESS_PATTERN = Pattern.compile("✅ (.+) complete \\((\\d+)s\\)");
    private static final String CONSOLE_NAME = "1C AI Assistant";
    private static volatile MessageConsole sharedConsole;
    
    /**
     * Запуск полного анализа
     */
    public static void runFullAnalysis(String configName, Runnable onComplete) {
        runAnalysis(configName, AnalysisType.FULL, onComplete);
    }
    
    /**
     * Запуск быстрого анализа (только парсинг)
     */
    public static void runQuickAnalysis(String configName, Runnable onComplete) {
        runAnalysis(configName, AnalysisType.QUICK, onComplete);
    }
    
    /**
     * Обновление только зависимостей
     */
    public static void refreshDependencies(String configName, Runnable onComplete) {
        runAnalysis(configName, AnalysisType.DEPENDENCIES, onComplete);
    }
    
    /**
     * Обновление только best practices
     */
    public static void updateBestPractices(String configName, Runnable onComplete) {
        runAnalysis(configName, AnalysisType.BEST_PRACTICES, onComplete);
    }
    
    private static void runAnalysis(String configName, AnalysisType type, Runnable onComplete) {
        Job job = new Job("EDT Analysis: " + configName) {
            @Override
            protected IStatus run(IProgressMonitor monitor) {
                try {
                    // Определяем команду
                    List<String> command = buildCommand(configName, type);
                    
                    // Получаем рабочую директорию (корень проекта)
                    Path workingDir = getProjectRoot();
                    
                    int totalWork = type == AnalysisType.FULL ? 2 : 1;
                    monitor.beginTask("Running EDT Analysis Orchestrator", totalWork);
                    
                    // Запускаем процесс
                    ProcessBuilder pb = new ProcessBuilder(command);
                    pb.directory(workingDir.toFile());
                    pb.redirectErrorStream(true);
                    
                    Process process = pb.start();
                    
                    // Читаем вывод
                    BufferedReader reader = new BufferedReader(
                        new InputStreamReader(process.getInputStream()));
                    
                    String line;
                    int currentStep = 0;
                    int totalSteps = type == AnalysisType.FULL ? 6 : 1;
                    
                    while ((line = reader.readLine()) != null) {
                        final String logLine = line;
                        
                        // Парсим прогресс из логов
                        Matcher stepMatcher = STEP_PATTERN.matcher(line);
                        if (stepMatcher.find()) {
                            currentStep = Integer.parseInt(stepMatcher.group(1));
                            totalSteps = Integer.parseInt(stepMatcher.group(2));
                            String stepName = stepMatcher.group(3);
                            
                            monitor.worked(1);
                            monitor.subTask(stepName);
                            
                            logInfo(logLine);
                        }
                        
                        // Проверяем успешное завершение шага
                        Matcher successMatcher = SUCCESS_PATTERN.matcher(line);
                        if (successMatcher.find()) {
                            String stepName = successMatcher.group(1);
                            String duration = successMatcher.group(2);
                            logInfo("✓ " + stepName + " (" + duration + "s)");
                        }
                        
                        // Проверяем ошибки
                        if (line.contains("ERROR") || line.contains("FAILED")) {
                            logError(logLine);
                        }
                    }
                    
                    // Ждем завершения
                    int exitCode = process.waitFor();
                    
                    monitor.done();
                    
                    if (exitCode == 0) {
                        logInfo("Analysis completed successfully!");
                        
                        // Вызываем callback
                        if (onComplete != null) {
                            Display.getDefault().asyncExec(onComplete);
                        }
                        
                        // Показываем уведомление
                        showNotification(
                            "Analysis Complete",
                            "EDT analysis for " + configName + " finished successfully.\n" +
                            "Results are available in output/ directory."
                        );
                        
                        return Status.OK_STATUS;
                        
                    } else {
                        logError("Analysis failed with exit code: " + exitCode);
                        
                        showError(
                            "Analysis Failed",
                            "EDT analysis failed. Check logs for details.\n" +
                            "Exit code: " + exitCode
                        );
                        
                        return Status.CANCEL_STATUS;
                    }
                    
                } catch (Exception e) {
                    logError("Analysis error: " + e.getMessage());
                    e.printStackTrace();
                    
                    showError(
                        "Analysis Error",
                        "Unexpected error: " + e.getMessage()
                    );
                    
                    return Status.CANCEL_STATUS;
                }
            }
        };
        
        job.setUser(true); // Show in UI
        job.setPriority(Job.LONG);
        job.schedule();
    }
    
    /**
     * Построение команды для запуска
     */
    private static List<String> buildCommand(String configName, AnalysisType type) {
        List<String> command = new ArrayList<>();
        
        // Определяем оболочку (bash для Unix, PowerShell для Windows)
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) {
            command.add("powershell.exe");
            command.add("-ExecutionPolicy");
            command.add("Bypass");
            command.add("-File");
            // Windows: запускаем через wrapper
            command.add("scripts/orchestrate_edt_analysis.ps1");
        } else {
            command.add("bash");
            command.add(ORCHESTRATOR_SCRIPT);
        }
        
        // Добавляем конфигурацию
        command.add(configName);
        
        // Добавляем флаги в зависимости от типа анализа
        switch (type) {
            case QUICK:
                // Только парсинг, пропустить анализы
                command.add("--quick");
                break;
            case DEPENDENCIES:
                // Только зависимости
                command.add("--skip-parse");
                command.add("--only-deps");
                break;
            case BEST_PRACTICES:
                // Только best practices
                command.add("--skip-parse");
                command.add("--only-bp");
                break;
            case FULL:
            default:
                // Полный анализ, без флагов
                break;
        }
        
        return command;
    }
    
    /**
     * Получение корня проекта
     */
    private static Path getProjectRoot() {
        // Попытка определить корень проекта
        String workspaceRoot = System.getProperty("user.dir");
        Path path = Paths.get(workspaceRoot);
        
        // Проверяем наличие scripts/orchestrate_edt_analysis.sh
        File scriptFile = path.resolve(ORCHESTRATOR_SCRIPT).toFile();
        if (scriptFile.exists()) {
            return path;
        }
        
        // Если не нашли, пытаемся подняться на уровень выше
        path = path.getParent();
        scriptFile = path.resolve(ORCHESTRATOR_SCRIPT).toFile();
        if (scriptFile.exists()) {
            return path;
        }
        
        // По умолчанию возвращаем текущую директорию
        return Paths.get(workspaceRoot);
    }
    
    private static void showNotification(String title, String message) {
        Display.getDefault().asyncExec(() -> {
            // TODO: Use Eclipse notification API
            // For now, simple message dialog
            org.eclipse.jface.dialogs.MessageDialog.openInformation(
                null, title, message
            );
        });
    }
    
    private static void showError(String title, String message) {
        Display.getDefault().asyncExec(() -> {
            org.eclipse.jface.dialogs.MessageDialog.openError(
                null, title, message
            );
        });
    }
    
    private static void logInfo(String message) {
        log(IStatus.INFO, message);
    }
    
    private static void logError(String message) {
        log(IStatus.ERROR, message);
    }

    private static void log(int severity, String message) {
        String decorated = "[Orchestrator] " + message;

        Activator activator = Activator.getDefault();
        if (activator != null) {
            ILog pluginLog = activator.getLog();
            if (pluginLog != null) {
                pluginLog.log(new Status(severity, Activator.PLUGIN_ID, decorated));
            }
        }

        // Fallback to stdout/stderr for development consoles
        if (severity == IStatus.ERROR) {
            System.err.println(decorated);
        } else {
            System.out.println(decorated);
        }

        appendToConsole(severity, decorated);
    }

    private static void appendToConsole(int severity, String message) {
        Display display = Display.getDefault();
        if (display == null || display.isDisposed()) {
            return;
        }

        display.asyncExec(() -> {
            MessageConsole console = getConsole();
            if (console == null) {
                return;
            }

            try (MessageConsoleStream stream = console.newMessageStream()) {
                String prefix = severity == IStatus.ERROR ? "[ERROR] " : "[INFO] ";
                stream.println(prefix + message);
            } catch (IOException e) {
                // If console writing fails, log to stderr
                System.err.println("[Orchestrator] Console write failed: " + e.getMessage());
            }
        });
    }

    private static MessageConsole getConsole() {
        MessageConsole console = sharedConsole;
        if (console != null) {
            return console;
        }

        ConsolePlugin consolePlugin = ConsolePlugin.getDefault();
        if (consolePlugin == null) {
            return null;
        }

        IConsoleManager manager = consolePlugin.getConsoleManager();
        for (IConsole existing : manager.getConsoles()) {
            if (existing instanceof MessageConsole && CONSOLE_NAME.equals(existing.getName())) {
                sharedConsole = (MessageConsole) existing;
                return sharedConsole;
            }
        }

        MessageConsole newConsole = new MessageConsole(CONSOLE_NAME, null);
        manager.addConsoles(new IConsole[] { newConsole });
        sharedConsole = newConsole;
        return sharedConsole;
    }
    
    /**
     * Типы анализа
     */
    public enum AnalysisType {
        FULL,           // Полный анализ (все 6 шагов)
        QUICK,          // Быстрый (только парсинг)
        DEPENDENCIES,   // Только зависимости
        BEST_PRACTICES  // Только best practices
    }
}



