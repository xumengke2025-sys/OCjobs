import { createRouter, createWebHistory } from 'vue-router'
import FortuneView from '../views/FortuneView.vue'
import OcResumeView from '../views/OcResumeView.vue'

const routes = [
  {
    path: '/',
    redirect: '/oc'
  },
  {
    path: '/fortune',
    name: 'Fortune',
    component: FortuneView
  },
  {
    path: '/oc',
    name: 'OcResume',
    component: OcResumeView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
