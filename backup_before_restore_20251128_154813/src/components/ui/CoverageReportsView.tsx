import React, { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  FileText,
  Download,
  Filter,
  Search,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  GitBranch,
  Calendar,
  Activity
} from 'lucide-react';

interface CoverageFile {
  name: string;
  path: string;
  type: 'component' | 'service' | 'util' | 'config';
  statements: { covered: number; total: number; percentage: number };
  branches: { covered: number; total: number; percentage: number };
  functions: { covered: number; total: number; percentage: number };
  lines: { covered: number; total: number; percentage: number };
  lastModified: Date;
  status: 'good' | 'warning' | 'critical';
}

interface CoverageTrend {
  date: string;
  statements: number;
  branches: number;
  functions: number;
  lines: number;
}

interface CoverageProject {
  id: string;
  name: string;
  branch: string;
  commitHash: string;
  buildDate: Date;
  overallCoverage: {
    statements: number;
    branches: number;
    functions: number;
    lines: number;
  };
  totalFiles: number;
  coveredFiles: number;
  trend: CoverageTrend[];
  files: CoverageFile[];
  targets: {
    statements: number;
    branches: number;
    functions: number;
    lines: number;
  };
}

const CoverageReportsView: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<string>('main');
  const [filterType, setFilterType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  // Генерируем тестовые данные покрытия
  const projects: CoverageProject[] = useMemo(() => {
    const fileTypes = ['component', 'service', 'util', 'config'] as const;
    const generateFiles = (count: number): CoverageFile[] => {
      return Array.from({ length: count }, (_, i) => {
        const totalStatements = Math.floor(Math.random() * 500) + 50;
        const coveredStatements = Math.floor(totalStatements * (0.6 + Math.random() * 0.35));
        const totalBranches = Math.floor(Math.random() * 100) + 10;
        const coveredBranches = Math.floor(totalBranches * (0.55 + Math.random() * 0.4));
        const totalFunctions = Math.floor(Math.random() * 50) + 5;
        const coveredFunctions = Math.floor(totalFunctions * (0.7 + Math.random() * 0.25));
        const totalLines = totalStatements;
        const coveredLines = Math.floor(totalLines * (0.65 + Math.random() * 0.3));

        const statementPercentage = (coveredStatements / totalStatements) * 100;
        const status = statementPercentage >= 80 ? 'good' : statementPercentage >= 60 ? 'warning' : 'critical';

        return {
          name: `File${i + 1}.ts`,
          path: `src/${fileTypes[Math.floor(Math.random() * fileTypes.length)]}/file${i + 1}.ts`,
          type: fileTypes[Math.floor(Math.random() * fileTypes.length)],
          statements: {
            covered: coveredStatements,
            total: totalStatements,
            percentage: statementPercentage
          },
          branches: {
            covered: coveredBranches,
            total: totalBranches,
            percentage: (coveredBranches / totalBranches) * 100
          },
          functions: {
            covered: coveredFunctions,
            total: totalFunctions,
            percentage: (coveredFunctions / totalFunctions) * 100
          },
          lines: {
            covered: coveredLines,
            total: totalLines,
            percentage: (coveredLines / totalLines) * 100
          },
          lastModified: new Date(Date.now() - Math.random() * 86400000 * 7),
          status
        };
      });
    };

    const generateTrends = (): CoverageTrend[] => {
      return Array.from({ length: 14 }, (_, i) => ({
        date: new Date(Date.now() - (13 - i) * 86400000).toISOString().split('T')[0],
        statements: 60 + Math.random() * 30,
        branches: 50 + Math.random() * 35,
        functions: 65 + Math.random() * 25,
        lines: 55 + Math.random() * 35
      }));
    };

    const files = generateFiles(25);
    const coveredFiles = files.filter(f => f.statements.percentage >= 60).length;

    return [{
      id: 'main',
      name: '1C AI Agent System',
      branch: 'main',
      commitHash: 'a1b2c3d',
      buildDate: new Date(),
      overallCoverage: {
        statements: 78.5,
        branches: 65.2,
        functions: 82.1,
        lines: 76.9
      },
      totalFiles: files.length,
      coveredFiles,
      trend: generateTrends(),
      files,
      targets: {
        statements: 80,
        branches: 70,
        functions: 85,
        lines: 80
      }
    }];
  }, []);

  // Фильтрация файлов
  const filteredFiles = useMemo(() => {
    const project = projects.find(p => p.id === selectedProject);
    if (!project) return [];

    return project.files.filter(file => {
      const matchesType = filterType === 'all' || file.type === filterType;
      const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           file.path.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [projects, selectedProject, filterType, searchTerm]);

  // Статистика проекта
  const projectData = useMemo(() => {
    const project = projects.find(p => p.id === selectedProject);
    if (!project) return null;

    const overallTarget = (project.targets.statements + project.targets.branches + 
                          project.targets.functions + project.targets.lines) / 4;
    const overallCurrent = (project.overallCoverage.statements + project.overallCoverage.branches +
                           project.overallCoverage.functions + project.overallCoverage.lines) / 4;
    const trendDirection = project.trend[project.trend.length - 1].statements - project.trend[0].statements;

    return {
      ...project,
      overallTarget,
      overallCurrent,
      trendDirection
    };
  }, [projects, selectedProject]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'component': return 'bg-blue-100 text-blue-800';
      case 'service': return 'bg-green-100 text-green-800';
      case 'util': return 'bg-purple-100 text-purple-800';
      case 'config': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const exportReport = (format: 'html' | 'json' | 'lcov') => {
    console.log(`Экспорт отчета покрытия в формате ${format}`);
    // Здесь будет логика экспорта
  };

  const selectedFileData = projectData?.files.find(f => f.path === selectedFile);

  if (!projectData) {
    return <div>Проект не найден</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Отчеты покрытия кода</h1>
              <p className="text-gray-600 mt-1">Анализ тестового покрытия и качества кода</p>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm" onClick={() => exportReport('html')}>
                <FileText className="h-4 w-4 mr-2" />
                HTML
              </Button>
              <Button variant="outline" size="sm" onClick={() => exportReport('lcov')}>
                <Download className="h-4 w-4 mr-2" />
                LCOV
              </Button>
            </div>
          </div>
        </div>

        {/* Общая статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Общее покрытие</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.overallCurrent.toFixed(1)}%</div>
              <div className="flex items-center space-x-2 mt-2">
                <Progress value={projectData.overallCurrent} className="flex-1 h-2" />
                {projectData.overallCurrent >= projectData.overallTarget ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Цель: {projectData.overallTarget.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Покрытые файлы</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.coveredFiles}</div>
              <p className="text-xs text-muted-foreground">
                из {projectData.totalFiles} файлов
              </p>
              <Progress 
                value={(projectData.coveredFiles / projectData.totalFiles) * 100} 
                className="mt-2 h-2" 
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Тренд</CardTitle>
              {projectData.trendDirection > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : projectData.trendDirection < 0 ? (
                <TrendingDown className="h-4 w-4 text-red-500" />
              ) : (
                <Activity className="h-4 w-4 text-gray-400" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {projectData.trendDirection > 0 ? '+' : ''}{projectData.trendDirection.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                за последние 2 недели
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Ветка</CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.branch}</div>
              <p className="text-xs text-muted-foreground">
                {projectData.commitHash}
              </p>
              <div className="flex items-center space-x-1 mt-2">
                <Calendar className="h-3 w-3 text-gray-400" />
                <span className="text-xs text-gray-500">
                  {projectData.buildDate.toLocaleDateString('ru-RU')}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Детальная статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Операторы</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.overallCoverage.statements.toFixed(1)}%</div>
              <Progress value={projectData.overallCoverage.statements} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                Цель: {projectData.targets.statements}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Ветки</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.overallCoverage.branches.toFixed(1)}%</div>
              <Progress value={projectData.overallCoverage.branches} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                Цель: {projectData.targets.branches}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Функции</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.overallCoverage.functions.toFixed(1)}%</div>
              <Progress value={projectData.overallCoverage.functions} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                Цель: {projectData.targets.functions}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Строки</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectData.overallCoverage.lines.toFixed(1)}%</div>
              <Progress value={projectData.overallCoverage.lines} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                Цель: {projectData.targets.lines}%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Фильтры и поиск */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Поиск файлов..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-64"
                />
              </div>

              <select 
                value={filterType} 
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="all">Все типы</option>
                <option value="component">Компоненты</option>
                <option value="service">Сервисы</option>
                <option value="util">Утилиты</option>
                <option value="config">Конфиги</option>
              </select>

              <div className="ml-auto text-sm text-gray-600">
                Показано {filteredFiles.length} из {projectData.files.length} файлов
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Основное содержимое */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Таблица файлов */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Файлы проекта</CardTitle>
                <CardDescription>
                  Покрытие по файлам ({filteredFiles.length} файлов)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Файл</TableHead>
                      <TableHead>Тип</TableHead>
                      <TableHead>Статус</TableHead>
                      <TableHead>Операторы</TableHead>
                      <TableHead>Ветки</TableHead>
                      <TableHead>Функции</TableHead>
                      <TableHead>Строки</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredFiles.map((file) => (
                      <TableRow 
                        key={file.path}
                        className={`cursor-pointer hover:bg-gray-50 ${selectedFile === file.path ? 'bg-blue-50' : ''}`}
                        onClick={() => setSelectedFile(file.path)}
                      >
                        <TableCell>
                          <div>
                            <div className="font-medium">{file.name}</div>
                            <div className="text-sm text-gray-500">{file.path}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getTypeColor(file.type)}>
                            {file.type.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(file.status)}
                            <span className="capitalize">{file.status}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>{file.statements.percentage.toFixed(1)}%</div>
                            <div className="text-gray-500">
                              {file.statements.covered}/{file.statements.total}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>{file.branches.percentage.toFixed(1)}%</div>
                            <div className="text-gray-500">
                              {file.branches.covered}/{file.branches.total}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>{file.functions.percentage.toFixed(1)}%</div>
                            <div className="text-gray-500">
                              {file.functions.covered}/{file.functions.total}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>{file.lines.percentage.toFixed(1)}%</div>
                            <div className="text-gray-500">
                              {file.lines.covered}/{file.lines.total}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-3 w-3" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          {/* Панель деталей файла */}
          <div className="lg:col-span-1">
            {selectedFileData ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Детали файла</CardTitle>
                  <CardDescription>
                    {selectedFileData.name}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Информация</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Путь:</span>
                        <span className="font-mono text-xs">{selectedFileData.path}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Тип:</span>
                        <Badge className={getTypeColor(selectedFileData.type)}>
                          {selectedFileData.type}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Статус:</span>
                        <div className="flex items-center space-x-1">
                          {getStatusIcon(selectedFileData.status)}
                          <span className="capitalize">{selectedFileData.status}</span>
                        </div>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Изменен:</span>
                        <span>{selectedFileData.lastModified.toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Метрики покрытия</h4>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Операторы</span>
                          <span className="font-medium">{selectedFileData.statements.percentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={selectedFileData.statements.percentage} className="h-2" />
                        <div className="text-xs text-gray-500 mt-1">
                          {selectedFileData.statements.covered} из {selectedFileData.statements.total}
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Ветки</span>
                          <span className="font-medium">{selectedFileData.branches.percentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={selectedFileData.branches.percentage} className="h-2" />
                        <div className="text-xs text-gray-500 mt-1">
                          {selectedFileData.branches.covered} из {selectedFileData.branches.total}
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Функции</span>
                          <span className="font-medium">{selectedFileData.functions.percentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={selectedFileData.functions.percentage} className="h-2" />
                        <div className="text-xs text-gray-500 mt-1">
                          {selectedFileData.functions.covered} из {selectedFileData.functions.total}
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Строки</span>
                          <span className="font-medium">{selectedFileData.lines.percentage.toFixed(1)}%</span>
                        </div>
                        <Progress value={selectedFileData.lines.percentage} className="h-2" />
                        <div className="text-xs text-gray-500 mt-1">
                          {selectedFileData.lines.covered} из {selectedFileData.lines.total}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Действия</h4>
                    <div className="space-y-2">
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="h-3 w-3 mr-2" />
                        Просмотр кода
                      </Button>
                      <Button variant="outline" size="sm" className="w-full">
                        <Download className="h-3 w-3 mr-2" />
                        Скачать отчет
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Выберите файл для просмотра деталей</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoverageReportsView;
