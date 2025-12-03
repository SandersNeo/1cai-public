import { useState } from 'react';

const WorkspaceViewer = ({ url, title, onClose }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullScreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullScreen(false);
      }
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>{title}</h2>
        <div style={styles.controls}>
          <button onClick={toggleFullScreen} style={styles.button}>
            {isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
          </button>
          <button onClick={onClose} style={{...styles.button, backgroundColor: '#f44336'}}>
            Close
          </button>
        </div>
      </div>
      
      <div style={styles.frameContainer}>
        {isLoading && (
          <div style={styles.loader}>
            Loading {title}...
          </div>
        )}
        <iframe
          src={url}
          style={styles.iframe}
          title={title}
          onLoad={() => setIsLoading(false)}
          allow="clipboard-read; clipboard-write; fullscreen"
        />
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 100px)', // Adjust based on header/padding
    backgroundColor: 'white',
    borderRadius: '12px',
    overflow: 'hidden',
    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
  },
  header: {
    padding: '12px 20px',
    backgroundColor: '#f5f5f5',
    borderBottom: '1px solid #ddd',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    margin: 0,
    fontSize: '1.1rem',
    color: '#333',
  },
  controls: {
    display: 'flex',
    gap: '10px',
  },
  button: {
    padding: '6px 12px',
    borderRadius: '4px',
    border: 'none',
    backgroundColor: '#2196f3',
    color: 'white',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  frameContainer: {
    flex: 1,
    position: 'relative',
  },
  iframe: {
    width: '100%',
    height: '100%',
    border: 'none',
  },
  loader: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    color: '#666',
    fontSize: '1.2rem',
  },
};

export default WorkspaceViewer;
