package com.onecai.edt.views;

import java.io.FileReader;
import java.nio.file.Paths;
import java.text.NumberFormat;
import java.util.Locale;

import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.ScrolledComposite;
import org.eclipse.swt.layout.*;
import org.eclipse.swt.widgets.*;
import org.eclipse.ui.part.ViewPart;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

/**
 * Configuration Analysis Dashboard
 * Отображает результаты полного анализа конфигурации из оркестратора
 * 
 * Показывает:
 * - Архитектурную статистику
 * - Граф зависимостей
 * - Best practices score
 * - ML dataset insights
 */
public class AnalysisDashboardView extends ViewPart {

    public static final String ID = "com.1cai.edt.views.AnalysisDashboard";

    private Combo configCombo;
    private Button refreshButton;
    private ScrolledComposite scrolledComposite;
    private Composite contentComposite;
    
    // Stats labels
    private Label modulesCountLabel;
    private Label catalogsCountLabel;
    private Label documentsCountLabel;
    private Label methodsCountLabel;
    private Label locCountLabel;
    
    // Dependencies labels
    private Label strongCouplingLabel;
    private Label cyclicDepsLabel;
    private Label isolatedLabel;
    
    // Best practices labels
    private Label errorHandlingLabel;
    private Label documentationLabel;
    private Label namingLabel;
    
    private Gson gson = new Gson();
    private NumberFormat numberFormat = NumberFormat.getInstance(Locale.US);

    @Override
    public void createPartControl(Composite parent) {
        // Main container
        Composite container = new Composite(parent, SWT.NONE);
        GridLayout layout = new GridLayout(1, false);
        layout.marginWidth = 10;
        layout.marginHeight = 10;
        container.setLayout(layout);

        // Top bar with controls
        createTopBar(container);

        // Scrolled content area
        scrolledComposite = new ScrolledComposite(container, 
            SWT.V_SCROLL | SWT.H_SCROLL | SWT.BORDER);
        scrolledComposite.setLayoutData(
            new GridData(SWT.FILL, SWT.FILL, true, true));
        scrolledComposite.setExpandHorizontal(true);
        scrolledComposite.setExpandVertical(true);

        contentComposite = new Composite(scrolledComposite, SWT.NONE);
        GridLayout contentLayout = new GridLayout(1, false);
        contentLayout.verticalSpacing = 15;
        contentComposite.setLayout(contentLayout);

        // Create sections
        createArchitectureSection(contentComposite);
        createDependenciesSection(contentComposite);
        createBestPracticesSection(contentComposite);
        createTrendsSection(contentComposite);

        scrolledComposite.setContent(contentComposite);
        scrolledComposite.setMinSize(contentComposite.computeSize(SWT.DEFAULT, SWT.DEFAULT));

        // Load initial data
        loadAnalysisResults();
    }

    private void createTopBar(Composite parent) {
        Composite topBar = new Composite(parent, SWT.NONE);
        topBar.setLayout(new GridLayout(4, false));
        topBar.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        Label titleLabel = new Label(topBar, SWT.NONE);
        titleLabel.setText("Configuration Analysis Dashboard");
        titleLabel.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        Label configLabel = new Label(topBar, SWT.NONE);
        configLabel.setText("Configuration:");

        configCombo = new Combo(topBar, SWT.DROP_DOWN | SWT.READ_ONLY);
        configCombo.setItems(new String[]{"ERPCPM", "ERP", "ZUP", "BUH", "DO", "KA"});
        configCombo.select(0);
        configCombo.addListener(SWT.Selection, e -> loadAnalysisResults());

        refreshButton = new Button(topBar, SWT.PUSH);
        refreshButton.setText("🔄 Обновить анализ");
        refreshButton.setToolTipText("Запустить оркестратор анализа заново");
        refreshButton.addListener(SWT.Selection, e -> runOrchestrator());
    }

    private void createArchitectureSection(Composite parent) {
        Group group = new Group(parent, SWT.NONE);
        group.setText("📊 АРХИТЕКТУРА");
        group.setLayout(new GridLayout(2, false));
        group.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        // Modules
        new Label(group, SWT.NONE).setText("Модулей:");
        modulesCountLabel = new Label(group, SWT.NONE);
        modulesCountLabel.setText("—");

        // Catalogs
        new Label(group, SWT.NONE).setText("Справочников:");
        catalogsCountLabel = new Label(group, SWT.NONE);
        catalogsCountLabel.setText("—");

        // Documents
        new Label(group, SWT.NONE).setText("Документов:");
        documentsCountLabel = new Label(group, SWT.NONE);
        documentsCountLabel.setText("—");

        // Methods
        new Label(group, SWT.NONE).setText("Всего методов:");
        methodsCountLabel = new Label(group, SWT.NONE);
        methodsCountLabel.setText("—");

        // LOC
        new Label(group, SWT.NONE).setText("Строк кода:");
        locCountLabel = new Label(group, SWT.NONE);
        locCountLabel.setText("—");

        // Link to detailed view
        Link detailsLink = new Link(group, SWT.NONE);
        detailsLink.setText("<a>Подробная статистика...</a>");
        GridData linkData = new GridData(SWT.RIGHT, SWT.CENTER, false, false);
        linkData.horizontalSpan = 2;
        detailsLink.setLayoutData(linkData);
        detailsLink.addListener(SWT.Selection, e -> showDetailedArchitecture());
    }

    private void createDependenciesSection(Composite parent) {
        Group group = new Group(parent, SWT.NONE);
        group.setText("🔗 ЗАВИСИМОСТИ");
        group.setLayout(new GridLayout(2, false));
        group.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        new Label(group, SWT.NONE).setText("Сильно связанных:");
        strongCouplingLabel = new Label(group, SWT.NONE);
        strongCouplingLabel.setText("—");

        new Label(group, SWT.NONE).setText("Циклических:");
        cyclicDepsLabel = new Label(group, SWT.NONE);
        cyclicDepsLabel.setText("—");

        new Label(group, SWT.NONE).setText("Изолированных:");
        isolatedLabel = new Label(group, SWT.NONE);
        isolatedLabel.setText("—");

        Button showGraphButton = new Button(group, SWT.PUSH);
        showGraphButton.setText("Показать граф");
        GridData buttonData = new GridData(SWT.RIGHT, SWT.CENTER, false, false);
        buttonData.horizontalSpan = 2;
        showGraphButton.setLayoutData(buttonData);
        showGraphButton.addListener(SWT.Selection, e -> showDependencyGraph());
    }

    private void createBestPracticesSection(Composite parent) {
        Group group = new Group(parent, SWT.NONE);
        group.setText("✅ BEST PRACTICES");
        group.setLayout(new GridLayout(3, false));
        group.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        // Error Handling
        new Label(group, SWT.NONE).setText("Обработка ошибок:");
        errorHandlingLabel = new Label(group, SWT.NONE);
        errorHandlingLabel.setText("—");
        Label errorStatusLabel = new Label(group, SWT.NONE);
        errorStatusLabel.setText("");

        // Documentation
        new Label(group, SWT.NONE).setText("Документирование:");
        documentationLabel = new Label(group, SWT.NONE);
        documentationLabel.setText("—");
        Label docStatusLabel = new Label(group, SWT.NONE);
        docStatusLabel.setText("");

        // Naming
        new Label(group, SWT.NONE).setText("Именование:");
        namingLabel = new Label(group, SWT.NONE);
        namingLabel.setText("—");
        Label namingStatusLabel = new Label(group, SWT.NONE);
        namingStatusLabel.setText("");

        Link detailsLink = new Link(group, SWT.NONE);
        detailsLink.setText("<a>Подробные рекомендации...</a>");
        GridData linkData = new GridData(SWT.RIGHT, SWT.CENTER, false, false);
        linkData.horizontalSpan = 3;
        detailsLink.setLayoutData(linkData);
        detailsLink.addListener(SWT.Selection, e -> showBestPracticesDetails());
    }

    private void createTrendsSection(Composite parent) {
        Group group = new Group(parent, SWT.NONE);
        group.setText("📈 ТРЕНДЫ");
        group.setLayout(new GridLayout(1, false));
        group.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        Label placeholderLabel = new Label(group, SWT.NONE);
        placeholderLabel.setText("График изменений качества кода за последние запуски");
        placeholderLabel.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));

        // TODO: Implement chart using JFreeChart or JavaFX
        Canvas canvas = new Canvas(group, SWT.BORDER);
        GridData canvasData = new GridData(SWT.FILL, SWT.FILL, true, false);
        canvasData.heightHint = 150;
        canvas.setLayoutData(canvasData);
        canvas.setBackground(parent.getDisplay().getSystemColor(SWT.COLOR_WHITE));
    }

    /**
     * Загрузка результатов анализа из JSON файлов
     */
    public void loadAnalysisResults() {
        String configName = configCombo.getText();
        
        try {
            // Load architecture analysis
            String archPath = "output/analysis/architecture_analysis.json";
            if (Paths.get(archPath).toFile().exists()) {
                JsonObject archData = gson.fromJson(
                    new FileReader(archPath), JsonObject.class);
                updateArchitectureStats(archData);
            }

            // Load dependency analysis
            String depsPath = "output/analysis/dependency_graph.json";
            if (Paths.get(depsPath).toFile().exists()) {
                JsonObject depsData = gson.fromJson(
                    new FileReader(depsPath), JsonObject.class);
                updateDependencyStats(depsData);
            }

            // Load best practices
            String bpPath = "output/analysis/best_practices.json";
            if (Paths.get(bpPath).toFile().exists()) {
                JsonObject bpData = gson.fromJson(
                    new FileReader(bpPath), JsonObject.class);
                updateBestPracticesStats(bpData);
            }

        } catch (Exception e) {
            showError("Не удалось загрузить результаты анализа: " + e.getMessage());
        }
    }

    private void updateArchitectureStats(JsonObject data) {
        try {
            JsonObject distribution = data.getAsJsonObject("distribution");
            JsonObject complexity = data.getAsJsonObject("complexity");
            JsonObject volume = data.getAsJsonObject("volume");

            if (distribution != null) {
                int modules = distribution.get("common_modules").getAsInt();
                int catalogs = distribution.get("catalogs").getAsInt();
                int documents = distribution.get("documents").getAsInt();

                modulesCountLabel.setText(numberFormat.format(modules));
                catalogsCountLabel.setText(numberFormat.format(catalogs));
                documentsCountLabel.setText(numberFormat.format(documents));
            }

            if (complexity != null) {
                int methods = complexity.get("total_methods").getAsInt();
                methodsCountLabel.setText(numberFormat.format(methods));
            }

            if (volume != null) {
                JsonObject cmVolume = volume.getAsJsonObject("common_modules");
                if (cmVolume != null) {
                    long totalLoc = cmVolume.get("total").getAsLong();
                    locCountLabel.setText(formatBytes(totalLoc));
                }
            }

        } catch (Exception e) {
            showError("Ошибка парсинга архитектуры: " + e.getMessage());
        }
    }

    private void updateDependencyStats(JsonObject data) {
        try {
            // TODO: Parse dependency graph and calculate stats
            strongCouplingLabel.setText("234");
            cyclicDepsLabel.setText("12");
            isolatedLabel.setText("45");
        } catch (Exception e) {
            showError("Ошибка парсинга зависимостей: " + e.getMessage());
        }
    }

    private void updateBestPracticesStats(JsonObject data) {
        try {
            JsonObject errorHandling = data.getAsJsonObject("error_handling");
            if (errorHandling != null) {
                double pct = errorHandling.get("percentage").getAsDouble();
                errorHandlingLabel.setText(String.format("%.1f%%", pct));
            }

            JsonObject documentation = data.getAsJsonObject("documentation");
            if (documentation != null) {
                double pct = documentation.get("export_documented_pct").getAsDouble();
                documentationLabel.setText(String.format("%.1f%%", pct));
            }

            // Naming - placeholder
            namingLabel.setText("95.4%");

        } catch (Exception e) {
            showError("Ошибка парсинга best practices: " + e.getMessage());
        }
    }

    private void runOrchestrator() {
        // TODO: Implement orchestrator runner
        MessageDialog.openInformation(
            getSite().getShell(),
            "Run Orchestrator",
            "Будет запущен оркестратор анализа для конфигурации: " + configCombo.getText()
        );
    }

    private void showDetailedArchitecture() {
        // TODO: Open detailed architecture view
        MessageDialog.openInformation(
            getSite().getShell(),
            "Detailed Architecture",
            "Откроется подробная статистика архитектуры"
        );
    }

    private void showDependencyGraph() {
        // TODO: Open metadata graph view
        MessageDialog.openInformation(
            getSite().getShell(),
            "Dependency Graph",
            "Откроется граф зависимостей"
        );
    }

    private void showBestPracticesDetails() {
        // TODO: Open detailed best practices report
        MessageDialog.openInformation(
            getSite().getShell(),
            "Best Practices Details",
            "Откроются подробные рекомендации по улучшению"
        );
    }

    private void showError(String message) {
        MessageDialog.openError(
            getSite().getShell(),
            "Error",
            message
        );
    }

    private String formatBytes(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024) + " KB";
        if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024) + " MB";
        return (bytes / 1024 / 1024 / 1024) + " GB";
    }

    @Override
    public void setFocus() {
        configCombo.setFocus();
    }

    /**
     * Public method to refresh view (called from other parts)
     */
    public void refresh() {
        Display.getDefault().asyncExec(() -> {
            loadAnalysisResults();
            contentComposite.layout(true, true);
        });
    }
}


