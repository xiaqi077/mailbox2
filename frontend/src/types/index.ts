/**
 * TypeScript 类型定义
 */

// 用户类型
export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  must_change_password?: boolean
  created_at: string
  updated_at: string
  last_login_at?: string
}

// 认证类型
export interface LoginCredentials {
  username: string
  password: string
  remember?: boolean
}

export interface RegisterData {
  username: string
  email: string
  password: string
  password_confirm: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// 邮箱账户类型
export type ProviderType = 'microsoft' | 'google' | 'imap'
export type AccountStatus = 'active' | 'error' | 'syncing' | 'disabled' | 'auth_required'

export interface EmailAccount {
  id: number
  user_id: number
  email_address: string
  display_name?: string
  provider: ProviderType
  status: AccountStatus
  status_message?: string
  sync_enabled: boolean
  last_sync_at?: string
  sync_folder: string
  total_emails: number
  unread_count: number
  storage_used: number
  proxy_url?: string
  created_at: string
  updated_at: string
}

// 邮件类型
export interface Email {
  id: number
  account_id: number
  folder_id: number
  uid: string
  message_id?: string
  thread_id?: string
  subject?: string
  from_name?: string
  from_address: string
  to_addresses: string
  cc_addresses?: string
  bcc_addresses?: string
  reply_to?: string
  body_text?: string
  body_html?: string
  is_read: boolean
  is_flagged: boolean
  is_deleted: boolean
  has_attachments: boolean
  attachments_count: number
  size_bytes?: number
  sent_at?: string
  received_at?: string
  created_at: string
  updated_at: string
  account_email?: string
  account_provider?: string
}

// 文件夹类型
export interface Folder {
  id: number
  account_id: number
  name: string
  path: string
  is_system: boolean
  folder_type?: string
  total_count: number
  unread_count: number
  last_sync_at?: string
  created_at: string
  updated_at: string
}

// API 响应类型
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: number
    message: string
  }
  pagination?: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: 'connected' | 'disconnected' | 'notification' | 'sync_progress' | 'error'
  data?: any
  timestamp: string
}

// 搜索参数类型
export interface EmailSearchParams {
  q?: string
  account_id?: number
  folder_id?: number
  is_read?: boolean
  is_flagged?: boolean
  has_attachments?: boolean
  from?: string
  to?: string
  subject?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
  sort_by?: 'date' | 'subject' | 'from' | 'size'
  sort_order?: 'asc' | 'desc'
}