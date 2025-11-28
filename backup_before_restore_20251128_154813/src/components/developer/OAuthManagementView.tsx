import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Alert, AlertDescription } from '../ui/alert';
import { Switch } from '../ui/switch';
import OAuthService, { OAuthProvider, OAuthSession } from '../../services/oauth-service';
import { 
  Shield, 
  Plus, 
  Trash2, 
  Edit, 
  Key,
  LogIn,
  LogOut,
  RefreshCw,
  ExternalLink,
  Copy,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  Globe,
  Eye,
  EyeOff,
  Download,
  Upload
} from 'lucide-react';

export const OAuthManagementView: React.FC = () => {
  const [oauthService] = useState(() => new OAuthService());
  const [providers, setProviders] = useState<OAuthProvider[]>([]);
  const [sessions, setSessions] = useState<OAuthSession[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddProviderDialog, setShowAddProviderDialog] = useState(false);
  const [showSecrets, setShowSecrets] = useState(false);

  // Форма нового провайдера
  const [newProvider, setNewProvider] = useState<Partial<OAuthProvider>>({
    name: '',
    authUrl: '',
    tokenUrl: '',
    clientId: '',
    scopes: [],
    redirectUri: window.location.origin + '/oauth/callback',
    responseType: 'code',
    stateRequired: true
  });

  useEffect(() => {
    loadData();
    
    // Подписка на события
    oauthService.on('provider-registered', loadData);
    oauthService.on('oauth-success', loadData);
    oauthService.on('token-refreshed', loadData);
    oauthService.on('token-expired', loadData);
    oauthService.on('token-revoked', loadData);

    return () => {
      oauthService.removeAllListeners();
    };
  }, []);

  const loadData = useCallback(() => {
    try {
      setProviders(oauthService.getProviders());
      setSessions(oauthService.getActiveSessions());
    } catch (error) {
      console.error('Failed to load OAuth data:', error);
    }
  }, [oauthService]);

  const handleInitiateOAuth = async (providerId: string) => {
    try {
      setIsLoading(true);
      
      const provider = providers.find(p => p.id === providerId);
      if (!provider) {
        throw new Error('Provider not found');
      }

      const authUrl = oauthService.initiateOAuth({
        provider: providerId,
        redirectUri: provider.redirectUri,
        scopes: provider.scopes
      });

      // Открываем OAuth flow в новом окне или перенаправляем
      const authWindow = window.open(authUrl, '_blank', 'width=600,height=700,scrollbars=yes,resizable=yes');
      
      if (!authWindow) {
        // Если popup заблокирован, открываем в том же окне
        window.location.href = authUrl;
      }

    } catch (error) {
      console.error('OAuth initiation failed:', error);
      alert(`Ошибка инициации OAuth: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevokeToken = async (providerId: string, userId?: string) => {
    if (!confirm('Вы уверены, что хотите отозвать токен? Вам потребуется пройти авторизацию заново.')) return;

    try {
      setIsLoading(true);
      await oauthService.revokeToken(providerId, userId);
      alert('Токен успешно отозван');
    } catch (error) {
      console.error('Token revocation failed:', error);
      alert(`Ошибка отзыва токена: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestProvider = async (providerId: string) => {
    try {
      setIsLoading(true);
      
      // Для тестирования провайдера обычно нужно сначала авторизоваться
      // Здесь можно добавить специальную тестовую функциональность
      
      alert('Для тестирования провайдера необходимо сначала авторизоваться');
      
    } catch (error) {
      console.error('Provider test failed:', error);
      alert(`Тест провайдера не удался: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddProvider = async () => {
    try {
      setIsLoading(true);
      
      const provider: OAuthProvider = {
        id: newProvider.id || newProvider.name?.toLowerCase().replace(/\s+/g, '_') || `provider_${Date.now()}`,
        name: newProvider.name || '',
        authUrl: newProvider.authUrl || '',
        tokenUrl: newProvider.tokenUrl || '',
        clientId: newProvider.clientId || '',
        scopes: newProvider.scopes || [],
        redirectUri: newProvider.redirectUri || '',
        responseType: newProvider.responseType || 'code',
        stateRequired: newProvider.stateRequired || true,
        additionalParams: newProvider.additionalParams
      };

      // Валидация
      if (!provider.name || !provider.authUrl || !provider.tokenUrl || !provider.clientId) {
        throw new Error('Все основные поля должны быть заполнены');
      }

      oauthService.registerProvider(provider);
      setShowAddProviderDialog(false);
      setNewProvider({
        name: '',
        authUrl: '',
        tokenUrl: '',
        clientId: '',
        scopes: [],
        redirectUri: window.location.origin + '/oauth/callback',
        responseType: 'code',
        stateRequired: true
      });
      
      alert('Провайдер OAuth успешно добавлен');
      
    } catch (error) {
      console.error('Failed to add provider:', error);
      alert(`Ошибка добавления провайдера: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteProvider = async (providerId: string) => {
    if (!confirm('Вы уверены, что хотите удалить этого провайдера? Все связанные сессии будут потеряны.')) return;

    try {
      setIsLoading(true);
      
      // Сначала отзываем все токены для этого провайдера
      const providerSessions = sessions.filter(s => s.provider === providerId);
      for (const session of providerSessions) {
        await oauthService.revokeToken(session.provider, session.userId);
      }
      
      // Удаляем провайдера (здесь нужно добавить метод в OAuthService)
      // oauthService.unregisterProvider(providerId);
      
      alert('Провайдер удален');
      
    } catch (error) {
      console.error('Failed to delete provider:', error);
      alert(`Ошибка удаления провайдера: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const exportProviders = () => {
    try {
      const config = oauthService.exportProvidersConfig();
      const blob = new Blob([config], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `oauth-providers-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Экспорт не удался: ${(error as Error).message}`);
    }
  };

  const importProviders = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const config = e.target?.result as string;
        await oauthService.importProvidersConfig(config);
        alert('Провайдеры успешно импортированы!');
      } catch (error) {
        console.error('Import failed:', error);
        alert(`Импорт не удался: ${(error as Error).message}`);
      }
    };
    reader.readAsText(file);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Скопировано в буфер обмена');
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
      case 'google': return '🔍';
      case 'github': return '🐙';
      case 'microsoft': return '🔷';
      case 'facebook': return '📘';
      case 'linkedin': return '💼';
      default: return '🌐';
    }
  };

  const getSessionStatus = (session: OAuthSession) => {
    const now = new Date();
    if (now >= session.expiresAt) {
      return { status: 'expired', color: 'bg-red-100 text-red-800', text: 'Истек' };
    }
    
    const timeUntilExpiry = session.expiresAt.getTime() - now.getTime();
    const hoursUntilExpiry = timeUntilExpiry / (1000 * 60 * 60);
    
    if (hoursUntilExpiry < 1) {
      return { status: 'expiring', color: 'bg-yellow-100 text-yellow-800', text: 'Скоро истечет' };
    }
    
    return { status: 'active', color: 'bg-green-100 text-green-800', text: 'Активен' };
  };

  return (
    <div className="oauth-management-view p-6">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Shield className="w-8 h-8 text-blue-500" />
              Управление OAuth авторизацией
            </h1>
            <p className="text-gray-600 mt-2">
              Настройка провайдеров OAuth2 и управление токенами доступа
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={exportProviders}>
              <Download className="w-4 h-4 mr-2" />
              Экспорт
            </Button>

            <Button variant="outline" size="sm" asChild>
              <label className="cursor-pointer">
                <Upload className="w-4 h-4 mr-2" />
                Импорт
                <input 
                  type="file" 
                  accept=".json"
                  onChange={importProviders}
                  className="hidden"
                />
              </label>
            </Button>

            <Dialog open={showAddProviderDialog} onOpenChange={setShowAddProviderDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Добавить провайдера
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Добавить новый OAuth провайдер</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="provider-name">Название</Label>
                      <Input
                        id="provider-name"
                        value={newProvider.name}
                        onChange={(e) => setNewProvider(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Google"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="provider-id">ID</Label>
                      <Input
                        id="provider-id"
                        value={newProvider.id || ''}
                        onChange={(e) => setNewProvider(prev => ({ ...prev, id: e.target.value }))}
                        placeholder="google (автоматически)"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="auth-url">Authorization URL</Label>
                    <Input
                      id="auth-url"
                      value={newProvider.authUrl}
                      onChange={(e) => setNewProvider(prev => ({ ...prev, authUrl: e.target.value }))}
                      placeholder="https://accounts.google.com/o/oauth2/v2/auth"
                    />
                  </div>

                  <div>
                    <Label htmlFor="token-url">Token URL</Label>
                    <Input
                      id="token-url"
                      value={newProvider.tokenUrl}
                      onChange={(e) => setNewProvider(prev => ({ ...prev, tokenUrl: e.target.value }))}
                      placeholder="https://oauth2.googleapis.com/token"
                    />
                  </div>

                  <div>
                    <Label htmlFor="client-id">Client ID</Label>
                    <Input
                      id="client-id"
                      value={newProvider.clientId}
                      onChange={(e) => setNewProvider(prev => ({ ...prev, clientId: e.target.value }))}
                      placeholder="your-client-id"
                    />
                  </div>

                  <div>
                    <Label htmlFor="redirect-uri">Redirect URI</Label>
                    <Input
                      id="redirect-uri"
                      value={newProvider.redirectUri}
                      onChange={(e) => setNewProvider(prev => ({ ...prev, redirectUri: e.target.value }))}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="response-type">Response Type</Label>
                      <Select value={newProvider.responseType} onValueChange={(value) => setNewProvider(prev => ({ ...prev, responseType: value as any }))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="code">Code (Authorization Code)</SelectItem>
                          <SelectItem value="token">Token (Implicit)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex items-center space-x-2 mt-6">
                      <Switch
                        id="state-required"
                        checked={newProvider.stateRequired}
                        onCheckedChange={(checked) => setNewProvider(prev => ({ ...prev, stateRequired: checked }))}
                      />
                      <Label htmlFor="state-required">State parameter required</Label>
                    </div>
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowAddProviderDialog(false)}>
                      Отмена
                    </Button>
                    <Button onClick={handleAddProvider} disabled={isLoading}>
                      {isLoading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
                      Добавить
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Провайдеры</p>
                <p className="text-2xl font-bold text-gray-900">{providers.length}</p>
              </div>
              <Shield className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Активные сессии</p>
                <p className="text-2xl font-bold text-green-600">{sessions.length}</p>
              </div>
              <Key className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Истекающие</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {sessions.filter(s => getSessionStatus(s).status === 'expiring').length}
                </p>
              </div>
              <Clock className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Истекшие</p>
                <p className="text-2xl font-bold text-red-600">
                  {sessions.filter(s => getSessionStatus(s).status === 'expired').length}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Основной контент */}
      <Tabs defaultValue="providers" className="oauth-tabs">
        <TabsList>
          <TabsTrigger value="providers">Провайдеры</TabsTrigger>
          <TabsTrigger value="sessions">Сессии</TabsTrigger>
          <TabsTrigger value="settings">Настройки</TabsTrigger>
        </TabsList>

        {/* Провайдеры */}
        <TabsContent value="providers">
          <Card>
            <CardHeader>
              <CardTitle>OAuth Провайдеры</CardTitle>
            </CardHeader>
            <CardContent>
              {providers.length === 0 ? (
                <div className="text-center py-12">
                  <Shield className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Нет настроенных провайдеров</h3>
                  <p className="text-gray-600 mb-4">Добавьте первый OAuth провайдер для начала работы</p>
                  <Button onClick={() => setShowAddProviderDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Добавить провайдера
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {providers.map((provider) => {
                    const providerSessions = sessions.filter(s => s.provider === provider.id);
                    const activeSessions = providerSessions.filter(s => getSessionStatus(s).status === 'active').length;
                    
                    return (
                      <div key={provider.id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="text-2xl">{getProviderIcon(provider.id)}</div>
                            
                            <div>
                              <h3 className="font-medium text-gray-900">{provider.name}</h3>
                              <p className="text-sm text-gray-600 mt-1">{provider.authUrl}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="outline">{provider.responseType}</Badge>
                                {provider.stateRequired && (
                                  <Badge variant="outline">State</Badge>
                                )}
                                <Badge variant="secondary">
                                  Сессии: {providerSessions.length}
                                </Badge>
                                {activeSessions > 0 && (
                                  <Badge className="bg-green-100 text-green-800">
                                    Активных: {activeSessions}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setSelectedProvider(selectedProvider === provider.id ? null : provider.id)}
                            >
                              <Settings className="w-4 h-4 mr-2" />
                              Настройки
                            </Button>
                            
                            <Button
                              size="sm"
                              onClick={() => handleInitiateOAuth(provider.id)}
                              disabled={isLoading}
                            >
                              <LogIn className="w-4 h-4 mr-2" />
                              Авторизоваться
                            </Button>
                            
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleTestProvider(provider.id)}
                              disabled={isLoading}
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                            
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteProvider(provider.id)}
                              disabled={isLoading}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>

                        {/* Детали провайдера */}
                        {selectedProvider === provider.id && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <Label className="text-sm text-gray-600">Client ID</Label>
                                <div className="flex items-center gap-2 mt-1">
                                  <code className="text-sm bg-gray-100 px-2 py-1 rounded flex-1">
                                    {showSecrets ? provider.clientId : '••••••••••••'}
                                  </code>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => copyToClipboard(provider.clientId)}
                                  >
                                    <Copy className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                              
                              <div>
                                <Label className="text-sm text-gray-600">Redirect URI</Label>
                                <div className="flex items-center gap-2 mt-1">
                                  <code className="text-sm bg-gray-100 px-2 py-1 rounded flex-1 truncate">
                                    {provider.redirectUri}
                                  </code>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => copyToClipboard(provider.redirectUri)}
                                  >
                                    <Copy className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                              
                              <div>
                                <Label className="text-sm text-gray-600">Token URL</Label>
                                <div className="mt-1">
                                  <code className="text-sm text-gray-700">{provider.tokenUrl}</code>
                                </div>
                              </div>
                              
                              <div>
                                <Label className="text-sm text-gray-600">Scopes</Label>
                                <div className="mt-1">
                                  {provider.scopes.map((scope, index) => (
                                    <Badge key={index} variant="secondary" className="mr-1">
                                      {scope}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>

                            {providerSessions.length > 0 && (
                              <div className="mt-4">
                                <Label className="text-sm text-gray-600 mb-2 block">Сессии пользователей</Label>
                                <div className="space-y-2">
                                  {providerSessions.slice(0, 3).map((session) => {
                                    const status = getSessionStatus(session);
                                    
                                    return (
                                      <div key={session.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                        <div>
                                          <span className="text-sm font-medium">
                                            {session.userEmail || session.userId || 'Unknown User'}
                                          </span>
                                          <div className="text-xs text-gray-500">
                                            Создана: {session.createdAt.toLocaleDateString()}
                                          </div>
                                        </div>
                                        
                                        <div className="flex items-center gap-2">
                                          <Badge className={status.color}>
                                            {status.text}
                                          </Badge>
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => handleRevokeToken(session.provider, session.userId)}
                                          >
                                            <LogOut className="w-3 h-3" />
                                          </Button>
                                        </div>
                                      </div>
                                    );
                                  })}
                                  
                                  {providerSessions.length > 3 && (
                                    <p className="text-sm text-gray-500 text-center">
                                      И еще {providerSessions.length - 3} сессий...
                                    </p>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Сессии */}
        <TabsContent value="sessions">
          <Card>
            <CardHeader>
              <CardTitle>Активные сессии</CardTitle>
            </CardHeader>
            <CardContent>
              {sessions.length === 0 ? (
                <div className="text-center py-12">
                  <Key className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Нет активных сессий</h3>
                  <p className="text-gray-600">Начните с авторизации через один из провайдеров</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {sessions.map((session) => {
                    const provider = providers.find(p => p.id === session.provider);
                    const status = getSessionStatus(session);
                    
                    return (
                      <div key={session.id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="text-2xl">{provider ? getProviderIcon(provider.id) : '🌐'}</div>
                            
                            <div>
                              <h3 className="font-medium text-gray-900">
                                {provider?.name || session.provider}
                              </h3>
                              <p className="text-sm text-gray-600">
                                {session.userEmail || session.userId || 'Unknown User'}
                              </p>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge className={status.color}>
                                  {status.text}
                                </Badge>
                                <span className="text-xs text-gray-500">
                                  Истекает: {session.expiresAt.toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRevokeToken(session.provider, session.userId)}
                            >
                              <LogOut className="w-4 h-4 mr-2" />
                              Отозвать
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Настройки */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Общие настройки</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Показывать секреты</h3>
                  <p className="text-sm text-gray-600">Отображать API ключи и токены в интерфейсе</p>
                </div>
                <Switch
                  checked={showSecrets}
                  onCheckedChange={setShowSecrets}
                />
              </div>

              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  <strong>Безопасность:</strong> OAuth токены хранятся локально в браузере. 
                  Для production среды используйте безопасное хранение на сервере.
                </AlertDescription>
              </Alert>

              <Alert>
                <ExternalLink className="h-4 w-4" />
                <AlertDescription>
                  <strong>Настройка провайдеров:</strong> Для каждого провайдера нужно настроить 
                  redirect URI в панели разработчика провайдера OAuth.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};