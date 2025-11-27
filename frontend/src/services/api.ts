/**
 * API service för att kommunicera med backend
 */
import axios from 'axios';
import type { ChatRequest, ChatResponse, HealthResponse } from '../types/chat';

// I Docker används relativ URL (nginx proxar till backend), lokalt används localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';
const API_VERSION = '/api/v1';

// Skapa axios instance med base URL
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_VERSION}`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 sekunder timeout (modellen kan ta tid)
});

/**
 * Kontrollera om API:et är igång och redo
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health/');
  return response.data;
};

/**
 * Skicka en fråga till chatboten
 */
export const sendChatMessage = async (
  question: string,
  sessionId?: string
): Promise<ChatResponse> => {
  const request: ChatRequest = {
    question,
    session_id: sessionId,
  };

  const response = await apiClient.post<ChatResponse>('/chat/', request);
  return response.data;
};

export default {
  checkHealth,
  sendChatMessage,
};
