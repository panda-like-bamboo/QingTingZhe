<template>
  <div class="user-management-container">
    <header class="page-header">
      <h1><i class="fas fa-users-cog"></i> 用户管理</h1>
      <p>管理系统中的所有用户账户。</p>
    </header>

    <div class="card">
      <div v-if="loading" class="loading-indicator">
        <i class="fas fa-spinner fa-spin"></i>
        <span>正在加载用户数据...</span>
      </div>
      <div v-else-if="error" class="error-display">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
      </div>
      <div v-else>
        <div class="table-meta">
          总计：<strong>{{ totalUsers }}</strong> 位用户
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>全名</th>
                <th>管理员</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.email || '未设置' }}</td>
                <td>{{ user.full_name || '未设置' }}</td>
                <td>
                  <span :class="['status-tag', user.is_superuser ? 'status-superuser' : '']">
                    {{ user.is_superuser ? '是' : '否' }}
                  </span>
                </td>
                <td>
                  <span :class="['status-tag', user.is_active ? 'status-active' : 'status-inactive']">
                    {{ user.is_active ? '已激活' : '已禁用' }}
                  </span>
                </td>
                <td>
                  <button @click="toggleUserStatus(user)" class="btn btn-small" 
                          :class="user.is_active ? 'btn-danger' : 'btn-primary'">
                    {{ user.is_active ? '禁用' : '激活' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'UserManagementView',
  computed: {
    ...mapState(['users', 'totalUsers', 'loading', 'error']),
  },
  methods: {
    ...mapActions(['fetchUsers']),
    async toggleUserStatus(user) {
        const confirmAction = confirm(`您确定要“${user.is_active ? '禁用' : '激活'}”用户 ${user.username} 吗？`);
        if (confirmAction) {
            try {
                await this.$store.dispatch('updateUserStatus', { 
                    userId: user.id, 
                    isActive: !user.is_active 
                });
                alert(`用户 ${user.username} 已成功${user.is_active ? '禁用' : '激活'}！`);
                this.fetchUsers({ skip: 0, limit: 100 });
            } catch (err) {
                alert(`操作失败: ${err.message}`);
            }
        }
    },
  },
  created() {
    this.fetchUsers({ skip: 0, limit: 100 });
  },
};
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; color: var(--primary-color); display: flex; align-items: center; }
.page-header h1 i { margin-right: 12px; }
.page-header p { color: #888; }
.loading-indicator, .error-display { text-align: center; padding: 40px; color: #888; font-size: 16px; }
.loading-indicator i, .error-display i { margin-right: 8px; }
.table-meta { margin-bottom: 16px; font-size: 14px; }
.table-wrapper { overflow-x: auto; }
.status-tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; color: white; background-color: #909399; }
.status-tag.status-active { background-color: var(--accent-color); }
.status-tag.status-inactive { background-color: #f56c6c; }
.status-tag.status-superuser { background-color: #e6a23c; }
.btn-small { padding: 4px 8px; font-size: 12px; }
</style>