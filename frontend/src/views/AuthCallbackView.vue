
<template>
  <div class="callback-view">
    <el-card class="box-card">
      <div class="loading-container" v-if="loading">
        <el-icon class="is-loading" :size="40" color="#409eff"><Loading /></el-icon>
        <p class="mt-4">正在与微软服务器通信...</p>
        <p class="sub-text">请稍候，正在获取您的授权令牌</p>
      </div>
      <div class="error-container" v-else>
        <el-icon :size="40" color="#f56c6c"><CircleCloseFilled /></el-icon>
        <p class="mt-4 error-text">{{ error }}</p>
        <el-button type="primary" @click="$router.push('/accounts')" class="mt-4">返回账户列表</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loading, CircleCloseFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const code = route.query.code as string
  if (!code) {
    error.value = '未找到授权码 (Code)，请重试'
    loading.value = false
    return
  }

  // 从 localStorage 获取之前保存的 Client ID/Secret
  const clientId = localStorage.getItem('oauth_client_id')
  const clientSecret = localStorage.getItem('oauth_client_secret')
  
  if (!clientId) {
    error.value = 'Client ID 丢失，请重新发起登录'
    loading.value = false
    return
  }

  try {
    // 调用后端换取 Token
    // 注意：redirect_uri 必须与 Azure 中配置的完全一致 (包括末尾斜杠)
    // 我们约定用当前页面的 URL (不带参数)
    const redirectUri = window.location.origin + window.location.pathname
    
    const res = await api.post('/auth/microsoft/exchange', {
      code,
      client_id: clientId,
      client_secret: clientSecret || '',
      redirect_uri: redirectUri
    })
    
    // 成功！保存 Token 到 localStorage 供 AccountsView 使用
    const tokens = res.data
    localStorage.setItem('oauth_result', JSON.stringify({
      refresh_token: tokens.refresh_token,
      access_token: tokens.access_token,
      client_id: clientId,
      client_secret: clientSecret
    }))
    
    ElMessage.success('授权成功！')
    
    // 清除临时 ID
    localStorage.removeItem('oauth_client_id')
    localStorage.removeItem('oauth_client_secret')
    
    // 跳转回账户页面，并带上标记让它自动填充
    router.push({ path: '/accounts', query: { oauth_success: '1' } })
    
  } catch (err: any) {
    console.error('Exchange failed', err)
    error.value = err.response?.data?.detail || '获取 Token 失败，请检查 Client Secret 是否正确'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.callback-view {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
.box-card {
  width: 400px;
  text-align: center;
  padding: 40px 20px;
}
.mt-4 { margin-top: 16px; }
.sub-text { font-size: 14px; color: #909399; margin-top: 8px; }
.error-text { color: #f56c6c; font-weight: 500; }
</style>
