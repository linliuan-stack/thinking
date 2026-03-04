import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/experiment',
      name: 'ExperimentList',
      component: () => import('../views/experiment/ExperimentList.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/experiment/:id',
      name: 'ExperimentDetail',
      component: () => import('../views/experiment/ExperimentDetail.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/experiment/:id/plate/:plateId',
      name: 'PlateEditor',
      component: () => import('../views/experiment/PlateEditor.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/experiment/:id/plate/:plateId/analysis',
      name: 'PlateAnalysis',
      component: () => import('../views/experiment/PlateAnalysis.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
