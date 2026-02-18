<template>
  <div class="email-detail">
    <el-page-header title="邮件详情" @back="$router.back()" />

    <el-card class="mt-20" v-loading="loading">
      <template #header>
        <div class="header">
          <div class="subject">{{ email?.subject || '(无主题)' }}</div>
          <div class="meta">
            <span>发件人：{{ email?.from_name || email?.from_address }}</span>
            <span>收件人：{{ email?.to_addresses }}</span>
            <span>时间：{{ email?.received_at || email?.created_at }}</span>
          </div>
        </div>
      </template>

      <div class="body" v-if="email">
        <div v-if="email.body_html" v-html="email.body_html"></div>
        <pre v-else class="plain">{{ email.body_text }}</pre>
      </div>

      <el-empty v-if="!email && !loading" description="邮件不存在" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as emailsApi from '@/api/emails'
import type { Email } from '@/types'

const route = useRoute()
const email = ref<Email | null>(null)
const loading = ref(false)

const loadEmail = async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await emailsApi.getEmail(id)
    email.value = res.data || null
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error?.message || '加载邮件详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadEmail)
</script>

<style scoped lang="scss">
.email-detail {
  .mt-20 { margin-top: 20px; }
  .header { display: flex; flex-direction: column; gap: 6px; }
  .subject { font-size: 18px; font-weight: 600; }
  .meta { display: flex; flex-direction: column; gap: 4px; color: #606266; font-size: 13px; }
  .body { padding-top: 10px; }
  .plain { white-space: pre-wrap; font-family: inherit; }
}
</style>
