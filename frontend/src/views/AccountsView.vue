<template>
  <div class="accounts-view">
    <el-page-header title="邮箱账户" @back="$router.back()">
      <template #extra>
        <div class="flex-buttons">
          <el-button type="info" plain @click="handleGlobalProxy" class="ml-2">
            <el-icon><Connection /></el-icon>
            全局代理
          </el-button>
          
          <el-button type="success" @click="handleQuickAdd" class="ml-2">
            <el-icon><Link /></el-icon>
            微软极速添加
          </el-button>
          
          <el-button type="primary" @click="handleAdd" class="ml-2">
            <el-icon><Plus /></el-icon>
            添加账户
          </el-button>
        </div>
      </template>
    </el-page-header>

    <el-card class="mt-20">
      <!-- 工具栏 -->
      <div class="toolbar mb-4">
        <el-upload
          class="upload-demo"
          :action="uploadUrl"
          :headers="uploadHeaders"
          :show-file-list="false"
          accept=".csv"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
        >
          <el-button type="success" plain :loading="uploading">
            <el-icon><Upload /></el-icon>
            批量导入
          </el-button>
        </el-upload>
        
        <el-button type="warning" plain @click="handleBatchExport" :disabled="accounts.length === 0" :loading="exporting">
          <el-icon><Download /></el-icon>
          批量导出
        </el-button>
        
        <el-button type="danger" plain @click="handleFullExport" :disabled="accounts.length === 0" :loading="fullExporting">
          <el-icon><Lock /></el-icon>
          完整备份(含密码)
        </el-button>
        
        <el-button type="danger" plain @click="handleBatchDelete" :disabled="selectedIds.length === 0">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>

        <el-button type="warning" plain @click="handleSyncAll" :loading="syncingAll">
          <el-icon><Refresh /></el-icon>
          一键同步所有
        </el-button>
      </div>

      <el-empty v-if="!accounts.length && !loading" description="暂无邮箱账户">
        <el-button type="primary" @click="handleAdd">添加账户</el-button>
      </el-empty>

      <el-table v-else :data="accounts" style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="email_address" label="邮箱地址" min-width="200" />
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag :type="getProviderType(row.provider)">
              {{ getProviderLabel(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="auth_type" label="认证方式" width="120">
          <template #default="{ row }">
            <el-tag effect="plain" :type="row.auth_type === 'oauth2' ? 'warning' : 'info'">
              {{ row.auth_type === 'oauth2' ? 'OAuth2' : '密码' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- 代理列：显示代理地址（隐藏认证信息）并附带编辑按钮 -->
        <el-table-column label="代理" width="200">
          <template #default="{ row }">
            <div v-if="row.proxy_url" class="proxy-cell">
              <span class="proxy-text">{{ formatProxy(row.proxy_url) }}</span>
              <el-button
                size="small"
                type="primary"
                link
                @click="handleEditProxy(row)"
                title="编辑代理"
              >编辑</el-button>
            </div>
            <el-button
              v-else
              size="small"
              type="primary"
              link
              @click="handleEditProxy(row)"
            >设置代理</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="success" @click="handleSync(row)">同步</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 全局代理对话框 -->
    <el-dialog v-model="showGlobalProxyDialog" title="设置全局代理" width="500px">
      <el-form :model="globalProxyForm" label-width="80px">
        <el-form-item label="代理地址">
          <el-input v-model="globalProxyForm.url" placeholder="例如: socks5://user:pass@1.2.3.4:1080" />
          <div class="text-gray-400 text-xs mt-1">
            支持 http://, socks4://, socks5://。<br>留空表示禁用全局代理。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showGlobalProxyDialog = false">取消</el-button>
          <el-button type="primary" @click="saveGlobalProxy">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 独立代理对话框 -->
    <el-dialog v-model="proxyAccountDialogVisible" title="账户代理设置" width="500px">
      <el-form :model="proxyAccountForm" label-width="80px">
        <el-form-item label="代理地址">
          <el-input v-model="proxyAccountForm.url" placeholder="例如: socks5://user:pass@1.2.3.4:1080" clearable />
          <div class="text-gray-400 text-xs mt-1">
            留空使用全局代理。支持 http://, socks4://, socks5://
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="proxyAccountDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="handleClearProxy">清空代理</el-button>
          <el-button type="primary" :loading="submittingProxy" @click="saveAccountProxy">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑账户' : '添加账户'"
      width="600px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" style="width: 100%" :disabled="isQuickAdd">
            <el-option label="Microsoft 365 / Outlook" value="microsoft" />
            <template v-if="!isQuickAdd">
              <el-option label="Gmail" value="google" />
              <el-option label="IMAP / SMTP (通用)" value="imap" />
            </template>
          </el-select>
        </el-form-item>

        <el-form-item label="邮箱地址" prop="email_address">
          <el-input v-model="form.email_address" placeholder="example@email.com" />
        </el-form-item>

        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="form.display_name" placeholder="例如: 工作邮箱" />
        </el-form-item>

        <!-- 认证方式选择 -->
        <el-form-item label="认证方式">
          <el-radio-group v-model="form.auth_type">
            <el-radio label="password">密码 / 应用专用密码</el-radio>
            <el-radio label="oauth2">OAuth2 (Refresh Token)</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 密码模式 -->
        <template v-if="form.auth_type === 'password'">
          <el-divider content-position="left">服务器配置</el-divider>
          <el-form-item label="IMAP 服务器" prop="imap_server">
            <el-input v-model="form.imap_server" placeholder="imap.example.com" />
          </el-form-item>
          <el-form-item label="IMAP 端口" prop="imap_port">
            <el-input-number v-model="form.imap_port" :min="1" :max="65535" controls-position="right" />
          </el-form-item>
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="通常是邮箱地址" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password />
          </el-form-item>
        </template>

        <!-- OAuth2 模式 -->
        <template v-else>
          <el-divider content-position="left">OAuth2 配置</el-divider>
          
          <el-alert 
            title="推荐：点击下方按钮直接登录获取 Token" 
            type="info" 
            show-icon 
            :closable="false" 
            class="mb-4" 
          />
          
          <el-form-item label="Client ID" prop="client_id">
            <el-input v-model="form.client_id" placeholder="Azure Client ID" />
          </el-form-item>
          
          <el-form-item label="Client Secret" prop="client_secret">
            <el-input v-model="form.client_secret" placeholder="Azure Client Secret (Web应用必填，公共客户端留空)" type="password" show-password />
          </el-form-item>
          
          <el-form-item v-if="isQuickAdd">
            <el-button type="primary" plain @click="handleMicrosoftLogin" :disabled="!form.client_id">
              <el-icon class="mr-1"><Link /></el-icon>
              去微软登录获取 Token
            </el-button>
          </el-form-item>

          <el-form-item label="Refresh Token" prop="refresh_token">
            <el-input 
              v-model="form.refresh_token" 
              type="textarea" 
              :rows="3" 
              placeholder="点击上方按钮登录后会自动填充，或者手动粘贴" 
            />
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '立即添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, Upload, Link, Refresh, Delete, Connection, Lock, Download } from '@element-plus/icons-vue'
import * as accountsApi from '@/api/accounts'
import * as settingsApi from '@/api/settings'
import { useAuthStore } from '@/stores/auth'
import type { EmailAccount } from '@/types'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const accounts = ref<EmailAccount[]>([])
const loading = ref(false)
const submitting = ref(false)
const uploading = ref(false)
const exporting = ref(false)
const fullExporting = ref(false)
const syncingAll = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const isQuickAdd = ref(false)
const formRef = ref<FormInstance>()

// 上传相关
const uploadUrl = '/api/v1/accounts/batch-import'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.token}`
}))

const form = reactive({
  id: null as number | null,
  provider: 'microsoft',
  email_address: '',
  display_name: '',
  auth_type: 'oauth2',
  // Password
  imap_server: '',
  imap_port: 993,
  username: '',
  password: '',
  proxy_url: '',
  // OAuth
  client_id: '',
  client_secret: '',
  refresh_token: ''
})

const rules = {
  email_address: [{ required: true, message: '请输入邮箱地址', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
}

// 监听 Provider 变化，自动切换认证方式和填充默认值
watch(() => form.provider, (val) => {
  if (val === 'microsoft') {
    form.auth_type = 'oauth2'
    form.imap_server = 'outlook.office365.com'
    form.imap_port = 993
  } else if (val === 'google') {
    form.auth_type = 'password'  // Gmail 使用应用专用密码
    form.imap_server = 'imap.gmail.com'
    form.imap_port = 993
  } else {
    form.auth_type = 'password'
    form.imap_server = ''
    form.imap_port = 993
  }
})

// 通用 CSV 构建
const buildCsv = (headers: string[], rows: Array<Array<string | number>>) => {
  return [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
  ].join('\n')
}

// ... 辅助函数 ...
const getProviderType = (provider: string) => {
  const map: Record<string, string> = { microsoft: 'primary', google: 'success', imap: 'warning' }
  return map[provider] || ''
}
const getProviderLabel = (provider: string) => {
  const map: Record<string, string> = { microsoft: 'Microsoft', google: 'Gmail', imap: 'IMAP' }
  return map[provider] || provider
}
const getStatusType = (status: string) => {
  const map: Record<string, string> = { active: 'success', error: 'danger', syncing: 'warning', auth_required: 'danger' }
  return map[status] || 'info'
}
const getStatusLabel = (status: string) => {
  const map: Record<string, string> = { active: '正常', error: '错误', syncing: '同步中', auth_required: '认证失败' }
  return map[status] || status
}

async function withConcurrencyLimit<T>(items: T[], limit: number, fn: (item: T) => Promise<void>) {
  const queue = [...items]
  const workers = Array(Math.min(limit, items.length)).fill(0).map(async function() {
    while (queue.length) {
      const item = queue.shift()
      if (item !== undefined) {
        await fn(item)
      }
    }
  })
  await Promise.all(workers)
}

const selectedIds = ref<number[]>([])

const handleSelectionChange = (selection: any[]) => {
  selectedIds.value = selection.map(item => item.id)
}

const handleBatchDelete = () => {
  ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个账户吗？`, '警告', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  }).then(async () => {
    loading.value = true
    let successCount = 0
    await withConcurrencyLimit(selectedIds.value, 3, async (id) => {
      try {
        await accountsApi.deleteAccount(id)
        successCount++
      } catch (e) {
        // Ignore errors
      }
    })
    ElMessage.success(`成功删除 ${successCount} 个账户`)
    loadAccounts()
  }).finally(() => {
    loading.value = false
  })
}

const handleSyncAll = () => {
  if (accounts.value.length === 0) {
    ElMessage.warning('暂无账户')
    return
  }
  syncingAll.value = true
  let count = 0
  withConcurrencyLimit(accounts.value.filter(a => a.status !== 'disabled'), 3, async (acc) => {
    try {
      await accountsApi.syncAccount(acc.id)
      count++
    } catch {}
  }).then(() => {
    ElMessage.success(`已触发 ${count} 个账户的同步`)
    syncingAll.value = false
  })
}

const showGlobalProxyDialog = ref(false)
const globalProxyForm = reactive({ url: '' })

const handleGlobalProxy = async () => {
  try {
    const res = await settingsApi.getSetting('global_proxy')
    globalProxyForm.url = res.data?.value || ''
    showGlobalProxyDialog.value = true
  } catch (e) {
    ElMessage.error('无法获取全局代理设置')
  }
}

const saveGlobalProxy = async () => {
  try {
    await settingsApi.updateSetting('global_proxy', globalProxyForm.url)
    ElMessage.success('全局代理保存成功')
    showGlobalProxyDialog.value = false
  } catch (e) {
    ElMessage.error('保存全局代理失败')
  }
}

const handleAdd = () => {
  isEdit.value = false
  isQuickAdd.value = false
  form.id = null
  // 默认为 Microsoft
  form.provider = 'microsoft'
  form.auth_type = 'oauth2'
  form.email_address = ''
  form.display_name = ''
  form.imap_server = 'outlook.office365.com'
  form.imap_port = 993
  form.username = ''
  form.password = ''
  form.proxy_url = ''
  
  // 普通添加: 不自动填充 Client ID/Secret
  form.client_id = ''
  form.client_secret = ''
  form.refresh_token = ''
  dialogVisible.value = true
}

const handleQuickAdd = async () => {
  // 极速添加: 自动填充 Client ID/Secret
  isEdit.value = false
  isQuickAdd.value = true
  form.id = null
  form.provider = 'microsoft'
  form.auth_type = 'oauth2'
  form.email_address = ''
  form.display_name = ''
  form.imap_server = ''
  form.imap_port = 993
  form.username = ''
  form.password = ''
  
  // 1. 优先查 LocalStorage
  let cid = localStorage.getItem('oauth_client_id') || ''
  let sec = localStorage.getItem('oauth_client_secret') || ''
  
  // 2. 如果没有，查后台数据库
  if (!cid) {
    try {
      const creds = await accountsApi.getDefaultCredentials('microsoft')
      if (creds && creds.client_id) {
        cid = creds.client_id
        sec = creds.client_secret || ''
        // 同步回 LocalStorage
        localStorage.setItem('oauth_client_id', cid)
        localStorage.setItem('oauth_client_secret', sec)
      }
    } catch (e) {
      // Ignore
    }
  }
  
  form.client_id = cid
  form.client_secret = sec
  form.refresh_token = ''
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  isQuickAdd.value = false
  Object.assign(form, row)
  // 补全默认值
  form.auth_type = row.auth_type || 'password'
  form.username = row.imap_username || row.email_address
  form.password = '' // 不回显密码
  // form.proxy_url = row.proxy_url || '' // proxy moved to separate dialog
  dialogVisible.value = true
}

const loadAccounts = async () => {
  loading.value = true
  try {
    const res = await accountsApi.listAccounts({ page: 1, page_size: 50 })
    accounts.value = (res as any).data || []
  } catch (err: any) {
    ElMessage.error('加载账户失败')
  } finally {
    loading.value = false
  }
}

const handleMicrosoftLogin = () => {
  if (!form.client_id) {
    ElMessage.warning('请先填写 Client ID')
    return
  }
  
  // 1. 保存当前的 Client ID/Secret 到 localStorage，供回调页面使用
  localStorage.setItem('oauth_client_id', form.client_id)
  localStorage.setItem('oauth_client_secret', form.client_secret || '')
  
  // 保存表单其他字段，以便回来后恢复
  localStorage.setItem('oauth_form_data', JSON.stringify({
    email_address: form.email_address,
    display_name: form.display_name
  }))
  
  // 2. 构造 Microsoft OAuth URL
  const redirectUri = window.location.origin + '/auth/callback'
  // 改用 Graph API 权限: Mail.Read (读取邮件), Mail.Send (发送邮件), User.Read (读取用户), offline_access (刷新令牌)
  const scope = 'offline_access https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/User.Read'
  const authUrl = `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=${form.client_id}&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&response_mode=query`
  
  // 3. 跳转
  window.location.href = authUrl
}

const proxyAccountDialogVisible = ref(false)
const proxyAccountForm = reactive({ id: 0, url: '' })
const submittingProxy = ref(false)

const handleEditProxy = (row: any) => {
  proxyAccountForm.id = row.id
  proxyAccountForm.url = row.proxy_url || ''
  proxyAccountDialogVisible.value = true
}

const saveAccountProxy = async () => {
  if (!proxyAccountForm.id) return
  submittingProxy.value = true
  try {
    await accountsApi.updateAccount(proxyAccountForm.id, { proxy_url: proxyAccountForm.url })
    ElMessage.success('代理设置已保存')
    proxyAccountDialogVisible.value = false
    loadAccounts()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    submittingProxy.value = false
  }
}

// 检查是否是从 OAuth 回调跳转回来的
onMounted(() => {
  loadAccounts()
  
  if (route.query.oauth_success === '1') {
    const oauthResult = localStorage.getItem('oauth_result')
    if (oauthResult) {
      try {
        const tokens = JSON.parse(oauthResult)
        // 自动打开对话框并填充
        handleAdd()
        form.provider = 'microsoft'
        form.auth_type = 'oauth2'
        form.client_id = tokens.client_id
        form.client_secret = tokens.client_secret
        form.refresh_token = tokens.refresh_token
        
        // 恢复之前保存的表单数据
        const savedForm = localStorage.getItem('oauth_form_data')
        if (savedForm) {
          const parsed = JSON.parse(savedForm)
          if (parsed.email_address) form.email_address = parsed.email_address
          if (parsed.display_name) form.display_name = parsed.display_name
          localStorage.removeItem('oauth_form_data')
        }
        
        ElMessage.success('已自动填充 Refresh Token')
        
        // 清除临时存储
        localStorage.removeItem('oauth_result')
        
        // 清除 URL 参数 (避免刷新重复触发)
        router.replace({ query: {} })
      } catch (e) {
        console.error('Invalid oauth result', e)
      }
    }
  }
})

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const payload = { ...form }
      if (isEdit.value && form.id) {
        await accountsApi.updateAccount(form.id, payload)
        ElMessage.success('更新成功')
      } else {
        await accountsApi.createAccount(payload)
        ElMessage.success('添加成功')
      }
      dialogVisible.value = false
      loadAccounts()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleSync = async (row: any) => {
  try {
    await accountsApi.syncAccount(row.id)
    ElMessage.success('已触发同步')
  } catch (err: any) {
    ElMessage.error('同步失败')
  }
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除吗？', '警告', { type: 'warning' })
    .then(async () => {
      await accountsApi.deleteAccount(row.id)
      ElMessage.success('删除成功')
      loadAccounts()
    })
}

// 批量上传处理
const beforeUpload = () => {
  uploading.value = true
  return true
}

const handleFullExport = () => {
  if (accounts.value.length === 0) {
    ElMessage.warning('没有可导出的账户')
    return
  }

  // 安全警告
  ElMessageBox.confirm(
    '完整备份将包含密码、Token等敏感信息。请妥善保管此文件，避免泄露！',
    '安全警告',
    {
      confirmButtonText: '我已了解风险，继续导出',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    doFullExport()
  }).catch(() => {
    ElMessage.info('已取消导出')
  })
}

const doFullExport = async () => {
  fullExporting.value = true
  ElMessage.info('正在获取完整数据...')

  try {
    // 调用 API 获取包含敏感信息的完整数据
    const response = await accountsApi.exportFullAccounts()
    const fullAccounts = (response as any).data || []
    
    if (!fullAccounts.length) {
      ElMessage.warning('没有可导出的账户')
      return
    }

    // 简化导出：只保留 4 个字段
    const headers = ['账号', '密码', 'client_id', 'refresh_token']

    const rows = fullAccounts.map((acc: any) => {
      // 判断是 OAuth 还是密码认证（兼容大小写）
      const authType = String(acc.auth_type || '').toLowerCase()
      const isOAuth = authType.includes('oauth')
      
      // 密码：OAuth 留空，密码认证用 imap_password
      const password = isOAuth 
        ? ''
        : (acc.imap_password || '')
      
      return [
        acc.email_address || '',           // 账号
        password,                           // 密码（OAuth 留空）
        acc.client_id || '',                // client_id
        acc.refresh_token || ''             // refresh_token（OAuth 用）
      ]
    })

    // 生成 CSV 内容
    const csvContent = buildCsv(headers, rows)

    // 创建并下载文件
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `mailbox_backup_${new Date().toISOString().slice(0,10)}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    
    ElMessage.success(`完整备份成功：${rows.length} 个账户`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    fullExporting.value = false
  }
}
const handleUploadSuccess = (res: any) => {
  uploading.value = false
  if (res.success) {
    ElMessageBox.alert(
      `导入成功: ${res.imported} 个\n错误: ${res.errors.length} 个\n${res.errors.join('\n')}`,
      '批量导入结果',
      { confirmButtonText: '确定' }
    )
    loadAccounts()
  } else {
    ElMessage.error('导入失败')
  }
}
const handleUploadError = (err: any) => {
  uploading.value = false
  ElMessage.error('上传失败，请检查文件格式')
}

const handleBatchExport = async () => {
  // 检查是否有选中的账户
  const exportIds = selectedIds.value.length > 0 ? selectedIds.value : accounts.value.map(a => a.id)
  
  if (exportIds.length === 0) {
    ElMessage.warning('没有可导出的账户')
    return
  }

  // 安全警告
  ElMessageBox.confirm(
    `将导出 ${exportIds.length} 个账户的完整信息（包含密码、Token等敏感信息）。请妥善保管此文件！`,
    '安全警告',
    {
      confirmButtonText: '我已了解风险，继续导出',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    doBatchExport(exportIds)
  }).catch(() => {
    ElMessage.info('已取消导出')
  })
}

const doBatchExport = async (exportIds: number[]) => {
  exporting.value = true
  ElMessage.info('正在获取完整数据...')

  try {
    // 调用 API 获取包含敏感信息的完整数据
    const response = await accountsApi.exportFullAccounts()
    const fullAccounts = (response as any).data || []
    
    // 只导出选中的账户
    const selectedAccounts = fullAccounts.filter((acc: any) => exportIds.includes(acc.id))
    
    if (!selectedAccounts.length) {
      ElMessage.warning('没有可导出的账户')
      return
    }

    // 简化导出：只保留 4 个字段
    const headers = ['账号', '密码', 'client_id', 'refresh_token']

    const rows = selectedAccounts.map((acc: any) => {
      // 判断是 OAuth 还是密码认证（兼容大小写）
      const authType = String(acc.auth_type || '').toLowerCase()
      const isOAuth = authType.includes('oauth')
      
      // 密码：OAuth 留空，密码认证用 imap_password
      const password = isOAuth 
        ? ''
        : (acc.imap_password || '')
      
      return [
        acc.email_address || '',           // 账号
        password,                           // 密码（OAuth 留空）
        acc.client_id || '',                // client_id
        acc.refresh_token || ''             // refresh_token（OAuth 用）
      ]
    })

    // 生成 CSV 内容
    const csvContent = buildCsv(headers, rows)

    // 创建并下载文件
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `mailbox_export_${new Date().toISOString().slice(0,10)}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    URL.revokeObjectURL(url)
    
    ElMessage.success(`成功导出 ${rows.length} 个账户`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadAccounts()
})

// 格式化代理地址，隐藏认证信息
const formatProxy = (url: string) => {
  try {
    const u = new URL(url)
    return `${u.protocol}//${u.host}`
  } catch {
    return url
  }
}

// 清空代理（在对话框中）
const handleClearProxy = async () => {
  if (!proxyAccountForm.id) return
  
  ElMessageBox.confirm('确定要清空该账户的代理吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    submittingProxy.value = true
    try {
      await accountsApi.updateAccount(proxyAccountForm.id, { proxy_url: '' })
      ElMessage.success('代理已清空')
      proxyAccountDialogVisible.value = false
      await loadAccounts()
    } catch (err) {
      console.error('清空代理失败', err)
      ElMessage.error('清空代理失败')
    } finally {
      submittingProxy.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.accounts-view {
  .mt-20 { margin-top: 20px; }
  .flex-buttons { display: flex; align-items: center; }
  .ml-2 { margin-left: 10px; }
  .mb-4 { margin-bottom: 16px; }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}
</style>
