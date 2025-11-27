/**
 * ChatContainer - huvudkomponent för chat-gränssnittet
 */
import { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { sendChatMessage, checkHealth } from '../services/api';
import type { ChatMessage as ChatMessageType } from '../types/chat';

export default function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef<string>(`session-${Date.now()}`);

  // Scrolla till botten när nya meddelanden läggs till
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Kontrollera backend-status vid start
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await checkHealth();
        setIsBackendReady(health.model_loaded);
        if (!health.model_loaded) {
          setError('AI-modellen laddar fortfarande. Vänta en stund och ladda om sidan.');
        }
      } catch (err) {
        setError('Kan inte ansluta till backend. Kontrollera att servern körs på http://localhost:8000');
        console.error('Health check failed:', err);
      }
    };

    checkBackend();
  }, []);

  const handleSendMessage = async (question: string) => {
    if (!isBackendReady) {
      setError('Backend är inte redo ännu. Vänta en stund.');
      return;
    }

    // Skapa temporary message med loading state
    const tempId = `temp-${Date.now()}`;
    const tempMessage: ChatMessageType = {
      id: tempId,
      question,
      answer: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, tempMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(question, sessionId.current);

      // Uppdatera meddelandet med svaret
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempId
            ? {
                ...msg,
                id: `${Date.now()}`,
                answer: response.answer,
                timestamp: new Date(response.timestamp),
                isLoading: false,
              }
            : msg
        )
      );
    } catch (err: any) {
      console.error('Error sending message:', err);
      setError(
        err.response?.data?.detail ||
          'Ett fel uppstod när meddelandet skulle skickas. Försök igen.'
      );

      // Ta bort temporary message vid fel
      setMessages((prev) => prev.filter((msg) => msg.id !== tempId));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Chat widget container - fixed bottom right */}
      <div className="fixed bottom-4 right-4 w-96 h-[500px] bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-4 shadow-lg">
          <h1 className="text-xl font-bold">Husqvarna Motorsåg Chatbot</h1>
          <p className="text-xs text-orange-100 mt-1">
            Ställ frågor om Husqvarna 365 motorsågen
          </p>
          {!isBackendReady && (
            <div className="mt-2 bg-yellow-500 text-yellow-900 px-2 py-1 rounded text-xs inline-block">
              ⚠️ AI-modellen laddar...
            </div>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 mx-3 mt-3 rounded text-sm">
            <p>{error}</p>
          </div>
        )}

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <svg
                  className="mx-auto h-10 w-10 text-gray-400 mb-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
                <p className="text-base font-medium">Välkommen!</p>
                <p className="text-sm mt-1">
                  Ställ din första fråga nedan
                </p>
                <div className="mt-3 text-xs text-gray-400">
                  <p>Exempel: "Hur byter man kedjan?"</p>
                  <p>"Vilken kedja behöver jag?"</p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input area */}
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading || !isBackendReady} />
      </div>
    </div>
  );
}
