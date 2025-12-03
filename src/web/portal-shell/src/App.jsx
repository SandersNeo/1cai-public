
const services = [
  { name: 'Business Workspace', url: 'http://localhost:13000', icon: '💼', description: 'NocoBase: No-Code Business Apps' },
  { name: 'Developer Workspace', url: 'http://localhost:8000', icon: '👨‍💻', description: 'VS Code Server: IDE' },
  { name: 'Git Server', url: 'http://localhost:3000', icon: '📦', description: 'Gitea: Source Control' },
  { name: 'Operations Workspace', url: 'http://localhost:9000', icon: '⚙️', description: 'Portainer: Docker Management' },
  { name: 'Event Bus', url: 'http://localhost:15672', icon: '📨', description: 'RabbitMQ: Messaging' },
];

import { useState } from 'react';
import ChatWidget from './components/ChatWidget';
import Dashboard from './components/Dashboard';
import GlobalSearch from './components/GlobalSearch';
import WorkspaceViewer from './components/WorkspaceViewer';

function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' or service URL
  const [currentTitle, setCurrentTitle] = useState('');

  const handleServiceClick = (service) => {
    // For now, only embed VS Code and NocoBase as examples
    if (service.name === 'Developer Workspace' || service.name === 'Business Workspace') {
      setCurrentView(service.url);
      setCurrentTitle(service.name);
    } else {
      window.open(service.url, '_blank');
    }
  };

  const handleCloseWorkspace = () => {
    setCurrentView('dashboard');
    setCurrentTitle('');
  };

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', padding: '2rem', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      <header style={{ marginBottom: '2rem', textAlign: 'center', display: currentView === 'dashboard' ? 'block' : 'none' }}>
        <h1 style={{ color: '#1a1a1a', fontSize: '2.5rem', marginBottom: '0.5rem' }}>Secure Enterprise OS</h1>
        <p style={{ color: '#666', marginBottom: '1.5rem' }}>Unified Workspace Portal</p>
        <GlobalSearch />
      </header>
      
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {currentView === 'dashboard' ? (
          <>
            <Dashboard />
            
            <h2 style={{ fontSize: '1.5rem', margin: '40px 0 20px', color: '#333' }}>Quick Access</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
              gap: '1.5rem',
            }}>
              {services.map((service) => (
                <div 
                  key={service.name} 
                  onClick={() => handleServiceClick(service)}
                  style={{
                    display: 'block',
                    padding: '1.5rem',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    cursor: 'pointer',
                    color: 'inherit',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    border: '1px solid #e1e4e8'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                    e.currentTarget.style.boxShadow = '0 10px 15px rgba(0,0,0,0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.05)';
                  }}
                >
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{service.icon}</div>
                  <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', color: '#2c3e50' }}>{service.name}</h2>
                  <p style={{ margin: '0', color: '#7f8c8d', fontSize: '0.85rem' }}>{service.description}</p>
                </div>
              ))}
            </div>
          </>
        ) : (
          <WorkspaceViewer 
            url={currentView} 
            title={currentTitle} 
            onClose={handleCloseWorkspace} 
          />
        )}
      </div>
      <ChatWidget />
    </div>
  );
}

export default App;
