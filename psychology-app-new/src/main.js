import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import { marked } from 'marked'; // For markdown rendering
import './assets/sci-fi-theme.css'; // Global CSS

// Create the Vue app
const app = createApp(App);

// Register a global markdown filter
app.config.globalProperties.$marked = (text) => {
  if (!text) return '';
  return marked(text);
};

// Use Vuex store and Vue Router
app.use(store);
app.use(router);

// Mount the app
app.mount('#app');

