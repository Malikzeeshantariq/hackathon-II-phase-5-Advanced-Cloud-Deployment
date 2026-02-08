"use client";
/** ChatPanel component for the Todo AI Chatbot. */

import { useState, useRef, useEffect } from 'react';
import { useSession } from '@/lib/auth';
import { chatClient } from '@/lib/chat-client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

interface ToolCall {
  id: string;
  toolName: string;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
}

const ChatPanel = () => {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const userId = session?.user?.id;

  // Scroll to bottom of messages when they change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || isLoading) return;

    if (!userId) {
      setError('Please log in to use the chat.');
      return;
    }

    // Clear any previous errors
    setError(null);

    // Add user message to the chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      createdAt: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      // Call the real chat API
      const response = await chatClient.sendMessage(
        userId,
        messageText,
        conversationId || undefined
      );

      // Update conversation ID if it changed
      if (response.conversationId && !conversationId) {
        setConversationId(response.conversationId);
      }

      // Add assistant message to the chat
      const assistantMessage: Message = {
        id: response.message.id || Date.now().toString(),
        role: 'assistant',
        content: response.message.content,
        createdAt: response.message.createdAt || new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error sending message:', err);

      // Add error message to the chat
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        createdAt: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  // Show login prompt if not authenticated
  if (!session) {
    return (
      <div className="flex flex-col h-full bg-white rounded-lg shadow-md items-center justify-center p-8">
        <div className="text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-700 mb-2">Login Required</h3>
          <p className="text-gray-600 mb-4">Please log in to use the AI Task Assistant.</p>
          <a
            href="/login"
            className="inline-block bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Log In
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md">
      {/* Chat Header */}
      <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 rounded-t-lg">
        <h2 className="text-lg font-semibold text-gray-800">AI Task Assistant</h2>
        <p className="text-sm text-gray-600">Ask me to create, list, complete, delete, or update tasks</p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-700">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <div className="mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-700 mb-1">Welcome to your AI Task Assistant!</h3>
            <p className="text-gray-600 max-w-md">
              I can help you manage your tasks using natural language. Try asking me to create, list, complete, delete, or update tasks.
            </p>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-2 text-left text-sm text-gray-600">
              <div className="bg-blue-50 p-2 rounded">&bull; Add a task to buy groceries</div>
              <div className="bg-blue-50 p-2 rounded">&bull; Show my tasks</div>
              <div className="bg-blue-50 p-2 rounded">&bull; Complete task &quot;buy groceries&quot;</div>
              <div className="bg-blue-50 p-2 rounded">&bull; Delete the report task</div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white rounded-br-none'
                    : 'bg-gray-200 text-gray-800 rounded-bl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                <div className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-500'}`}>
                  {new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-800 rounded-lg rounded-bl-none px-4 py-2 max-w-[80%]">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white rounded-b-lg">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message here..."
            className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className={`px-4 py-2 rounded-r-lg font-medium ${
              inputValue.trim() && !isLoading
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Send
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Example: &quot;Add a task to buy groceries&quot; or &quot;Show my tasks&quot;
        </p>
      </div>
    </div>
  );
};

export default ChatPanel;
