import { api } from './api'
import type { ChatRequest, ChatResponse, Conversation, ConversationSummary } from '@/types'

export const chatService = {
  async send(data: ChatRequest): Promise<ChatResponse> {
    const res = await api.post<ChatResponse>('/chat', data)
    return res.data
  },

  async getHistory(): Promise<ConversationSummary[]> {
    const res = await api.get<ConversationSummary[]>('/chat/history')
    return res.data
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await api.get<Conversation>(`/chat/conversation/${id}`)
    return res.data
  },
}
