<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-box">
        <div class="register-header">
          <el-icon class="logo-icon"><Message /></el-icon>
          <h1>Mailbox Manager</h1>
          <p>注册新账号</p>
        </div>

        <el-form
          ref="formRef"
          :model="registerForm"
          :rules="rules"
          @keyup.enter="handleRegister"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="邮箱"
              size="large"
              :prefix-icon="Message"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item prop="passwordConfirm">
            <el-input
              v-model="registerForm.passwordConfirm"
              type="password"
              placeholder="确认密码"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="authStore.isLoading"
              :disabled="authStore.isLoading"
              @click="handleRegister"
              style="width: 100%"
            >
              {{ authStore.isLoading ? '注册中...' : '注册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-footer">
          <p>已有账号? <el-link type="primary" @click="$router.push('/login')">立即登录</el-link></p>
        </div>
      </div>
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

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  passwordConfirm: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '长度在 6 到 128 个字符', trigger: 'blur' }
  ],
  passwordConfirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    const result = await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      password_confirm: registerForm.passwordConfirm,
      full_name: ''
    })

    if (result.success) {
      ElMessage.success('注册成功')
      router.push('/login')
    } else {
      ElMessage.error(result.error || '注册失败')
    }
  })
}
</script>

<style scoped lang="scss">
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-container {
  width: 100%;
  max-width: 440px;
  padding: 20px;
}

.register-box {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.register-header {
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

.register-footer {
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
</style>
