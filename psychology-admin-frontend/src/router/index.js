// 文件路径: psychology-admin-frontend/src/router/index.js (最终修复版)

import { createRouter, createWebHistory } from 'vue-router';

// [->] 核心修复: 确保所有在 routes 中使用的组件都被导入
import AppLayout from '../components/AppLayout.vue';
import LoginView from '../views/LoginView.vue';
import DashboardView from '../views/DashboardView.vue';
import UserManagementView from '../views/UserManagementView.vue';
import AssessmentSearchView from '../views/AssessmentSearchView.vue'; // <--- 之前可能缺失的导入
import PetitionerGuidanceView from '../views/PetitionerGuidanceView.vue';
import JuvenileCounselingView from '../views/JuvenileCounselingView.vue';
import PoliceAdjustmentView from '../views/PoliceAdjustmentView.vue';
import ReportDetailView from '../views/ReportDetailView.vue';
import InterrogationInputView from '../views/InterrogationInputView.vue';
import InterrogationEditView from '../views/InterrogationEditView.vue';
import InterrogationListView from '../views/InterrogationListView.vue';
import LawQueryView from '../views/LawQueryView.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      // 增加一个从根路径到 dashboard 的重定向
      { path: '', name: 'Home', redirect: '/dashboard' }, 
      { path: 'dashboard', name: 'Dashboard', component: DashboardView },
      { path: 'assessment-search', name: 'AssessmentSearch', component: AssessmentSearchView },
      { path: 'user-management', name: 'UserManagement', component: UserManagementView },
      { path: 'petitioner-guidance', name: 'PetitionerGuidance', component: PetitionerGuidanceView },
      { path: 'juvenile-counseling', name: 'JuvenileCounseling', component: JuvenileCounselingView },
      { path: 'police-adjustment', name: 'PoliceAdjustment', component: PoliceAdjustmentView },
      { path: 'report/:id', name: 'ReportDetail', component: ReportDetailView, props: true },
      { path: 'interrogation/new', name: 'InterrogationInput', component: InterrogationInputView },
      { path: 'interrogation/:id/edit', name: 'InterrogationEdit', component: InterrogationEditView, props: true },
      { path: 'interrogation/list', name: 'InterrogationList', component: InterrogationListView },
      { path: 'law-query', name: 'LawQuery', component: LawQueryView },
    ],
  },
];

const router = createRouter({
  // [->] 关键修复: 使用 import.meta.env.BASE_URL
  // 这会从 vite.config.js 的 base 选项中自动获取部署子路径，例如 /admin/
  history: createWebHistory(import.meta.env.BASE_URL), 
  routes,
});

// 路由守卫保持不变
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token');
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

  if (requiresAuth && !token) {
    next({ name: 'Login' });
  } else if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' }); // 已登录访问登录页，重定向到仪表盘
  } else {
    next();
  }
});

export default router;