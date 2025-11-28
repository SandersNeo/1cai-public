/**
 * Интеграционная тестовая страница Project Manager
 * Объединяет все компоненты управления проектами в единый интерфейс
 * с real-time синхронизацией между компонентами
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { 
  Calendar, 
  AlertTriangle, 
  GitBranch, 
  FileText, 
  Activity, 
  Users, 
  Clock,
  TrendingUp,
  RefreshCw,
  Download,
  Settings
} from 'lucide-react';

// Импорт компонентов
import { GanttChart } from '../components/developer/GanttChart';
import { RiskManager } from '../components/developer/RiskManager';
import { ProjectIntegrations } from '../components/developer/ProjectIntegrations';
import { ReportsDashboard } from '../components/developer/ReportsDashboard';

// Импорт сервисов
import { GanttDiagramService } from '../services/gantt-diagram-service';
import { RiskAnalysisService } from '../services/risk-analysis-service';
import { TaskIntegrationService } from '../services/task-management-integration-service';
import { AutomatedReportingService } from '../services/automated-reporting-service';

// Импорт типов данных
import { ProjectTask, Resource, Milestone } from '../services/gantt-diagram-service';
import { RiskFactor, RiskAnalysisReport } from '../services/risk-analysis-service';
import { ProjectKPIs } from '../services/automated-reporting-service';

export interface ProjectData {
  id: string;
  name: string;
  description: string;
  startDate: Date;
  endDate: Date;
  status: 'planning' | 'active' | 'completed' | 'on_hold';
  progress: number;
  budget: number;
  spent: number;
  tasks: ProjectTask[];
  resources: Resource[];
  milestones: Milestone[];
  risks: RiskFactor[];
  kpis: ProjectKPIs;
  lastUpdated: Date;
}

const ProjectManagerPage: React.FC = () => {
  // Состояние активной вкладки
  const [activeTab, setActiveTab] = useState('gantt');
  
  // Состояние проекта
  const [project, setProject] = useState<ProjectData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');

  // Инициализация сервисов
  const ganttService = new GanttDiagramService();
  const riskService = new RiskAnalysisService();
  const integrationService = new TaskIntegrationService();
  const reportingService = new AutomatedReportingService();

  // Примерные данные проекта для демонстрации
  const generateSampleProject = useCallback((): ProjectData => {
    const now = new Date();
    const projectStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 дней назад
    const projectEnd = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000); // 60 дней в будущем

    const resources: Resource[] = [
      {
        id: 'res-1',
        name: 'Алексей Иванов',
        type: 'person',
        availability: 100,
        costPerDay: 8000,
        skills: ['1С разработка', 'SQL', 'Интеграции'],
        assignments: []
      },
      {
        id: 'res-2',
        name: 'Мария Петрова',
        type: 'person',
        availability: 80,
        costPerDay: 7500,
        skills: ['UI/UX', 'JavaScript', 'React'],
        assignments: []
      },
      {
        id: 'res-3',
        name: 'Дмитрий Сидоров',
        type: 'person',
        availability: 60,
        costPerDay: 9000,
        skills: ['Архитектура', 'DevOps', 'Безопасность'],
        assignments: []
      }
    ];

    const tasks: ProjectTask[] = [
      {
        id: 'task-1',
        name: 'Анализ требований и планирование',
        description: 'Сбор и анализ требований от заказчика, создание технического задания',
        startDate: new Date(projectStart.getTime() + 1 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectStart.getTime() + 7 * 24 * 60 * 60 * 1000),
        duration: 7,
        progress: 100,
        assignee: 'Алексей Иванов',
        priority: 'critical',
        status: 'completed',
        dependencies: [],
        resources: [],
        milestones: [],
        isCritical: true,
        isMilestone: false,
        color: '#22c55e'
      },
      {
        id: 'task-2',
        name: 'Проектирование архитектуры системы',
        description: 'Создание архитектуры 1С системы, схемы БД, API',
        startDate: new Date(projectStart.getTime() + 8 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectStart.getTime() + 14 * 24 * 60 * 60 * 1000),
        duration: 7,
        progress: 100,
        assignee: 'Дмитрий Сидоров',
        priority: 'critical',
        status: 'completed',
        dependencies: ['task-1'],
        resources: [],
        milestones: [],
        isCritical: true,
        isMilestone: false,
        color: '#22c55e'
      },
      {
        id: 'task-3',
        name: 'Разработка модуля учетной системы',
        description: 'Создание основных объектов метаданных 1С: справочники, документы, регистры',
        startDate: new Date(projectStart.getTime() + 15 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectStart.getTime() + 35 * 24 * 60 * 60 * 1000),
        duration: 21,
        progress: 85,
        assignee: 'Алексей Иванов',
        priority: 'high',
        status: 'in_progress',
        dependencies: ['task-2'],
        resources: [],
        milestones: [],
        isCritical: true,
        isMilestone: false,
        color: '#3b82f6'
      },
      {
        id: 'task-4',
        name: 'Разработка пользовательского интерфейса',
        description: 'Создание форм, отчетов, обработок в 1С',
        startDate: new Date(projectStart.getTime() + 20 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectStart.getTime() + 40 * 24 * 60 * 60 * 1000),
        duration: 21,
        progress: 60,
        assignee: 'Мария Петрова',
        priority: 'high',
        status: 'in_progress',
        dependencies: ['task-2'],
        resources: [],
        milestones: [],
        isCritical: false,
        isMilestone: false,
        color: '#3b82f6'
      },
      {
        id: 'task-5',
        name: 'Интеграция с внешними системами',
        description: 'Настройка обмена данными с CRM, банковскими системами',
        startDate: new Date(projectStart.getTime() + 36 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectStart.getTime() + 50 * 24 * 60 * 60 * 1000),
        duration: 15,
        progress: 30,
        assignee: 'Алексей Иванов',
        priority: 'medium',
        status: 'in_progress',
        dependencies: ['task-3'],
        resources: [],
        milestones: [],
        isCritical: false,
        isMilestone: false,
        color: '#f59e0b'
      },
      {
        id: 'task-6',
        name: 'Тестирование и отладка',
        description: 'Функциональное и интеграционное тестирование системы',
        startDate: new Date(projectStart.getTime() + 41 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectStart.getTime() + 55 * 24 * 60 * 60 * 1000),
        duration: 15,
        progress: 10,
        assignee: 'Дмитрий Сидоров',
        priority: 'high',
        status: 'in_progress',
        dependencies: ['task-4', 'task-5'],
        resources: [],
        milestones: [],
        isCritical: true,
        isMilestone: false,
        color: '#3b82f6'
      },
      {
        id: 'task-7',
        name: 'Внедрение и запуск',
        description: 'Развертывание системы в продуктивной среде, обучение пользователей',
        startDate: new Date(projectStart.getTime() + 56 * 24 * 60 * 60 * 1000),
        endDate: new Date(projectEnd.getTime()),
        duration: 5,
        progress: 0,
        assignee: 'Алексей Иванов',
        priority: 'critical',
        status: 'not_started',
        dependencies: ['task-6'],
        resources: [],
        milestones: [
          {
            id: 'milestone-1',
            name: 'Запуск в продуктив',
            date: projectEnd,
            description: 'Финальный запуск системы',
            isCompleted: false
          }
        ],
        isCritical: true,
        isMilestone: false,
        color: '#ef4444'
      }
    ];

    const milestones: Milestone[] = [
      {
        id: 'milestone-1',
        name: 'Техническое задание утверждено',
        date: new Date(projectStart.getTime() + 7 * 24 * 60 * 60 * 1000),
        description: 'Утверждение ТЗ заказчиком',
        isCompleted: true
      },
      {
        id: 'milestone-2',
        name: 'Архитектура согласована',
        date: new Date(projectStart.getTime() + 14 * 24 * 60 * 60 * 1000),
        description: 'Согласование архитектуры с командой',
        isCompleted: true
      },
      {
        id: 'milestone-3',
        name: 'Бета-версия готова',
        date: new Date(projectStart.getTime() + 45 * 24 * 60 * 60 * 1000),
        description: 'Готовность бета-версии для тестирования',
        isCompleted: false
      }
    ];

    // Назначение ресурсов на задачи
    tasks.forEach(task => {
      const resource = resources.find(r => r.assignee === task.assignee);
      if (resource) {
        resource.assignments.push({
          taskId: task.id,
          resourceId: resource.id,
          allocation: task.assignee === 'Дмитрий Сидоров' ? 60 : 100,
          startDate: task.startDate,
          endDate: task.endDate
        });
      }
    });

    return {
      id: 'project-1c-demo',
      name: 'Проект автоматизации учета для ООО "ДемоКомпани"',
      description: 'Внедрение системы автоматизированного учета на базе 1С:Предприятие 8.3',
      startDate: projectStart,
      endDate: projectEnd,
      status: 'active',
      progress: 65,
      budget: 500000,
      spent: 325000,
      tasks,
      resources,
      milestones,
      risks: [],
      kpis: {
        schedulePerformanceIndex: 0.95,
        costPerformanceIndex: 1.1,
        velocity: 0.8,
        defectRate: 2.1,
        testCoverage: 78,
        codeQuality: 85,
        burndownRate: 1.2,
        resourceUtilization: 88,
        scopeCreep: 0.05,
        stakeholderSatisfaction: 8.5,
        teamMorale: 7.8,
        technicalDebt: 12,
        documentationCompleteness: 72,
        riskExposure: 15,
        roi: 1.25
      },
      lastUpdated: new Date()
    };
  }, []);

  // Инициализация проекта
  useEffect(() => {
    const initProject = async () => {
      setIsLoading(true);
      try {
        const sampleProject = generateSampleProject();
        setProject(sampleProject);
        
        // Генерация рисков на основе задач проекта
        const riskReport: RiskAnalysisReport = await riskService.analyzeProjectRisks(sampleProject);
        setProject(prev => prev ? { ...prev, risks: riskReport.risks } : null);
        
      } catch (error) {
        console.error('Ошибка инициализации проекта:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initProject();
  }, [generateSampleProject]);

  // Функция синхронизации между компонентами
  const syncProjectData = useCallback(async () => {
    if (!project) return;
    
    setIsSyncing(true);
    setSyncStatus('syncing');
    
    try {
      // 1. Обновляем риски на основе изменений в задачах
      const riskReport: RiskAnalysisReport = await riskService.analyzeProjectRisks(project);
      
      // 2. Пересчитываем KPI на основе обновленных данных
      const kpis: ProjectKPIs = reportingService.calculateKPIs(project);
      
      // 3. Обновляем критический путь в Gantt
      // Создаем массив зависимостей из задач
      const dependencies: any[] = [];
      project.tasks.forEach(task => {
        task.dependencies.forEach(depId => {
          dependencies.push({
            fromTaskId: depId,
            toTaskId: task.id,
            type: 'finish_to_start' as const,
            lag: 0
          });
        });
      });
      
      const criticalPath = ganttService.calculateCriticalPath(project, dependencies);
      const updatedTasks = project.tasks.map(task => ({
        ...task,
        isCritical: criticalPath.some(cp => cp.taskId === task.id && cp.isCritical)
      }));
      
      // 4. Обновляем ресурсы и их загрузку
      const updatedResources = project.resources.map(resource => {
        const assignments = resource.assignments || [];
        const totalAllocation = assignments.reduce((sum, assignment) => {
          const task = project.tasks.find(t => t.id === assignment.taskId);
          if (task && task.status !== 'completed') {
            return sum + assignment.allocation;
          }
          return sum;
        }, 0);
        
        return {
          ...resource,
          availability: Math.max(0, 100 - totalAllocation)
        };
      });
      
      // Применяем все изменения
      setProject(prev => prev ? {
        ...prev,
        tasks: updatedTasks,
        risks: riskReport.risks,
        kpis,
        resources: updatedResources,
        lastUpdated: new Date()
      } : null);
      
      setSyncStatus('success');
      setLastSync(new Date());
      
    } catch (error) {
      console.error('Ошибка синхронизации:', error);
      setSyncStatus('error');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  }, [project, ganttService, riskService, reportingService]);

  // Автоматическая синхронизация при изменении данных
  useEffect(() => {
    if (project && !isLoading) {
      const timeoutId = setTimeout(() => {
        syncProjectData();
      }, 2000); // Задержка 2 секунды для избежания частых обновлений
      
      return () => clearTimeout(timeoutId);
    }
  }, [project?.tasks, project?.progress, syncProjectData, isLoading]);

  // Обработчики событий от компонентов
  const handleTaskUpdate = useCallback((updatedTask: ProjectTask) => {
    if (!project) return;
    
    setProject(prev => prev ? {
      ...prev,
      tasks: prev.tasks.map(task => 
        task.id === updatedTask.id ? updatedTask : task
      ),
      lastUpdated: new Date()
    } : null);
  }, [project]);

  const handleRiskUpdate = useCallback((updatedRisk: RiskFactor) => {
    if (!project) return;
    
    setProject(prev => prev ? {
      ...prev,
      risks: prev.risks.map(risk => 
        risk.id === updatedRisk.id ? updatedRisk : risk
      ),
      lastUpdated: new Date()
    } : null);
  }, [project]);

  const handleResourceUpdate = useCallback((updatedResource: Resource) => {
    if (!project) return;
    
    setProject(prev => prev ? {
      ...prev,
      resources: prev.resources.map(resource => 
        resource.id === updatedResource.id ? updatedResource : resource
      ),
      lastUpdated: new Date()
    } : null);
  }, [project]);

  // Статистика проекта
  const getProjectStats = () => {
    if (!project) return null;
    
    const completedTasks = project.tasks.filter(task => task.status === 'completed').length;
    const totalTasks = project.tasks.length;
    const criticalRisks = project.risks.filter(risk => risk.severity === 'critical' || risk.severity === 'high').length;
    const overdueTasks = project.tasks.filter(task => 
      task.status !== 'completed' && new Date(task.endDate) < new Date()
    ).length;
    
    return {
      completedTasks,
      totalTasks,
      progressPercent: (completedTasks / totalTasks) * 100,
      criticalRisks,
      overdueTasks,
      budgetUtilization: (project.spent / project.budget) * 100
    };
  };

  const stats = getProjectStats();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-lg text-gray-600">Загрузка проекта...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-center text-red-600">Ошибка загрузки</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center">Не удалось загрузить данные проекта</p>
            <Button 
              className="w-full mt-4" 
              onClick={() => window.location.reload()}
            >
              Попробовать снова
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Шапка с общей информацией */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
                  <p className="text-sm text-gray-500 mt-1">{project.description}</p>
                </div>
                <Badge 
                  variant={project.status === 'active' ? 'default' : 'secondary'}
                  className="ml-4"
                >
                  {project.status === 'active' ? 'Активный' : 
                   project.status === 'completed' ? 'Завершен' :
                   project.status === 'planning' ? 'Планирование' : 'Приостановлен'}
                </Badge>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    Последнее обновление: {project.lastUpdated.toLocaleString('ru-RU')}
                  </p>
                  {lastSync && (
                    <p className="text-xs text-gray-400">
                      Синхронизация: {lastSync.toLocaleTimeString('ru-RU')}
                    </p>
                  )}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={syncProjectData}
                  disabled={isSyncing}
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className={`h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
                  <span>Синхронизация</span>
                </Button>
              </div>
            </div>
            
            {/* Статистика проекта */}
            {stats && (
              <div className="mt-6 grid grid-cols-2 md:grid-cols-6 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <Calendar className="h-5 w-5 text-blue-600 mr-2" />
                    <div>
                      <p className="text-xs text-gray-500">Прогресс</p>
                      <p className="text-lg font-semibold">{Math.round(stats.progressPercent)}%</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <Activity className="h-5 w-5 text-green-600 mr-2" />
                    <div>
                      <p className="text-xs text-gray-500">Задачи</p>
                      <p className="text-lg font-semibold">{stats.completedTasks}/{stats.totalTasks}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                    <div>
                      <p className="text-xs text-gray-500">Риски</p>
                      <p className="text-lg font-semibold">{stats.criticalRisks}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <Clock className="h-5 w-5 text-orange-600 mr-2" />
                    <div>
                      <p className="text-xs text-gray-500">Просрочено</p>
                      <p className="text-lg font-semibold">{stats.overdueTasks}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <TrendingUp className="h-5 w-5 text-purple-600 mr-2" />
                    <div>
                      <p className="text-xs text-gray-500">SPI</p>
                      <p className="text-lg font-semibold">{project.kpis.schedulePerformanceIndex.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <Users className="h-5 w-5 text-indigo-600 mr-2" />
                    <div>
                      <p className="text-xs text-gray-500">Команда</p>
                      <p className="text-lg font-semibold">{project.resources.length}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Прогресс бар */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-sm">
                <span>Общий прогресс проекта</span>
                <span>{project.progress}%</span>
              </div>
              <Progress value={project.progress} className="mt-2" />
            </div>
            
            {/* Статус синхронизации */}
            {syncStatus !== 'idle' && (
              <Alert className={`mt-4 ${syncStatus === 'success' ? 'border-green-200 bg-green-50' : 
                syncStatus === 'error' ? 'border-red-200 bg-red-50' : 'border-blue-200 bg-blue-50'}`}>
                <RefreshCw className={`h-4 w-4 ${syncStatus === 'syncing' ? 'animate-spin' : ''}`} />
                <AlertDescription>
                  {syncStatus === 'syncing' && 'Синхронизация данных между компонентами...'}
                  {syncStatus === 'success' && 'Синхронизация завершена успешно'}
                  {syncStatus === 'error' && 'Ошибка синхронизации данных'}
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>
      </div>

      {/* Основной контент с табами */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="gantt" className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>Gantt Диаграмма</span>
            </TabsTrigger>
            <TabsTrigger value="risks" className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Анализ Рисков</span>
            </TabsTrigger>
            <TabsTrigger value="integrations" className="flex items-center space-x-2">
              <GitBranch className="h-4 w-4" />
              <span>Интеграции</span>
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span>Отчеты</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="gantt" className="mt-6">
            <GanttChart 
              project={{
                tasks: project.tasks,
                resources: project.resources,
                milestones: project.milestones,
                criticalPath: project.tasks.filter(t => t.isCritical).map(t => t.id)
              }}
              onTaskUpdate={handleTaskUpdate}
              onResourceUpdate={handleResourceUpdate}
            />
          </TabsContent>

          <TabsContent value="risks" className="mt-6">
            <RiskManager 
              projectId={project.id}
              risks={project.risks}
              tasks={project.tasks}
              onRiskUpdate={handleRiskUpdate}
            />
          </TabsContent>

          <TabsContent value="integrations" className="mt-6">
            <ProjectIntegrations 
              projectId={project.id}
              project={project}
            />
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            <ReportsDashboard 
              projectId={project.id}
              kpis={project.kpis}
              tasks={project.tasks}
              risks={project.risks}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Футер с дополнительной информацией */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center space-x-4">
              <span>1C AI Project Manager Demo</span>
              <span>•</span>
              <span>Бюджет: {project.budget.toLocaleString('ru-RU')} ₽</span>
              <span>•</span>
              <span>Потрачено: {project.spent.toLocaleString('ru-RU')} ₽</span>
              <span>•</span>
              <span>ROI: {(project.kpis.roi * 100).toFixed(0)}%</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Экспорт
              </Button>
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Настройки
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectManagerPage;