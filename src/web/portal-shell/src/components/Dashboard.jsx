
const Dashboard = () => {
  // Mock Data (will be replaced by API calls to Aggregator Service)
  const systemStatus = [
    { name: 'Kubernetes', status: 'operational', uptime: '99.9%' },
    { name: 'Keycloak', status: 'operational', uptime: '100%' },
    { name: 'RabbitMQ', status: 'operational', uptime: '99.8%' },
    { name: 'Wazuh', status: 'operational', uptime: '99.5%' },
  ];

  const recentTasks = [
    { id: 1, title: 'Implement RLTF Feedback Loop', status: 'Completed', assignee: 'AI Agent' },
    { id: 2, title: 'Fix Wazuh Certificates', status: 'Completed', assignee: 'DevOps' },
    { id: 3, title: 'Design Unified Dashboard', status: 'In Progress', assignee: 'Frontend' },
  ];

  const activityFeed = [
    { id: 1, user: 'AI Agent', action: 'committed to', target: 'configuration-repo', time: '5 mins ago' },
    { id: 2, user: 'Admin', action: 'deployed', target: 'collab-service', time: '1 hour ago' },
    { id: 3, user: 'OPA', action: 'blocked', target: 'nginx:latest deployment', time: '2 hours ago' },
  ];

  return (
    <div style={styles.dashboard}>
      <h2 style={styles.sectionTitle}>System Overview</h2>
      
      <div style={styles.grid}>
        {/* Widget 1: System Status */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>System Health</h3>
          <div style={styles.statusList}>
            {systemStatus.map((service) => (
              <div key={service.name} style={styles.statusItem}>
                <span style={styles.statusName}>{service.name}</span>
                <span style={{...styles.statusIndicator, color: service.status === 'operational' ? '#4caf50' : '#f44336'}}>
                  ● {service.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Widget 2: Recent Tasks */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Active Tasks</h3>
          <div style={styles.taskList}>
            {recentTasks.map((task) => (
              <div key={task.id} style={styles.taskItem}>
                <span style={styles.taskTitle}>{task.title}</span>
                <span style={styles.taskStatus}>{task.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Widget 3: Activity Feed */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Recent Activity</h3>
          <div style={styles.activityList}>
            {activityFeed.map((item) => (
              <div key={item.id} style={styles.activityItem}>
                <span style={styles.activityUser}>{item.user}</span> {item.action} <span style={styles.activityTarget}>{item.target}</span>
                <div style={styles.activityTime}>{item.time}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  dashboard: {
    padding: '20px 0',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    marginBottom: '20px',
    color: '#333',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
    border: '1px solid #e1e4e8',
  },
  cardTitle: {
    fontSize: '1.1rem',
    marginBottom: '15px',
    color: '#2c3e50',
    borderBottom: '1px solid #eee',
    paddingBottom: '10px',
  },
  statusList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  statusItem: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.9rem',
  },
  statusName: {
    fontWeight: '500',
  },
  taskList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  taskItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '0.9rem',
  },
  taskTitle: {
    color: '#333',
  },
  taskStatus: {
    fontSize: '0.8rem',
    padding: '4px 8px',
    borderRadius: '12px',
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
  },
  activityList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  activityItem: {
    fontSize: '0.9rem',
    color: '#555',
  },
  activityUser: {
    fontWeight: '600',
    color: '#333',
  },
  activityTarget: {
    color: '#0366d6',
  },
  activityTime: {
    fontSize: '0.8rem',
    color: '#999',
    marginTop: '2px',
  },
};

export default Dashboard;
