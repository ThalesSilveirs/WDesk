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

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
