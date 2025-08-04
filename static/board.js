/**
 * FastBoard Client-Side JavaScript
 * Real-time collaborative whiteboard with WebSocket support
 */

class FastBoard {
  constructor() {
    // Get canvas element and 2D context
    this.canvas = document.getElementById('whiteboard-canvas');
    this.ctx = this.canvas.getContext('2d');

    // Drawing state
    this.isDrawing = false;
    this.lastX = 0;
    this.lastY = 0;
    this.currentStroke = []; // Store current stroke points

    // Current tool settings
    this.currentTool = 'pen';
    this.currentColor = '#000000';
    this.currentSize = 5;

    // WebSocket and collaboration
    this.clientId = this.generateClientId();
    this.ws = null;
    this.isConnected = false;

    // Real-time cursor tracking
    this.otherCursors = {}; // Store other users' cursors

    this.init();
  }

  /**
   * Generate a simple unique client ID
   */
  generateClientId() {
    return (
      'client_' +
      Math.random().toString(36).substr(2, 9) +
      '_' +
      Date.now().toString(36)
    );
  }

  init() {
    this.setupCanvas();
    this.setupEventListeners();
    this.setupWebSocket();
  }

  /**
   * Initialize WebSocket connection for real-time collaboration
   */
  setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.updateConnectionStatus(true);
      };

      this.ws.onmessage = (event) => {
        this.handleWebSocketMessage(event);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.updateConnectionStatus(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (!this.isConnected) {
            this.setupWebSocket();
          }
        }, 3000);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnected = false;
        this.updateConnectionStatus(false);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleWebSocketMessage(event) {
    try {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'draw':
          this.handleRemoteDrawing(message);
          break;
        case 'user_count':
          this.updateUserCount(message.payload.count);
          break;
        case 'cursor':
          this.updateRemoteCursor(message);
          break;
        case 'clear':
          this.handleRemoteClear(message);
          break;
        case 'board_state':
          this.handleBoardState(message);
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Send a message through WebSocket
   */
  sendWebSocketMessage(message) {
    if (this.ws && this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  /**
   * Update connection status indicator
   */
  updateConnectionStatus(connected) {
    const indicator = document.querySelector('.w-2.h-2.bg-green-500');
    if (indicator) {
      if (connected) {
        indicator.classList.remove('bg-red-500');
        indicator.classList.add('bg-green-500', 'animate-pulse');
      } else {
        indicator.classList.remove('bg-green-500', 'animate-pulse');
        indicator.classList.add('bg-red-500');
      }
    }
  }

  setupCanvas() {
    // Set canvas size to fill its container
    this.resizeCanvas();

    // Set canvas drawing properties for smooth lines
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';
    this.ctx.imageSmoothingEnabled = true;
  }

  resizeCanvas() {
    const container = this.canvas.parentElement;
    const rect = container.getBoundingClientRect();

    // Set canvas size to fill container
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
  }

  setupEventListeners() {
    // Canvas mouse events for drawing
    this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
    this.canvas.addEventListener('mousemove', (e) => {
      this.draw(e);
      this.handleMouseMove(e); // For cursor tracking
    });
    this.canvas.addEventListener('mouseup', () => this.stopDrawing());
    this.canvas.addEventListener('mouseout', () => this.stopDrawing());

    // Global mouse move for cursor tracking
    window.addEventListener('mousemove', (e) => this.trackCursor(e));

    // Touch events for mobile support
    this.canvas.addEventListener('touchstart', (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY,
      });
      this.canvas.dispatchEvent(mouseEvent);
    });

    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY,
      });
      this.canvas.dispatchEvent(mouseEvent);
    });

    this.canvas.addEventListener('touchend', (e) => {
      e.preventDefault();
      const mouseEvent = new MouseEvent('mouseup', {});
      this.canvas.dispatchEvent(mouseEvent);
    });

    // Toolbar control event listeners
    this.setupToolbarListeners();

    // Window resize
    window.addEventListener('resize', () => {
      this.resizeCanvas();
    });
  }

  /**
   * Handle mouse movement for cursor tracking
   */
  handleMouseMove(event) {
    // This is handled by the global mousemove listener
  }

  /**
   * Track cursor position and send to other users
   */
  trackCursor(event) {
    // Only track if mouse is over the canvas
    const rect = this.canvas.getBoundingClientRect();
    const isOverCanvas =
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom;

    if (isOverCanvas) {
      const coords = this.getCanvasCoordinates(event);

      // Send cursor position via WebSocket
      this.sendWebSocketMessage({
        type: 'cursor',
        clientId: this.clientId,
        payload: {
          x: coords.x,
          y: coords.y,
        },
      });
    }
  }

  setupToolbarListeners() {
    // Tool buttons
    const penTool = document.getElementById('pen-tool');
    const eraserTool = document.getElementById('eraser-tool');

    if (penTool) {
      penTool.addEventListener('click', () => this.setTool('pen'));
    }

    if (eraserTool) {
      eraserTool.addEventListener('click', () => this.setTool('eraser'));
    }

    // Color picker
    const colorPicker = document.getElementById('color-picker');
    if (colorPicker) {
      colorPicker.addEventListener('change', (e) => {
        this.setColor(e.target.value);
      });
    }

    // Brush size slider
    const brushSize = document.getElementById('brush-size');
    const sizeDisplay = document.getElementById('size-display');

    if (brushSize) {
      brushSize.addEventListener('input', (e) => {
        this.currentSize = parseInt(e.target.value);
        if (sizeDisplay) {
          sizeDisplay.textContent = this.currentSize + 'px';
        }
      });
    }

    // Clear board button
    const clearBoard = document.getElementById('clear-board');
    if (clearBoard) {
      clearBoard.addEventListener('click', () => {
        this.clearBoard();
      });
    }

    // AI Assist button
    const aiAssistButton = document.getElementById('ai-assist');
    if (aiAssistButton) {
      aiAssistButton.addEventListener('click', () => {
        this.handleAIAssist();
      });
    }

    // AI Modal close button
    const closeAIModal = document.getElementById('close-ai-modal');
    if (closeAIModal) {
      closeAIModal.addEventListener('click', () => {
        this.hideAIModal();
      });
    }
  }

  getCanvasCoordinates(event) {
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = this.canvas.width / rect.width;
    const scaleY = this.canvas.height / rect.height;

    return {
      x: (event.clientX - rect.left) * scaleX,
      y: (event.clientY - rect.top) * scaleY,
    };
  }

  startDrawing(event) {
    this.isDrawing = true;
    const coords = this.getCanvasCoordinates(event);
    this.lastX = coords.x;
    this.lastY = coords.y;

    // Initialize current stroke
    this.currentStroke = [
      {
        x: coords.x,
        y: coords.y,
      },
    ];
  }

  draw(event) {
    if (!this.isDrawing) return;

    const coords = this.getCanvasCoordinates(event);

    // Add point to current stroke
    this.currentStroke.push({
      x: coords.x,
      y: coords.y,
    });

    // Draw on canvas
    this.drawLine(
      this.lastX,
      this.lastY,
      coords.x,
      coords.y,
      this.currentTool,
      this.currentColor,
      this.currentSize
    );

    // Update last position
    this.lastX = coords.x;
    this.lastY = coords.y;
  }

  stopDrawing() {
    if (!this.isDrawing) return;

    this.isDrawing = false;

    // Send drawing data via WebSocket when stroke is complete
    if (this.currentStroke.length > 0) {
      this.sendWebSocketMessage({
        type: 'draw',
        clientId: this.clientId,
        payload: {
          tool: this.currentTool,
          color: this.currentColor,
          size: this.currentSize,
          points: this.currentStroke,
        },
      });
    }

    // Clear current stroke
    this.currentStroke = [];
  }

  /**
   * Draw a line on the canvas
   */
  drawLine(fromX, fromY, toX, toY, tool, color, size) {
    // Set line properties based on tool
    this.ctx.lineWidth = size;

    if (tool === 'eraser') {
      this.ctx.globalCompositeOperation = 'destination-out';
    } else {
      this.ctx.globalCompositeOperation = 'source-over';
      this.ctx.strokeStyle = color;
    }

    // Draw line
    this.ctx.beginPath();
    this.ctx.moveTo(fromX, fromY);
    this.ctx.lineTo(toX, toY);
    this.ctx.stroke();
  }

  /**
   * Draw a complete stroke from points data
   */
  drawStroke(strokeData) {
    const { tool, color, size, points } = strokeData;

    if (!points || points.length < 2) return;

    // Set drawing properties
    this.ctx.lineWidth = size;

    if (tool === 'eraser') {
      this.ctx.globalCompositeOperation = 'destination-out';
    } else {
      this.ctx.globalCompositeOperation = 'source-over';
      this.ctx.strokeStyle = color;
    }

    // Draw the stroke
    this.ctx.beginPath();
    this.ctx.moveTo(points[0].x, points[0].y);

    for (let i = 1; i < points.length; i++) {
      this.ctx.lineTo(points[i].x, points[i].y);
    }

    this.ctx.stroke();
  }

  setTool(tool) {
    this.currentTool = tool;

    // Update UI to show active tool
    this.updateToolUI(tool);

    // Change cursor based on tool
    this.canvas.style.cursor = tool === 'eraser' ? 'grab' : 'crosshair';
  }

  updateToolUI(activeTool) {
    // Remove active class from all tool buttons
    const toolButtons = document.querySelectorAll('[id$="-tool"]');
    toolButtons.forEach((btn) => {
      btn.classList.remove('tool-active', 'bg-blue-600', 'text-white');
      btn.classList.add('bg-gray-700', 'hover:bg-gray-600');
    });

    // Add active class to current tool
    const activeBtn = document.getElementById(activeTool + '-tool');
    if (activeBtn) {
      activeBtn.classList.add('tool-active', 'bg-blue-600', 'text-white');
      activeBtn.classList.remove('bg-gray-700', 'hover:bg-gray-600');
    }
  }

  setColor(color) {
    this.currentColor = color;
  }

  clearBoard() {
    if (
      confirm(
        'Are you sure you want to clear the board? This action cannot be undone.'
      )
    ) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      // Send clear message via WebSocket
      this.sendWebSocketMessage({
        type: 'clear',
        clientId: this.clientId,
      });
    }
  }

  /**
   * Handle remote drawing from other users
   */
  handleRemoteDrawing(message) {
    if (message.clientId === this.clientId) return; // Don't draw our own strokes

    const strokeData = message.payload;
    this.drawStroke(strokeData);
  }

  /**
   * Handle remote clear board action
   */
  handleRemoteClear(message) {
    if (message.clientId === this.clientId) return; // Don't clear from our own action

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * Handle board state from server (for new users)
   */
  handleBoardState(message) {
    const actions = message.payload.actions;

    // Clear canvas first
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Replay all actions
    actions.forEach((action) => {
      if (action.type === 'draw') {
        this.drawStroke(action.payload);
      } else if (action.type === 'clear') {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      }
    });
  }

  /**
   * Update user count display
   */
  updateUserCount(count) {
    const userCountElement = document.getElementById('user-count');
    if (userCountElement) {
      userCountElement.textContent = count;
    }
  }

  /**
   * Update remote cursor position
   */
  updateRemoteCursor(message) {
    if (message.clientId === this.clientId) return; // Don't show our own cursor

    const { clientId } = message;
    const { x, y } = message.payload;

    // Get or create cursor element
    let cursorElement = this.otherCursors[clientId];

    if (!cursorElement) {
      cursorElement = this.createCursorElement(clientId);
      this.otherCursors[clientId] = cursorElement;
      document.body.appendChild(cursorElement);
    }

    // Convert canvas coordinates to screen coordinates
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = rect.width / this.canvas.width;
    const scaleY = rect.height / this.canvas.height;

    const screenX = rect.left + x * scaleX;
    const screenY = rect.top + y * scaleY;

    // Update cursor position
    cursorElement.style.left = screenX + 'px';
    cursorElement.style.top = screenY + 'px';
    cursorElement.style.display = 'block';

    // Hide cursor after 3 seconds of inactivity
    clearTimeout(cursorElement.hideTimeout);
    cursorElement.hideTimeout = setTimeout(() => {
      cursorElement.style.display = 'none';
    }, 3000);
  }

  /**
   * Create a cursor element for remote users
   */
  createCursorElement(clientId) {
    const cursor = document.createElement('div');
    cursor.className = 'remote-cursor';
    cursor.style.cssText = `
      position: fixed;
      width: 12px;
      height: 12px;
      background-color: #8B5CF6;
      border: 2px solid white;
      border-radius: 50%;
      pointer-events: none;
      z-index: 1000;
      transform: translate(-50%, -50%);
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      display: none;
    `;

    // Add user label
    const label = document.createElement('div');
    label.textContent = clientId.substring(0, 8) + '...';
    label.style.cssText = `
      position: absolute;
      top: 15px;
      left: 50%;
      transform: translateX(-50%);
      background-color: #8B5CF6;
      color: white;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      white-space: nowrap;
      font-family: sans-serif;
    `;
    cursor.appendChild(label);

    return cursor;
  }

  /**
   * Handle AI Assist button click
   */
  async handleAIAssist() {
    try {
      // Show loading indicator
      this.showLoadingIndicator();

      // Convert canvas to Base64 encoded PNG string
      const canvasDataURL = this.canvas.toDataURL('image/png');

      // Make fetch POST request to /api/v1/ai-assist endpoint
      const response = await fetch('/api/v1/ai-assist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: canvasDataURL,
        }),
      });

      // Hide loading indicator
      this.hideLoadingIndicator();

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        // Display the AI response in modal
        this.showAIModal(result.interpretation);
      } else {
        throw new Error('AI processing failed');
      }
    } catch (error) {
      console.error('AI Assist error:', error);
      this.hideLoadingIndicator();
      this.showAIModal(`Error: ${error.message}`, true);
    }
  }

  /**
   * Show loading indicator
   */
  showLoadingIndicator() {
    const loadingSpinner = document.getElementById('loading-spinner');
    if (loadingSpinner) {
      loadingSpinner.classList.remove('hidden');
    }
  }

  /**
   * Hide loading indicator
   */
  hideLoadingIndicator() {
    const loadingSpinner = document.getElementById('loading-spinner');
    if (loadingSpinner) {
      loadingSpinner.classList.add('hidden');
    }
  }

  /**
   * Show AI modal with response
   */
  showAIModal(content, isError = false) {
    const aiModal = document.getElementById('ai-modal');
    const aiResult = document.getElementById('ai-result');

    if (aiModal && aiResult) {
      // Set content with appropriate styling
      if (isError) {
        aiResult.innerHTML = `<div class="text-red-400 p-4 bg-red-900 bg-opacity-30 rounded-lg">${content}</div>`;
      } else {
        // Format the content - if it looks like code, wrap in pre tags
        if (
          content.includes('```') ||
          content.includes('graph') ||
          content.includes('flowchart')
        ) {
          aiResult.innerHTML = `<pre class="bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm"><code>${content}</code></pre>`;
        } else {
          aiResult.innerHTML = `<div class="whitespace-pre-wrap">${content}</div>`;
        }
      }

      // Show modal
      aiModal.classList.remove('hidden');
    }
  }

  /**
   * Hide AI modal
   */
  hideAIModal() {
    const aiModal = document.getElementById('ai-modal');
    if (aiModal) {
      aiModal.classList.add('hidden');
    }
  }
}

// Initialize FastBoard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new FastBoard();
});
