<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-box">
        <div class="login-header">
          <el-icon class="logo-icon"><Message /></el-icon>
          <h1>Mailbox Manager</h1>
          <p>现代化邮箱管理工具</p>
        </div>

        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名 / 邮箱"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <div class="login-options">
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
          </div>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="authStore.isLoading"
              :disabled="authStore.isLoading"
              @click.prevent="handleLogin"
            >
              {{ authStore.isLoading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 移除注册和忘记密码链接 -->
      </div>
    </div>

    <div class="login-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '长度在 6 到 128 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    const result = await authStore.login({
      username: loginForm.username,
      password: loginForm.password,
      remember: loginForm.remember
    })
    
    if (result.success) {
      ElMessage.success('登录成功')
      
      // 处理“记住我”：保存用户名到本地存储
      if (loginForm.remember) {
        localStorage.setItem('rememberedUsername', loginForm.username)
      } else {
        localStorage.removeItem('rememberedUsername')
      }
      
      // 检查是否需要强制改密
      const user = authStore.currentUser
      if (user && user.must_change_password) {
        ElMessage.warning('为了安全，请先修改默认密码')
        router.replace('/settings?forceChange=1')
      } else {
        router.push('/')
      }
    } else {
      ElMessage.error(result.error || '登录失败')
    }
  })
}

// 初始化加载记住的用户名
import { onMounted } from 'vue'
onMounted(() => {
  const savedUsername = localStorage.getItem('rememberedUsername')
  if (savedUsername) {
    loginForm.username = savedUsername
    loginForm.remember = true
  }
})
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.login-box {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;

  .logo-icon {
    font-size: 48px;
    color: #667eea;
    margin-bottom: 16px;
  }

  h1 {
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 8px 0;
  }

  p {
    font-size: 14px;
    color: #6b7280;
    margin: 0;
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.el-button--primary {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
  }

  &:active {
    transform: translateY(0);
  }
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;

  p {
    color: #6b7280;
    font-size: 14px;
    margin: 0;
  }
}

// 背景动画
.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 1;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s infinite ease-in-out;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: #ff6b9d;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: #4ecdc4;
  top: 50%;
  right: -50px;
  animation-delay: -5s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  background: #ffe66d;
  bottom: -100px;
  left: 30%;
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(50px, -30px) scale(1.1);
  }
  50% {
    transform: translate(0, 50px) scale(0.9);
  }
  75% {
    transform: translate(-50px, -20px) scale(1.05);
  }
}

// 响应式
@media (max-width: 480px) {
  .login-box {
    padding: 24px;
    margin: 16px;
  }

  .login-header {
    h1 {
      font-size: 24px;
    }
  }
}
</style>