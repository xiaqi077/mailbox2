<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="logo">
        <el-icon class="logo-icon"><Message /></el-icon>
        <span v-if="!isCollapsed" class="logo-text">Mailbox Manager</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        :collapse="isCollapsed"
        class="sidebar-menu"
        background-color="transparent"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        
        <el-menu-item index="/accounts">
          <el-icon><Message /></el-icon>
          <template #title>邮箱账户</template>
        </el-menu-item>
        
        <el-menu-item index="/emails">
          <el-icon><MessageBox /></el-icon>
          <template #title>邮件管理</template>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-button text class="collapse-btn" @click="toggleCollapse">
          <el-icon v-if="!isCollapsed"><Fold /></el-icon>
          <el-icon v-else><Expand /></el-icon>
          <span v-if="!isCollapsed" class="ml-2">收起</span>
        </el-button>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <header class="header">
        <div class="header-left">
          <el-button 
            type="text" 
            class="mobile-menu-btn" 
            @click="isCollapsed = !isCollapsed"
          >
            <el-icon><Expand v-if="isCollapsed" /><Fold v-else /></el-icon>
          </el-button>
          
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta?.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-tooltip content="全屏切换" placement="bottom">
            <el-button circle plain @click="toggleFullscreen">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </el-tooltip>
          
          <el-tooltip content="刷新页面" placement="bottom">
            <el-button circle plain @click="refresh">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-tooltip>

          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-profile">
              <el-avatar :size="32" :src="user?.avatar_url || ''" class="avatar">
                {{ user?.username?.charAt(0)?.toUpperCase() || 'U' }}
              </el-avatar>
              <span class="username">{{ user?.username || 'User' }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Message, HomeFilled, MessageBox, Setting,
  Fold, Expand, User, FullScreen, Refresh,
  ArrowDown, SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapsed = ref(false)
const user = computed(() => authStore.currentUser)

onMounted(() => {
  // 初始化认证状态
  authStore.init()
})

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      await authStore.logout()
      router.push('/login')
      break
  }
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const refresh = () => {
  location.reload()
}
</script>

<style scoped lang="scss">
.main-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  color: #e2e8f0; // Slate 200
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 24px rgba(0,0,0,0.02);
  z-index: 10;
  
  &.collapsed {
    width: var(--sidebar-collapsed-width);
  }
}

.logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  
  .logo-icon {
    font-size: 28px;
    color: var(--primary-light);
    transition: transform 0.3s;
  }
  
  .logo-text {
    margin-left: 12px;
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc; // Slate 50
    white-space: nowrap;
    letter-spacing: -0.5px;
  }
  
  &:hover .logo-icon {
    transform: rotate(10deg);
  }
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  margin-top: 16px;
  
  :deep(.el-menu-item) {
    margin: 4px 12px;
    border-radius: 8px;
    height: 48px;
    
    &:hover {
      background-color: rgba(255, 255, 255, 0.1) !important;
      color: #fff !important;
    }
    
    &.is-active {
      background: linear-gradient(135deg, var(--primary-color), var(--primary-light)) !important;
      color: #fff !important;
      box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.4);
    }
    
    .el-icon {
      font-size: 20px;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn {
  width: 100%;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.05);
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-color);
}

.header {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 5;
  backdrop-filter: blur(8px);
  background: rgba(255, 255, 255, 0.9);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .mobile-menu-btn {
    display: none; // Hidden on desktop
    font-size: 20px;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-profile {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 20px;
  transition: background 0.2s;
  border: 1px solid transparent;
  
  &:hover {
    background: #f1f5f9;
    border-color: #e2e8f0;
  }
  
  .avatar {
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    font-weight: 600;
  }
  
  .username {
    margin: 0 8px;
    color: var(--text-main);
    font-weight: 500;
    font-size: 14px;
  }
  
  .el-icon--right {
    color: #94a3b8;
    font-size: 12px;
  }
}

.content-wrapper {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    height: 100%;
    transform: translateX(-100%);
    
    &.mobile-open {
      transform: translateX(0);
    }
  }
  
  .header-left .mobile-menu-btn {
    display: flex;
  }
}
</style>
