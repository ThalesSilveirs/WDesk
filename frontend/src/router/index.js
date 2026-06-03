import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import MainLayout from '../components/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: Dashboard
        },
        {
          path: 'conversations',
          name: 'Conversations',
          component: () => import('../views/Conversations.vue')
        },
        {
          path: 'users',
          name: 'Users',
          component: () => import('../views/Users.vue')
        },
        {
          path: 'analytics',
          name: 'Analytics',
          component: () => import('../views/Analytics.vue')
        },
        {
          path: 'customers',
          name: 'Customers',
          component: () => import('../views/Customers.vue')
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('../views/Settings.vue')
        },
        {
          path: 'connections',
          name: 'Connections',
          component: () => import('../views/Connections.vue')
        }
      ]
    }
  ]
})

function isTokenExpired(token) {
  if (!token) return true
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return true
    const base64Url = parts[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    const payload = JSON.parse(jsonPayload)
    if (payload.exp) {
      return payload.exp < (Date.now() / 1000)
    }
    return false
  } catch (e) {
    return true
  }
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && (!token || isTokenExpired(token))) {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    next('/login')
  } else if (to.name === 'Login' && token && !isTokenExpired(token)) {
    next('/')
  } else {
    next()
  }
})

export default router
