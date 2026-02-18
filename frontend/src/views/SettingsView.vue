<template>
  <div class="settings-view">
    <el-dialog
      v-model="forceDialogVisible"
      title="首次登录需要修改密码"
      width="420px"
      :close-on-click-modal="false"
      :show-close="false"
      :close-on-press-escape="false"
    >
      <p>为了安全起见，请先修改默认密码后再继续使用系统。</p>
      <template #footer>
        <el-button type="primary" @click="scrollToPassword">去修改</el-button>
      </template>
    </el-dialog>

    <el-page-header title="设置" @back="$router.back()" />

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>👤 个人资料</span>
            </div>
          </template>
          
          <el-form :model="profileForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" placeholder="修改用户名" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateProfile">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card id="password-card">
          <template #header>
            <div class="card-header">
              <span>🔒 修改密码</span>
            </div>
          </template>
          
          <el-form :model="passwordForm" label-width="120px" :rules="passwordRules" ref="passwordFormRef">
            <el-form-item label="当前密码" prop="old_password">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'

const authStore = useAuthStore()
const passwordFormRef = ref<FormInstance>()
const route = useRoute()
const router = useRouter()
const forceChange = computed(() => route.query.forceChange === '1')
const forceDialogVisible = ref(false)

// 个人资料表单
const profileForm = reactive({
  username: '',
  email: ''
})

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 密码验证规则
const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 加载用户信息
onMounted(() => {
  const user = authStore.currentUser
  if (user) {
    profileForm.username = user.username
    profileForm.email = user.email
  }
  if (forceChange.value) {
    forceDialogVisible.value = true
  }
})

// 更新个人资料
const scrollToPassword = async () => {
  // 先关闭弹窗，避免遮挡/锁定滚动
  forceDialogVisible.value = false
  await nextTick()
  const el = document.querySelector('#password-card') as HTMLElement | null
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const handleUpdateProfile = async () => {
  const result = await authStore.updateProfile({
    username: profileForm.username,
    email: profileForm.email
  })
  
  if (result.success) {
    ElMessage.success('个人资料更新成功')
    // 如果改了用户名或邮箱，最好刷新一下用户信息
    authStore.init()
  } else {
    ElMessage.error(result.error || '更新失败')
  }
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      const result = await authStore.changePassword(
        passwordForm.old_password,
        passwordForm.new_password
      )
      
      if (result.success) {
        ElMessage.success('密码修改成功，请重新登录')
        // 重置表单
        passwordFormRef.value?.resetFields()
        // 如果是强制改密，或者只是普通修改，最好都重新登录
        authStore.logout()
        router.replace('/login')
      } else {
        ElMessage.error(result.error || '密码修改失败')
      }
    }
  })
}
</script>

<style scoped lang="scss">
.settings-view {
  .mt-20 {
    margin-top: 20px;
  }
  .card-header {
    font-size: 16px;
    font-weight: 600;
  }
}
</style>
