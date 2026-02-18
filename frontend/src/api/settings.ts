import api from './index'
import type { ApiResponse } from '@/types'

export interface SettingData {
  key: string
  value: string
}

export async function getSetting(key: string): Promise<ApiResponse<SettingData>> {
  const response = await api.get(`/settings/${key}`)
  return response.data
}

export async function updateSetting(key: string, value: string): Promise<ApiResponse<SettingData>> {
  const response = await api.put(`/settings/${key}`, { value })
  return response.data
}
