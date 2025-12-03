import { useEffect, useRef, useState } from 'react';

import ContextCollector from '../utils/ContextCollector';

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [status, setStatus] = useState('disconnected'); // disconnected, connecting, connected
  const ws = useRef(null);
  const messagesEndRef = useRef(null);
  const collector = useRef(null);

  useEffect(() => {
    if (isOpen && status === 'disconnected') {
      connect();
    }
    // Cleanup on unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (collector.current) {
        collector.current.stop();
      }
    };
  }, [isOpen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connect = () => {
    setStatus('connecting');
    // Connect to the Collab Service
    // Note: In production, this URL should be configurable
    ws.current = new WebSocket('ws://localhost:8002/ws/portal-chat');

    ws.current.onopen = () => {
      setStatus('connected');
      addMessage({ sender: 'System', text: 'Connected to chat room.' });
      
      // Initialize Context Collector
      collector.current = new ContextCollector(ws.current);
      collector.current.start();
    };

    ws.current.onmessage = (event) => {
      try {
        // Assume simple text for now, or JSON
        // If it's a JSON string, parse it. If not, treat as text.
        let data = event.data;
        try {
            const parsed = JSON.parse(data);
            addMessage(parsed);
        } catch (e) {
            addMessage({ sender: 'User', text: data });
        }
      } catch (error) {
        console.error('Message parsing error:', error);
      }
    };

    ws.current.onclose = () => {
      setStatus('disconnected');
      addMessage({ sender: 'System', text: 'Disconnected.' });
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('error');
    };
  };

  const addMessage = (msg) => {
    setMessages((prev) => [...prev, msg]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = () => {
    if (!inputValue.trim() || status !== 'connected') return;

    const message = {
      sender: 'Me', // In real app, get from Auth Context
      text: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    // Send as JSON string
    ws.current.send(JSON.stringify(message));
    
    // Optimistically add to UI
    addMessage(message);
    setInputValue('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div style={styles.container}>
      {!isOpen && (
        <button onClick={() => setIsOpen(true)} style={styles.toggleButton}>
          💬 Chat
        </button>
      )}

      {isOpen && (
        <div style={styles.widget}>
          <div style={styles.header}>
            <div style={styles.status}>
              <span style={{...styles.dot, backgroundColor: status === 'connected' ? '#4caf50' : '#f44336'}}></span>
              Team Chat
            </div>
            <button onClick={() => setIsOpen(false)} style={styles.closeButton}>×</button>
          </div>

          <div style={styles.messages}>
            {messages.map((msg, index) => (
              <div key={index} style={msg.sender === 'Me' ? styles.myMessage : styles.otherMessage}>
                <div style={styles.sender}>{msg.sender}</div>
                <div>{msg.text}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div style={styles.inputArea}>
            <input
              style={styles.input}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              disabled={status !== 'connected'}
            />
            <button onClick={handleSend} style={styles.sendButton} disabled={status !== 'connected'}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 1000,
    fontFamily: 'Inter, sans-serif',
  },
  toggleButton: {
    padding: '12px 24px',
    borderRadius: '30px',
    backgroundColor: '#FF9100', // 1C Yellow/Orange
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    fontSize: '16px',
    fontWeight: '600',
  },
  widget: {
    width: '350px',
    height: '500px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '16px',
    backgroundColor: '#f5f5f5',
    borderBottom: '1px solid #eee',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    fontWeight: '600',
    color: '#333',
  },
  dot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    marginRight: '8px',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    cursor: 'pointer',
    color: '#666',
  },
  messages: {
    flex: 1,
    padding: '16px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    backgroundColor: '#fff',
  },
  myMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#FFF3E0', // Light orange
    padding: '8px 12px',
    borderRadius: '12px 12px 0 12px',
    maxWidth: '80%',
    fontSize: '14px',
  },
  otherMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f5f5f5',
    padding: '8px 12px',
    borderRadius: '12px 12px 12px 0',
    maxWidth: '80%',
    fontSize: '14px',
  },
  sender: {
    fontSize: '11px',
    color: '#888',
    marginBottom: '4px',
  },
  inputArea: {
    padding: '12px',
    borderTop: '1px solid #eee',
    display: 'flex',
    gap: '8px',
  },
  input: {
    flex: 1,
    padding: '8px 12px',
    borderRadius: '20px',
    border: '1px solid #ddd',
    outline: 'none',
    fontSize: '14px',
  },
  sendButton: {
    padding: '8px 16px',
    borderRadius: '20px',
    backgroundColor: '#FF9100',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '14px',
  },
};

export default ChatWidget;
