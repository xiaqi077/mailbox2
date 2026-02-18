<template>
  <div class="dashboard">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card mb-4" shadow="hover">
      <div class="welcome-content">
        <div class="text">
          <h2>👋 欢迎回来, 开启高效邮件管理之旅</h2>
          <p class="text-secondary">Mailbox Manager 助您轻松掌控所有邮箱账户，安全、快速、私有。</p>
        </div>
        <el-button type="primary" size="large" icon="Plus" @click="$router.push('/accounts')">
          立即添加邮箱
        </el-button>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="24">
      <el-col :xs="24" :sm="12" :lg="8">
        <div class="stat-card bg-gradient-blue">
          <div class="stat-icon">
            <el-icon><Message /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.accountCount }}</div>
            <div class="stat-label">活跃邮箱账户</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="8">
        <div class="stat-card bg-gradient-red">
          <div class="stat-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.errorCount }}</div>
            <div class="stat-label">需关注的异常</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 功能简介 -->
    <el-row :gutter="24" class="mt-8">
      <el-col :span="24">
        <el-card shadow="never" class="feature-card">
          <template #header>
            <div class="card-header">
              <span class="flex-center gap-2"><el-icon class="text-primary"><Star /></el-icon> 核心功能</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="多账户支持">Microsoft 365, Outlook, Gmail, 以及任何标准 IMAP 邮箱。</el-descriptions-item>
            <el-descriptions-item label="批量操作">支持 CSV/TXT 文件批量导入账户，一键同步，批量删除。</el-descriptions-item>
            <el-descriptions-item label="网络代理">支持设置全局 SOCKS5/HTTP 代理，也可为每个账户单独配置代理。</el-descriptions-item>
            <el-descriptions-item label="OAuth2 集成">内置 Microsoft Graph API 支持，自动刷新 Token，无需手动维护。</el-descriptions-item>
            <el-descriptions-item label="智能同步">后台自动同步邮件，支持手动触发和状态监控。</el-descriptions-item>
            <el-descriptions-item label="安全隐私">本地化部署，数据仅存储在您的服务器，支持加密连接。</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Warning, Plus, Star } from '@element-plus/icons-vue'
import * as accountsApi from '@/api/accounts'

const router = useRouter()
const stats = ref({
  accountCount: 0,
  errorCount: 0
})

const loadStats = async () => {
  try {
    const accountsRes = await accountsApi.listAccounts({ page: 1, page_size: 100 })
    const accounts = Array.isArray(accountsRes) ? accountsRes : (accountsRes as any).data || []
    
    stats.value.accountCount = accounts.length
    stats.value.errorCount = accounts.filter((acc: any) => acc.status === 'error' || acc.status === 'auth_required').length
  } catch (err) {
    console.error('加载统计失败', err)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  background: #fff;
  border: none;
  border-radius: 12px;
  
  .welcome-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    flex-wrap: wrap;
    gap: 16px;
    
    h2 {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 8px;
    }
    
    p {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}

.stat-card {
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  color: #fff;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
  margin-bottom: 16px;
  
  &:hover {
    transform: translateY(-4px);
  }
  
  .stat-icon {
    width: 64px;
    height: 64px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    margin-right: 20px;
  }
  
  .stat-value {
    font-size: 36px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
  }
  
  .stat-label {
    font-size: 14px;
    opacity: 0.9;
    font-weight: 500;
  }
}

.bg-gradient-blue {
  background: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%);
}

.bg-gradient-red {
  background: linear-gradient(135deg, #ef4444 0%, #f43f5e 100%);
}

.feature-card {
  :deep(.el-card__header) {
    border-bottom: 1px solid var(--border-color);
    padding: 16px 24px;
  }
  
  .card-header {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-main);
    display: flex;
    align-items: center;
  }
}

.mt-8 { margin-top: 2rem; }
.mb-4 { margin-bottom: 1rem; }
.gap-2 { gap: 0.5rem; }
.flex-center { display: flex; align-items: center; }
.text-primary { color: var(--primary-color); }
.text-secondary { color: var(--text-secondary); }
</style>