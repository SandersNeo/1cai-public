class ContextCollector {
    constructor(wsClient) {
        this.ws = wsClient;
        this.isTracking = false;
    }

    start() {
        if (this.isTracking) return;
        this.isTracking = true;
        
        document.addEventListener('click', this.handleClick.bind(this), true);
        document.addEventListener('input', this.handleInput.bind(this), true);
        
        console.log('[ContextCollector] Started tracking user interactions.');
    }

    stop() {
        this.isTracking = false;
        document.removeEventListener('click', this.handleClick.bind(this), true);
        document.removeEventListener('input', this.handleInput.bind(this), true);
    }

    handleClick(event) {
        const target = event.target;
        const context = {
            type: 'click',
            tag: target.tagName,
            id: target.id,
            className: target.className,
            text: target.innerText?.substring(0, 50),
            timestamp: new Date().toISOString(),
            path: window.location.pathname
        };
        
        this.sendContext(context);
    }

    handleInput(event) {
        // Debounce could be added here
        const target = event.target;
        const context = {
            type: 'input',
            tag: target.tagName,
            id: target.id,
            value: target.value?.substring(0, 20) + '...', // Privacy: don't send full content
            timestamp: new Date().toISOString()
        };
        
        this.sendContext(context);
    }

    sendContext(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'context_event',
                payload: data
            };
            this.ws.send(JSON.stringify(message));
        }
    }
}

export default ContextCollector;
