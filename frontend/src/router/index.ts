import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true }
    },
    {
      path: '/auth/callback',
      name: 'AuthCallback',
      component: () => import('@/views/AuthCallbackView.vue'),
      meta: { requiresAuth: true } // 需要登录后才能绑定账号
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '首页' }
        },
        {
          path: 'accounts',
          name: 'Accounts',
          component: () => import('@/views/AccountsView.vue'),
          meta: { title: '邮箱账户' }
        },
        {
          path: 'emails',
          name: 'Emails',
          component: () => import('@/views/EmailsView.vue'),
          meta: { title: '邮件' }
        },
        {
          path: 'emails/:id',
          name: 'EmailDetail',
          component: () => import('@/views/EmailDetailView.vue'),
          meta: { title: '邮件详情' }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: { title: '设置' }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFoundView.vue')
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  if (!authStore.isInitialized) {
    await authStore.init()
  }
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - Mailbox Manager`
  } else {
    document.title = 'Mailbox Manager'
  }
  
  // 需要认证但未登录
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  // 游客页面但已登录
  if (to.meta.guest && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }

  // 首次登录强制改密码
  if (
    authStore.isAuthenticated &&
    authStore.currentUser?.must_change_password &&
    to.name !== 'Settings'
  ) {
    next({ name: 'Settings', query: { forceChange: '1' } })
    return
  }
  
  next()
})

export default router