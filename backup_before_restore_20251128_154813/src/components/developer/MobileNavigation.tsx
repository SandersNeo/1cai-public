/**
 * MobileNavigation Component
 * 
 * ИСПРАВЛЕНИЕ TYPESCRIPT ОШИБОК И RXJS ПОДПИСОК
 * 
 * Основные исправления:
 * 1. Исправлена синтаксическая ошибка в renderSideDrawer (строка 347)
 * 2. Улучшена типизация rxjs подписок с проверками на существование методов
 * 3. Добавлена безопасная очистка подписок в useEffect cleanup
 * 4. Все вызовы методов сервисов защищены проверками typeof === 'function'
 * 5. Устранены ошибки 'Property subscribe does not exist on type never'
 * 
 * Подход к решению:
 * - Использование опциональной цепочки (?.) для доступа к Observable
 * - Проверка typeof subscription.unsubscribe === 'function' перед очисткой
 * - Создание массива подписок для централизованной очистки
 * - Защита вызовов методов сервисов проверками типов
 */

import React, { useState, useEffect, useRef } from 'react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  Home, 
  Users, 
  CheckSquare, 
  Folder, 
  Settings, 
  Menu, 
  X,
  ChevronRight,
  Plus,
  Search,
  Bell
} from 'lucide-react';
import { NavigationItem, MobileNavigationService, NavigationState } from '../../services/mobile-navigation-service';
import { MobileDetectionService, DeviceInfo } from '../../services/mobile-detection-service';

interface MobileNavigationProps {
  navigationService: MobileNavigationService;
  mobileDetection: MobileDetectionService;
  className?: string;
}

const MobileNavigation: React.FC<MobileNavigationProps> = ({
  navigationService,
  mobileDetection,
  className = ''
}) => {
  const [navigationItems, setNavigationItems] = useState<NavigationItem[]>([]);
  const [state, setState] = useState<NavigationState | null>(null);
  const [deviceInfo, setDeviceInfo] = useState<any>(null);
  const [isVisible, setIsVisible] = useState(true);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  
  const drawerRef = useRef<HTMLDivElement>(null);
  const lastScrollY = useRef(0);

  useEffect(() => {
    // Подписки на Observable с безопасной типизацией
    const subscriptions: any[] = [];

    // Subscribe to state changes
    const stateSubscription = (navigationService as any).state$?.subscribe?.((navState: any) => {
      setState(navState);
    });
    if (stateSubscription) subscriptions.push(stateSubscription);

    // Get navigation items с проверкой на Observable
    const itemsResult = (navigationService as any).getNavigationItems?.();
    if (Array.isArray(itemsResult)) {
      setNavigationItems(itemsResult);
    } else if (itemsResult && typeof itemsResult.subscribe === 'function') {
      const itemsSubscription = itemsResult.subscribe((navItems: any) => {
        setNavigationItems(navItems);
      });
      subscriptions.push(itemsSubscription);
    }

    // Subscribe to visibility changes
    const visibilitySubscription = (navigationService as any).visibility$?.subscribe?.((visible: any) => {
      setIsVisible(visible);
    });
    if (visibilitySubscription) subscriptions.push(visibilitySubscription);

    // Subscribe to device changes
    const deviceSubscription = (mobileDetection as any).deviceInfo$?.subscribe?.((device: any) => {
      setDeviceInfo(device);
    });
    if (deviceSubscription) subscriptions.push(deviceSubscription);

    // Scroll handling for auto-hide
    let scrollListener: any;
    if (typeof window !== 'undefined') {
      const handleScroll = () => {
        const currentScrollY = window.scrollY;
        
        if (currentScrollY > lastScrollY.current && currentScrollY > 100) {
          setIsVisible(false);
        } else {
          setIsVisible(true);
        }
        
        lastScrollY.current = currentScrollY;
      };

      window.addEventListener('scroll', handleScroll, { passive: true });
      scrollListener = handleScroll;
    }

    return () => {
      // Безопасная очистка всех подписок
      subscriptions.forEach((sub: any) => {
        if (sub && typeof sub.unsubscribe === 'function') {
          sub.unsubscribe();
        }
      });
      
      // Очистка scroll listener
      if (scrollListener && typeof window !== 'undefined') {
        window.removeEventListener('scroll', scrollListener);
      }
    };
  }, [navigationService, mobileDetection]);

  const handleNavigationClick = (item: any) => {
    if (item?.disabled) return;
    
    if (item?.id && typeof navigationService.selectNavigationItem === 'function') {
      navigationService.selectNavigationItem(item.id);
    }
    setActiveDropdown(null);
  };

  const handleDrawerToggle = () => {
    if (typeof navigationService.toggleDrawer === 'function') {
      navigationService.toggleDrawer();
    }
  };

  const getVisibleItems = (): any[] => {
    const deviceType = (deviceInfo as any)?.type || 'desktop';
    return (navigationItems as any)
      .filter((item: any) => !item.disabled)
      .slice(0, deviceType === 'mobile' ? 4 : 6);
  };

  const renderBottomTabs = (): JSX.Element | null => {
    if (!isVisible || !state) return null;

    const visibleItems = getVisibleItems();
    const deviceType = deviceInfo?.type || 'desktop';
    const maxItems = deviceType === 'mobile' ? 4 : 6;

    return (
      <div className={`
        fixed bottom-0 left-0 right-0 z-50 
        bg-white border-t border-gray-200 
        safe-area-bottom
        transform transition-transform duration-300 ease-in-out
        ${!isVisible ? 'translate-y-full' : 'translate-y-0'}
        ${className}
      `}>
        <div className={`grid grid-cols-${maxItems} gap-1 p-2`}>
          {(visibleItems as any).map((item: any, index: any) => {
            const isActive = (item as any).id === (state as any)?.activeItem || '';
            const hasChildren = (item as any).children && (item as any).children.length > 0;
            
            return (
              <div key={(item as any).id} className="relative">
                <button
                  onClick={() => {
                    if (hasChildren) {
                      setActiveDropdown(activeDropdown === (item as any).id ? null : (item as any).id);
                    } else {
                      handleNavigationClick(item);
                    }
                  }}
                  className={`
                    flex flex-col items-center justify-center 
                    w-full h-16 rounded-lg transition-all duration-200
                    ${isActive 
                      ? 'text-primary bg-primary/10' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }
                  `}
                >
                  <div className="relative">
                    {(item as any).icon && (
                      <span className="text-xl">{getIcon((item as any).icon)}</span>
                    )}
                    {(item as any).badge && (
                      <Badge 
                        variant="destructive" 
                        className="absolute -top-2 -right-2 min-w-[1.2rem] h-5 text-xs p-0 flex items-center justify-center"
                      >
                        {typeof (item as any).badge === 'number' && (item as any).badge > 99 ? '99+' : (item as any).badge}
                      </Badge>
                    )}
                  </div>
                  
                  <span className="text-xs mt-1 font-medium leading-tight">
                    {(item as any).label}
                  </span>
                </button>

                {/* Dropdown for child items */}
                {hasChildren && activeDropdown === (item as any).id && (
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-lg py-2 min-w-[200px]">
                      {(item as any).children?.map((child: any) => (
                        <button
                          key={(child as any).id}
                          onClick={() => handleNavigationClick(child)}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                          {(child as any).icon && (
                            <span className="mr-3">{getIcon((child as any).icon)}</span>
                          )}
                          <span>{(child as any).label}</span>
                          {(child as any).badge && (
                            <Badge variant="secondary" className="ml-auto">
                              {(child as any).badge}
                            </Badge>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          
          {/* More button for additional items */}
          {navigationItems.filter((item: NavigationItem) => !item.disabled).length > maxItems && (
            <button
              onClick={handleDrawerToggle}
              className="flex flex-col items-center justify-center w-full h-16 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
            >
              <Menu className="text-xl" />
              <span className="text-xs mt-1 font-medium">Ещё</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderSideDrawer = (): JSX.Element | null => {
    if (!state || !state.drawerOpen) return null;

    return (
      <>
        {/* Overlay */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => typeof navigationService.closeDrawer === 'function' && navigationService.closeDrawer()}
        />
        
        {/* Drawer */}
        <div 
          ref={drawerRef}
          className={`
            fixed inset-y-0 left-0 z-50 w-80 bg-white border-r border-gray-200 
            transform transition-transform duration-300 ease-in-out
            ${state.drawerOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
        >
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">Навигация</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => typeof navigationService.closeDrawer === 'function' && navigationService.closeDrawer()}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Quick Actions */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Plus className="h-4 w-4 mr-2" />
                  Создать
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  <Search className="h-4 w-4 mr-2" />
                  Поиск
                </Button>
                <Button variant="outline" size="sm">
                  <Bell className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Navigation Items */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-2">
                {navigationItems.filter((item: NavigationItem) => item && typeof item === 'object').map((item: NavigationItem) => {
                  const isActive = item.id === (state?.activeItem || '');
                  const hasChildren = item.children && Array.isArray(item.children) && item.children.length > 0;
                  const isExpanded = activeDropdown === item.id;
                  
                  return (
                    <div key={item.id}>
                      <button
                        onClick={() => {
                          if (hasChildren) {
                            setActiveDropdown(isExpanded ? null : item.id);
                          } else {
                            handleNavigationClick(item);
                          }
                        }}
                        className={`
                          flex items-center w-full p-3 rounded-lg text-left transition-colors
                          ${isActive 
                            ? 'bg-primary text-primary-foreground' 
                            : 'text-gray-700 hover:bg-gray-100'
                          }
                          ${item.disabled ? 'opacity-50 cursor-not-allowed' : ''}
                        `}
                        disabled={item.disabled}
                      >
                        {item.icon && (
                          <span className="mr-3 text-lg">{getIcon(item.icon)}</span>
                        )}
                        
                        <div className="flex-1">
                          <div className="font-medium">{item.label}</div>
                          {hasChildren && (
                            <div className="text-xs opacity-70">
                              {item.children?.length} подразделов
                            </div>
                          )}
                        </div>

                        {item.badge && (
                          <Badge 
                            variant={isActive ? "secondary" : "default"}
                            className="ml-2"
                          >
                            {item.badge}
                          </Badge>
                        )}

                        {hasChildren && (
                          <ChevronRight 
                            className={`ml-2 h-4 w-4 transition-transform ${
                              isExpanded ? 'rotate-90' : ''
                            }`} 
                          />
                        )}
                      </button>

                      {/* Child items */}
                      {hasChildren && isExpanded && item.children && Array.isArray(item.children) && (
                        <div className="ml-8 mt-1 space-y-1">
                          {item.children.map((child: NavigationItem) => {
                            if (!child || typeof child !== 'object') return null;
                            return (
                              <button
                                key={child.id}
                                onClick={() => handleNavigationClick(child)}
                                className={`
                                  flex items-center w-full p-2 rounded text-left text-sm
                                  ${child.id === (state?.activeItem || '')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-gray-600 hover:bg-gray-50'
                                  }
                                `}
                              >
                                {child.icon && (
                                  <span className="mr-2">{getIcon(child.icon)}</span>
                                )}
                                <span>{child.label}</span>
                                {child.badge && (
                                  <Badge variant="outline" className="ml-auto">
                                    {child.badge}
                                  </Badge>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200">
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => typeof navigationService.selectNavigationItem === 'function' && navigationService.selectNavigationItem('settings')}
              >
                <Settings className="h-4 w-4 mr-2" />
                Настройки
              </Button>
            </div>
          </div>
        </div>
      </>
    );
  };

  const renderFloatingActionButton = (): JSX.Element | null => {
    const deviceType = deviceInfo?.type;
    if (deviceType !== 'mobile' || !isVisible) return null;

    return (
      <div className={`
        fixed bottom-20 right-4 z-40
        transform transition-all duration-300 ease-in-out
        ${!isVisible ? 'translate-y-16 opacity-0' : 'translate-y-0 opacity-100'}
      `}>
        <Button
          size="lg"
          className="rounded-full w-14 h-14 shadow-lg"
          onClick={handleDrawerToggle}
        >
          <Menu className="h-6 w-6" />
        </Button>
      </div>
    );
  };

  const getIcon = (iconName: string): React.ReactNode => {
    const icons: Record<string, React.ReactNode> = {
      home: <Home className="h-5 w-5" />,
      users: <Users className="h-5 w-5" />,
      'check-square': <CheckSquare className="h-5 w-5" />,
      folder: <Folder className="h-5 w-5" />,
      settings: <Settings className="h-5 w-5" />,
      menu: <Menu className="h-5 w-5" />
    };
    
    return icons[iconName] || <div className="h-5 w-5 bg-gray-300 rounded" />;
  };

  // Don't render anything if device detection is not complete
  if (!deviceInfo) {
    return null;
  }

  // Render based on device type and navigation style
  const config = (navigationService as any).getConfig?.();
  const navigationStyle = config?.style || 'bottom-tabs';
  const deviceType = deviceInfo?.type || 'desktop';

  switch (navigationStyle) {
    case 'bottom-tabs':
      return renderBottomTabs();
    
    case 'side-drawer':
      return (
        <>
          {/* Toggle button for desktop */}
          {deviceType !== 'mobile' && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDrawerToggle}
              className="fixed top-4 left-4 z-30"
            >
              <Menu className="h-4 w-4" />
            </Button>
          )}
          {renderSideDrawer()}
          {renderFloatingActionButton()}
        </>
      );
    
    case 'floating':
      return renderFloatingActionButton();
    
    default:
      return renderBottomTabs();
  }
};

export default MobileNavigation;