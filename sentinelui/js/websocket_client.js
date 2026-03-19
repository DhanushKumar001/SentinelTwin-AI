/**
 * SentinelTwin AI — WebSocket Client
 * Manages real-time bidirectional communication with the backend.
 */
class SentinelWebSocket {
  constructor(url, onMessage, onStatusChange) {
    this.url = url;
    this.onMessage = onMessage;
    this.onStatusChange = onStatusChange;
    this.ws = null;
    this.reconnectDelay = 2000;
    this.maxReconnectDelay = 30000;
    this.reconnectAttempts = 0;
    this.connected = false;
    this._pingInterval = null;
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 2000;
        this.onStatusChange(true);
        this.ws.send(JSON.stringify({ type: 'client_info', data: { name: 'SentinelTwin-Dashboard', version: '1.0.0' } }));
        this._pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping', data: {} }));
          }
        }, 25000);
      };
      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          this.onMessage(msg);
        } catch (e) {
          console.warn('WS parse error:', e);
        }
      };
      this.ws.onclose = () => {
        this.connected = false;
        clearInterval(this._pingInterval);
        this.onStatusChange(false);
        const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), delay);
      };
      this.ws.onerror = (err) => {
        console.warn('WS error:', err);
      };
    } catch (e) {
      console.warn('WS connect error:', e);
      setTimeout(() => this.connect(), this.reconnectDelay);
    }
  }

  send(type, data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data, timestamp: new Date().toISOString() }));
    }
  }

  disconnect() {
    clearInterval(this._pingInterval);
    if (this.ws) this.ws.close();
  }
}
