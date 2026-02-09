/** Chat API client for the Todo AI Chatbot. */

interface ChatRequest {
  message: string;
  conversation_id?: string;
}

interface ToolCall {
  id: string;
  toolName: string;
  parameters: Record<string, any>;
  result: Record<string, any>;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  toolCalls: ToolCall[];
}

interface ChatResponse {
  conversationId: string;
  message: Message;
  toolCalls: ToolCall[];
  needClarification: boolean;
}

interface Conversation {
  id: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
}

class ChatClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl?: string) {
    // In production, use relative URL so requests go through Next.js rewrites proxy.
    this.baseUrl = baseUrl || (typeof window !== 'undefined' && process.env.NODE_ENV === 'production' ? '' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'));
  }

  /**
   * Set the authentication token for API requests.
   */
  setAuthToken(token: string) {
    this.authToken = token;
  }

  /**
   * Send a message to the AI assistant.
   */
  async sendMessage(userId: string, message: string, conversationId?: string): Promise<ChatResponse> {
    if (!userId || !message) {
      throw new Error('User ID and message are required');
    }

    const response = await fetch(`${this.baseUrl}/api/${userId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId || null,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // Transform snake_case response to camelCase
    const data = await response.json();
    return {
      conversationId: data.conversation_id,
      message: {
        id: data.message.id,
        role: data.message.role,
        content: data.message.content,
        createdAt: data.message.created_at,
        toolCalls: data.message.tool_calls || [],
      },
      toolCalls: data.tool_calls || [],
      needClarification: data.need_clarification || false,
    };
  }

  /**
   * Get a list of conversations for the user.
   */
  async getConversations(userId: string): Promise<Conversation[]> {
    if (!userId) {
      throw new Error('User ID is required');
    }

    const response = await fetch(`${this.baseUrl}/api/${userId}/conversations`, {
      headers: {
        ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Get a specific conversation with its messages.
   */
  async getConversation(userId: string, conversationId: string): Promise<any> {
    if (!userId || !conversationId) {
      throw new Error('User ID and conversation ID are required');
    }

    const response = await fetch(`${this.baseUrl}/api/${userId}/conversations/${conversationId}`, {
      headers: {
        ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Delete a specific conversation.
   */
  async deleteConversation(userId: string, conversationId: string): Promise<void> {
    if (!userId || !conversationId) {
      throw new Error('User ID and conversation ID are required');
    }

    const response = await fetch(`${this.baseUrl}/api/${userId}/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: {
        ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
  }
}

// Export a singleton instance
const chatClient = new ChatClient();

export { chatClient, ChatClient, type ChatRequest, type ChatResponse, type Message, type Conversation };