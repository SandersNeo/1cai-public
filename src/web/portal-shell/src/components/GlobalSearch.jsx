import { useEffect, useRef, useState } from 'react';

const GlobalSearch = () => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState([]);
  const wrapperRef = useRef(null);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleClickOutside = (event) => {
    if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
      setIsOpen(false);
    }
  };

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value);
    
    if (value.length > 2) {
      setIsOpen(true);
      // Mock Search Logic
      const mockResults = [
        { type: 'code', title: 'auth_service.py', subtitle: 'src/auth', url: '#' },
        { type: 'task', title: 'Implement OAuth2', subtitle: 'High Priority', url: '#' },
        { type: 'doc', title: 'Deployment Guide', subtitle: 'Wiki', url: '#' },
      ].filter(item => item.title.toLowerCase().includes(value.toLowerCase()));
      
      setResults(mockResults);
    } else {
      setResults([]);
      setIsOpen(false);
    }
  };

  return (
    <div ref={wrapperRef} style={styles.container}>
      <div style={styles.inputWrapper}>
        <span style={styles.icon}>🔍</span>
        <input
          style={styles.input}
          type="text"
          placeholder="Search everywhere (Ctrl+K)..."
          value={query}
          onChange={handleSearch}
          onFocus={() => query.length > 2 && setIsOpen(true)}
        />
      </div>

      {isOpen && results.length > 0 && (
        <div style={styles.dropdown}>
          {results.map((result, index) => (
            <div key={index} style={styles.resultItem}>
              <div style={styles.resultIcon}>
                {result.type === 'code' && '📦'}
                {result.type === 'task' && '✅'}
                {result.type === 'doc' && '📄'}
              </div>
              <div style={styles.resultContent}>
                <div style={styles.resultTitle}>{result.title}</div>
                <div style={styles.resultSubtitle}>{result.subtitle}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    position: 'relative',
    width: '400px',
    margin: '0 auto',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  icon: {
    position: 'absolute',
    left: '12px',
    color: '#666',
    zIndex: 1,
  },
  input: {
    width: '100%',
    padding: '10px 12px 10px 36px',
    borderRadius: '20px',
    border: '1px solid #ddd',
    outline: 'none',
    fontSize: '0.95rem',
    backgroundColor: 'white',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
    transition: 'box-shadow 0.2s',
  },
  dropdown: {
    position: 'absolute',
    top: '110%',
    left: 0,
    right: 0,
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    border: '1px solid #eee',
    overflow: 'hidden',
    zIndex: 100,
  },
  resultItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 16px',
    cursor: 'pointer',
    borderBottom: '1px solid #f5f5f5',
    transition: 'background-color 0.1s',
  },
  resultIcon: {
    fontSize: '1.2rem',
    marginRight: '12px',
  },
  resultContent: {
    display: 'flex',
    flexDirection: 'column',
  },
  resultTitle: {
    fontSize: '0.9rem',
    fontWeight: '500',
    color: '#333',
  },
  resultSubtitle: {
    fontSize: '0.8rem',
    color: '#888',
  },
};

export default GlobalSearch;
