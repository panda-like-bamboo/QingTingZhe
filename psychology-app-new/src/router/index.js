import { createRouter, createWebHistory } from 'vue-router';
import store from '../store'; // Import Vuex store

// Import all the views
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import UserInfoView from '../views/UserInfoView.vue';
import QuestionnaireView from '../views/QuestionnaireView.vue';
import LoadingView from '../views/LoadingView.vue';
import ReportView from '../views/ReportView.vue';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { requiresAuth: false }
  },
  {
    path: '/user-info',
    name: 'UserInfo',
    component: UserInfoView,
    meta: { requiresAuth: true }
  },
  {
    path: '/questionnaire',
    name: 'Questionnaire',
    component: QuestionnaireView,
    meta: { requiresAuth: true }
  },
  {
    path: '/loading',
    name: 'Loading',
    component: LoadingView,
    meta: { requiresAuth: true }
  },
  {
    path: '/report',
    name: 'Report',
    component: ReportView,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard to check authentication
router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters.isAuthenticated;
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    // If route requires auth and user is not authenticated, redirect to login
    next({ name: 'Login' });
  } else if (to.path === '/login' && isAuthenticated) {
    // If user is already logged in and tries to access login page, redirect to user-info
    next({ name: 'UserInfo' });
  } else {
    // Otherwise allow navigation
    next();
  }
});

export default router;