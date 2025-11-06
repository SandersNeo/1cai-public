package com.onecai.edt.services;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.swt.widgets.Display;

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
                    
                    monitor.beginTask("Running EDT Analysis Orchestrator", 
                        type == AnalysisType.FULL ? 6 : 1);
                    
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
                // TODO: добавить флаг --quick в оркестратор
                break;
            case DEPENDENCIES:
                // Только зависимости
                command.add("--skip-parse");
                // TODO: добавить флаг --only-deps
                break;
            case BEST_PRACTICES:
                // Только best practices
                command.add("--skip-parse");
                // TODO: добавить флаг --only-bp
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
        System.out.println("[OrchestratorRunner] " + message);
    }
    
    private static void logError(String message) {
        System.err.println("[OrchestratorRunner] " + message);
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


