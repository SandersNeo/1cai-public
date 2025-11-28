import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { 
  Plug, 
  Plus, 
  Search, 
  Filter, 
  Star, 
  Download, 
  Settings, 
  Trash2, 
  ExternalLink,
  Shield,
  Users,
  Calendar,
  Eye,
  EyeOff,
  RefreshCw
} from 'lucide-react';
import { PluginRegistryService, PluginRegistryEntry, PluginSearchQuery } from '@/services/plugin-registry-service';

interface PluginMarketplaceProps {
  registryService: PluginRegistryService;
  onPluginSelect?: (plugin: PluginRegistryEntry) => void;
}

const PluginMarketplace: React.FC<PluginMarketplaceProps> = ({
  registryService,
  onPluginSelect
}) => {
  const [plugins, setPlugins] = useState<PluginRegistryEntry[]>([]);
  const [searchResults, setSearchResults] = useState<PluginRegistryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSort, setSelectedSort] = useState<'name' | 'rating' | 'downloads' | 'updated' | 'installs'>('rating');
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadPlugins();
  }, []);

  useEffect(() => {
    performSearch();
  }, [searchQuery, selectedCategory, selectedSort, activeTab]);

  const loadPlugins = async () => {
    try {
      setLoading(true);
      const allPlugins = registryService.getAllPlugins();
      setPlugins(allPlugins);
    } catch (error) {
      console.error('Failed to load plugins:', error);
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async () => {
    try {
      const query: PluginSearchQuery = {
        query: searchQuery || undefined,
        category: selectedCategory === 'all' ? undefined : selectedCategory as any,
        sortBy: selectedSort,
        sortOrder: 'desc',
        limit: 50
      };

      if (activeTab === 'featured') {
        query.featured = true;
      } else if (activeTab === 'popular') {
        // Already sorted by downloads in the service
        query.sortBy = 'downloads';
      }

      const results = await registryService.searchPlugins(query);
      setSearchResults(results.plugins);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    }
  };

  const getDisplayedPlugins = (): PluginRegistryEntry[] => {
    switch (activeTab) {
      case 'featured':
        return registryService.getFeaturedPlugins();
      case 'popular':
        return registryService.getPopularPlugins(20);
      case 'top-rated':
        return registryService.getTopRatedPlugins(20);
      case 'all':
      default:
        return searchResults;
    }
  };

  const getCategoryDisplayName = (category: string): string => {
    const names: Record<string, string> = {
      'development': 'Разработка',
      'analytics': 'Аналитика',
      'integration': 'Интеграция',
      'productivity': 'Продуктивность',
      'visualization': 'Визуализация',
      'automation': 'Автоматизация',
      'custom': 'Пользовательские',
      'theme': 'Темы',
      'utility': 'Утилиты'
    };
    return names[category] || category;
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const PluginCard: React.FC<{ plugin: PluginRegistryEntry }> = ({ plugin }) => (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => onPluginSelect?.(plugin)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Plug className="h-5 w-5 text-primary" />
            <div>
              <CardTitle className="text-lg">{plugin.manifest.name}</CardTitle>
              <p className="text-sm text-muted-foreground">v{plugin.manifest.version}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {plugin.verified && (
              <Badge variant="default" className="text-xs">
                <Shield className="h-3 w-3 mr-1" />
                Проверен
              </Badge>
            )}
            {plugin.marketplace?.featured && (
              <Badge variant="secondary" className="text-xs">
                <Star className="h-3 w-3 mr-1" />
                Рекомендуем
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {plugin.manifest.description}
        </p>
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            <span>{plugin.rating.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Download className="h-4 w-4" />
            <span>{formatNumber(plugin.downloadCount)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            <span>{formatNumber(plugin.installCount)}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {getCategoryDisplayName(plugin.manifest.category)}
            </Badge>
            <span className="text-xs text-muted-foreground">{plugin.manifest.author}</span>
          </div>
          <span className="text-xs text-muted-foreground">
            {formatDate(plugin.lastUpdated)}
          </span>
        </div>

        <div className="flex gap-2">
          <Button size="sm" className="flex-1">
            <Download className="h-4 w-4 mr-2" />
            Установить
          </Button>
          <Button size="sm" variant="outline">
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-6 w-6 animate-spin" />
        <span className="ml-2">Загрузка плагинов...</span>
      </div>
    );
  }

  return (
    <div className="plugin-marketplace space-y-6">
      {/* Заголовок и поиск */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Plug className="h-6 w-6" />
            Маркетплейс плагинов
          </h2>
          <p className="text-muted-foreground">
            Расширьте возможности агентной системы с помощью плагинов
          </p>
        </div>
      </div>

      {/* Фильтры и поиск */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Поиск плагинов..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все категории</SelectItem>
                <SelectItem value="development">Разработка</SelectItem>
                <SelectItem value="analytics">Аналитика</SelectItem>
                <SelectItem value="integration">Интеграция</SelectItem>
                <SelectItem value="productivity">Продуктивность</SelectItem>
                <SelectItem value="visualization">Визуализация</SelectItem>
                <SelectItem value="automation">Автоматизация</SelectItem>
                <SelectItem value="theme">Темы</SelectItem>
                <SelectItem value="utility">Утилиты</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSort} onValueChange={(value: any) => setSelectedSort(value)}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rating">По рейтингу</SelectItem>
                <SelectItem value="downloads">По загрузкам</SelectItem>
                <SelectItem value="installs">По установкам</SelectItem>
                <SelectItem value="updated">По обновлению</SelectItem>
                <SelectItem value="name">По названию</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Вкладки */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">Все плагины</TabsTrigger>
          <TabsTrigger value="featured">Рекомендуемые</TabsTrigger>
          <TabsTrigger value="popular">Популярные</TabsTrigger>
          <TabsTrigger value="top-rated">Высокий рейтинг</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {getDisplayedPlugins().map(plugin => (
              <PluginCard key={plugin.id} plugin={plugin} />
            ))}
          </div>
          {getDisplayedPlugins().length === 0 && (
            <div className="text-center py-12">
              <Plug className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Плагины не найдены</h3>
              <p className="text-muted-foreground">
                Попробуйте изменить параметры поиска или фильтры
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="featured" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {getDisplayedPlugins().map(plugin => (
              <PluginCard key={plugin.id} plugin={plugin} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="popular" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {getDisplayedPlugins().map(plugin => (
              <PluginCard key={plugin.id} plugin={plugin} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="top-rated" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {getDisplayedPlugins().map(plugin => (
              <PluginCard key={plugin.id} plugin={plugin} />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PluginMarketplace;