<template>
  <div class="emails-view">
    <!-- 1. 账户列表视图 -->
    <div v-if="!currentAccount">
      <el-page-header title="账户看板" :icon="null">
        <template #extra>
          <el-button type="primary" :loading="syncing" @click="handleSyncAll">
            <el-icon><Refresh /></el-icon>
            同步所有
          </el-button>
        </template>
      </el-page-header>

      <el-card class="mt-20">
        <el-table :data="accounts" v-loading="loadingAccounts" stripe style="width: 100%">
          <el-table-column prop="id" label="序号" width="80" align="center" sortable />
          
          <el-table-column prop="email_address" label="邮箱账户" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">
              <span style="font-weight: 600">{{ row.email_address }}</span>
              <el-tag v-if="row.display_name" size="small" type="info" class="ml-2">{{ row.display_name }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="快捷入口" width="280" align="center">
            <template #default="{ row }">
              <el-button type="success" plain size="small" :loading="syncingMap[row.id]" @click="handleSyncOne(row)">
                <el-icon><Refresh /></el-icon>
              </el-button>
              <el-button type="primary" plain size="small" @click="enterAccount(row, 'inbox')">
                <el-icon class="mr-1"><Message /></el-icon> 收件箱
              </el-button>
              <el-button type="danger" plain size="small" @click="enterAccount(row, 'trash')">
                <el-icon class="mr-1"><Delete /></el-icon> 垃圾箱
              </el-button>
            </template>
          </el-table-column>
          
          <el-table-column label="最新验证码" min-width="250">
            <template #default="{ row }">
              <div v-if="codes[row.id]?.loading" class="text-gray">
                <el-icon class="is-loading"><Loading /></el-icon> 提取中...
              </div>
              <div v-else-if="codes[row.id]?.code" class="code-box">
                <span class="code-value">{{ codes[row.id].code }}</span>
                <el-tooltip :content="`来自: ${codes[row.id].subject}`" placement="top">
                  <el-icon class="ml-1 text-gray" style="cursor: pointer"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div v-else class="text-gray-light">无验证码</div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 2. 邮件列表视图 -->
    <div v-else>
      <el-page-header :title="`${currentAccount.email_address} - ${folderName}`" @back="exitAccount">
        <template #extra>
          <el-button @click="loadEmails">
            <el-icon><Refresh /></el-icon> 刷新列表
          </el-button>
          <el-button type="danger" plain @click="handleClear">
            <el-icon><Delete /></el-icon> 清空{{ folderName }}
          </el-button>
        </template>
      </el-page-header>

      <el-card class="mt-20">
        <div class="filters">
          <el-input v-model="filters.q" placeholder="搜索主题/发件人" clearable @keyup.enter="handleSearch" style="width: 250px" />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>

        <el-table :data="emails" v-loading="loading" style="width: 100%" @row-click="goDetail" stripe>
          <el-table-column prop="subject" label="主题" min-width="300" show-overflow-tooltip>
            <template #default="{ row }">
              <span :class="{ 'unread-bold': !row.is_read }">{{ row.subject || '(无主题)' }}</span>
              <el-tag v-if="row.has_attachments" size="small" type="info" effect="plain" class="ml-1"><el-icon><Paperclip /></el-icon></el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="from_address" label="发件人" width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.from_name || row.from_address }}
            </template>
          </el-table-column>
          
          <el-table-column prop="received_at" label="时间" width="160">
            <template #default="{ row }">
              {{ formatTime(row.received_at) }}
            </template>
          </el-table-column>
          
          <el-table-column width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_read ? 'info' : 'danger'" effect="light">
                {{ row.is_read ? '已读' : '未读' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="loadEmails"
            @current-change="loadEmails"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Message, Delete, Paperclip, Search, Loading, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as emailsApi from '@/api/emails'
import * as accountsApi from '@/api/accounts'
import type { Email, EmailAccount } from '@/types'

const router = useRouter()

// 状态
const currentAccount = ref<EmailAccount | null>(null)
const currentFolder = ref<'inbox' | 'trash'>('inbox')
const accounts = ref<EmailAccount[]>([])
const loadingAccounts = ref(false)
const syncing = ref(false)
const syncingMap = reactive<Record<number, boolean>>({})

// 文件夹状态
const folders = ref<any[]>([])
const inboxFolderId = ref<number | null>(null)
const junkFolderId = ref<number | null>(null)

// 验证码缓存
const codes = reactive<Record<number, { code: string, loading: boolean, subject?: string }>>({})

// 邮件列表状态
const emails = ref<Email[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filters = reactive({
  q: '',
})

// 计算属性
const folderName = computed(() => currentFolder.value === 'inbox' ? '收件箱' : '垃圾箱 (已删除)')

// 方法
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const loadAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await accountsApi.listAccounts({ page: 1, page_size: 100 })
    accounts.value = Array.isArray(res) ? res : (res as any).data || []
    
    // 加载完账户后，自动提取验证码
    fetchCodes()
  } catch (e) {
    ElMessage.error('加载账户失败')
  } finally {
    loadingAccounts.value = false
  }
}

const fetchCodes = async () => {
  for (const acc of accounts.value) {
    if (acc.status === 'active') {
      codes[acc.id] = { code: '', loading: true }
      try {
        const res = await accountsApi.getLatestCode(acc.id)
        if (res && res.success && res.code) {
          codes[acc.id] = { code: res.code, loading: false, subject: res.email_subject }
        } else {
          codes[acc.id] = { code: '', loading: false }
        }
      } catch (e) {
        codes[acc.id] = { code: '', loading: false }
      }
    }
  }
}

const enterAccount = (acc: EmailAccount, folder: 'inbox' | 'trash') => {
  currentAccount.value = acc
  currentFolder.value = folder
  currentPage.value = 1
  filters.q = ''
  loadFolders()
}

const loadFolders = async () => {
  if (!currentAccount.value) return
  
  try {
    const res = await fetch(`/api/v1/folders/?account_id=${currentAccount.value.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await res.json()
    folders.value = data.data || []
    
    // 找到收件箱和垃圾箱的 folder_id
    const inbox = folders.value.find((f: any) => f.folder_type === 'inbox')
    const junk = folders.value.find((f: any) => f.folder_type === 'spam')
    
    inboxFolderId.value = inbox?.id || null
    junkFolderId.value = junk?.id || null
    
    // 加载邮件
    loadEmails()
  } catch (e) {
    ElMessage.error('加载文件夹失败')
    loadEmails()
  }
}

const exitAccount = () => {
  currentAccount.value = null
  emails.value = []
}

const loadEmails = async () => {
  if (!currentAccount.value) return
  
  loading.value = true
  try {
    const isTrash = currentFolder.value === 'trash'
    
    // 根据文件夹类型选择 folder_id
    let folderId: number | undefined
    if (isTrash && junkFolderId.value) {
      folderId = junkFolderId.value
    } else if (!isTrash && inboxFolderId.value) {
      folderId = inboxFolderId.value
    }
    
    const res = await emailsApi.listEmails({
      page: currentPage.value,
      page_size: pageSize.value,
      account_id: currentAccount.value.id,
      folder_id: folderId,
      q: filters.q || undefined,
    })
    
    emails.value = res.data || []
    total.value = res.pagination?.total || 0
  } catch (err) {
    ElMessage.error('加载邮件失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadEmails()
}

const handleSyncOne = async (acc: EmailAccount) => {
  syncingMap[acc.id] = true
  try {
    await accountsApi.syncAccount(acc.id)
    ElMessage.success('已触发同步')
    
    // 3秒后刷新该账户的验证码
    setTimeout(async () => {
      codes[acc.id] = { code: '', loading: true }
      try {
        const res = await accountsApi.getLatestCode(acc.id)
        if (res && res.success && res.code) {
          codes[acc.id] = { code: res.code, loading: false, subject: res.email_subject }
        } else {
          codes[acc.id] = { code: '', loading: false }
        }
      } catch (e) {
        codes[acc.id] = { code: '', loading: false }
      }
      syncingMap[acc.id] = false
    }, 3000)
    
  } catch (e) {
    ElMessage.error('同步失败')
    syncingMap[acc.id] = false
  }
}

const handleSyncAll = async () => {
  syncing.value = true
  let count = 0
  for (const acc of accounts.value) {
    if (acc.status !== 'disabled') {
      accountsApi.syncAccount(acc.id).catch(() => {})
      count++
    }
  }
  ElMessage.success(`已触发 ${count} 个账户同步`)
  setTimeout(() => { 
    syncing.value = false 
    // 刷新验证码
    fetchCodes()
  }, 3000)
}

const handleClear = () => {
  if (!currentAccount.value) return
  const isTrash = currentFolder.value === 'trash'
  const action = isTrash ? '彻底删除' : '清空'
  const target = isTrash ? '垃圾箱中的' : '收件箱中的'
  
  ElMessageBox.confirm(
    `确定要${action}${target}所有邮件吗？${isTrash ? '此操作不可恢复！' : '邮件将移至垃圾箱。'}`,
    '高风险操作',
    {
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    loading.value = true
    try {
      await emailsApi.clearEmails(currentAccount.value.id, isTrash)
      ElMessage.success('操作成功')
      loadEmails()
    } catch (e) {
      ElMessage.error('操作失败')
      loading.value = false
    }
  }).catch(() => {})
}

const goDetail = (row: Email) => {
  if (row?.id) {
    router.push(`/emails/${row.id}`)
  }
}

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped lang="scss">
.emails-view {
  max-width: 1200px;
  margin: 0 auto;

  .mt-20 { 
    margin-top: 24px; 
    border-radius: 12px;
    border: none;
  }
  
  .filters { 
    display: flex; 
    gap: 12px; 
    margin-bottom: 24px; 
    align-items: center; 
    background: #fff;
    padding: 16px;
    border-radius: 12px;
    box-shadow: var(--card-shadow);
  }
  
  .pagination-container { 
    margin-top: 24px; 
    display: flex; 
    justify-content: center; 
  }
  
  .unread-bold { 
    font-weight: 700; 
    color: var(--text-main); 
    position: relative;
    padding-left: 12px;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 6px;
      height: 6px;
      background: var(--primary-color);
      border-radius: 50%;
    }
  }
  
  .ml-1 { margin-left: 8px; }
  .mr-1 { margin-right: 8px; }
  .text-gray { color: var(--text-secondary); font-size: 13px; }
  .text-gray-light { color: #cbd5e1; font-size: 13px; }
  
  .code-box {
    display: inline-flex;
    align-items: center;
    background: #ecfdf5; // Emerald 50
    border: 1px solid #d1fae5; // Emerald 100
    padding: 4px 12px;
    border-radius: 6px;
    transition: all 0.2s;
    
    &:hover {
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
      transform: translateY(-1px);
    }
    
    .code-value {
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-weight: 700;
      color: #10b981; // Emerald 500
      font-size: 18px;
      letter-spacing: 2px;
    }
  }
  
  :deep(.el-table) {
    --el-table-row-hover-bg-color: #f8fafc;
    border-radius: 8px;
    overflow: hidden;
    
    th {
      background-color: #f1f5f9;
      color: var(--text-secondary);
      font-weight: 600;
    }
    
    td {
      padding: 12px 0;
    }
  }
  
  :deep(.el-tag) {
    border-radius: 4px;
    font-weight: 500;
  }
}
</style>
