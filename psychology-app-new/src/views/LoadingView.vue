<template>
  <div class="page-container loading-page">
    <nav-bar title="分析进行中" :canGoBack="false" />

    <div class="loading-content">
      <div class="loading-visualization">
        <div class="brain-scan">
          <i class="fas fa-brain brain-icon"></i>
          <div class="scan-line"></div>
          <div class="scan-particles"></div>
          <div class="scan-ring"></div>
        </div>
        <div class="neural-network">
          <div v-for="i in 9" :key="i" 
               class="neural-node" 
               :class="`node-${i}`"></div>
          <div v-for="i in 12" :key="`line-${i}`" 
               class="neural-line" 
               :class="`line-${i}`"></div>
        </div>
      </div>

      <div class="loading-text">
        <h2>
          <span class="tech-highlight">AI</span> 
          心理分析报告生成中
          <i class="fas fa-dna icon-spin"></i>
        </h2>
        
        <p v-if="!localError && !reportReady">
          <i class="fas fa-microchip"></i> 
          AI 正在努力分析，请稍候...
          <span class="status-badge processing">处理中</span>
        </p>
        
        <p v-if="isPolling && !reportReady && !localError" class="polling-status">
          <i class="fas fa-sync fa-spin"></i> 
          自动查询中 ({{ retries + 1 }}/{{ maxRetries }})
        </p>
        
        <p v-if="reportReady && !localError" class="success-message">
          <i class="fas fa-check-circle"></i> 
          报告已生成！
          <span class="redirect-text">正在跳转...</span>
        </p>
      </div>

      <!-- 高科技进度条 -->
      <div v-if="!localError && !reportReady" class="progress-container">
        <div class="progress-track">
          <div class="progress-value" :style="{width: `${progressValue}%`}"></div>
          <div class="progress-glow"></div>
        </div>
        <div class="progress-text">{{ Math.round(progressValue) }}%</div>
      </div>

      <!-- 错误信息 -->
      <div v-if="localError" class="status-message">
        <i class="fas fa-exclamation-triangle error-icon"></i>
        <div class="error-text">{{ localError }}</div>
        <div class="action-buttons">
          <button @click="manualFetchReport" class="btn btn-secondary btn-small" :disabled="isFetchingManually || isCheckingReport">
            <i class="fas fa-sync-alt"></i> {{ isFetchingManually ? '刷新中...' : '手动刷新' }}
          </button>
          <button @click="goBackToStart" class="btn btn-small">
            <i class="fas fa-arrow-left"></i> 返回
          </button>
        </div>
      </div>

      <!-- 心理小贴士 -->
      <transition name="fade" mode="out-in">
        <loading-tip
          :key="currentTipKey"
          :tip="currentTip"
        />
      </transition>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex';
import NavBar from '../components/NavBar.vue';
import LoadingTip from '../components/LoadingTip.vue';
import { getRandomDefaultTip } from '../utils';

export default {
  name: 'LoadingView',
  components: {
    NavBar,
    LoadingTip
  },
  data() {
    return {
      tipInterval: null,
      // +++ 轮询相关状态 +++
      checkReportInterval: null, // 轮询定时器 ID
      retries: 0,                // 当前重试次数
      maxRetries: 30,            // 最大重试次数 (例如 30次 * 10秒 = 5分钟)
      pollingIntervalMs: 10000,  // 轮询间隔 (毫秒)
      isPolling: false,          // 标记是否正在进行轮询
      isCheckingReport: false,   // 防止并发检查报告
      // +++++++++++++++++++++
      tipIntervalMs: 15000,
      currentTipKey: 0,
      localError: '', // 本地错误/状态信息
      eventSource: null, // SSE 实例
      reportReady: false, // 标记 SSE 是否收到成功事件
      isFetchingManually: false, // 手动刷新状态
      progressValue: 0,
      progressInterval: null,
    };
  },
  computed: {
    ...mapState({
      reportFromStore: state => state.report, // 引入 report state
      submissionIdFromStore: state => state.assessment.submissionId,
      globalError: state => state.error
    }),
    ...mapGetters({
      tip: 'getCurrentTip',
    }),
    submissionId() {
      const id = this.submissionIdFromStore;
      console.log('[LoadingView computed] submissionId:', id);
      return id;
    },
    // +++ 计算属性：检查报告是否有效 +++
    isValidReportAvailable() {
      const report = this.reportFromStore;
      // 报告必须是对象且有非空 report_text
      const isValid = report && typeof report === 'object' && report.report_text && report.report_text.trim() !== '';
      if (isValid) {
          console.log('[LoadingView computed] isValidReportAvailable: true');
      }
      return isValid;
    },
    // ++++++++++++++++++++++++++++++++
    currentTip() {
      return this.tip || getRandomDefaultTip();
    }
  },
  watch: {
    // +++ 监听报告是否有效，一旦有效就跳转 +++
    isValidReportAvailable(newValue) {
        if (newValue) {
            console.log('[LoadingView watcher] isValidReportAvailable 变为 true，准备导航。');
            this.clearPollingIntervals(); // 停止所有定时器
            this.closeEventSource();    // 关闭 SSE 连接
            this.progressValue = 100; // 设置进度为100%
            // 短暂延迟确保状态更新渲染
            setTimeout(() => {
                console.log('[LoadingView watcher] 执行导航到 /report');
                this.$router.push('/report');
            }, 1000); // 减少延迟
        }
    },
    // +++++++++++++++++++++++++++++++++++++
    globalError(newError) {
        console.log('[LoadingView watcher] 全局 Vuex 错误状态变化:', newError);
        if (newError && !this.localError) {
            this.localError = `发生全局错误: ${newError}`;
            this.closeEventSource();
            this.clearPollingIntervals(); // 全局错误也停止轮询
        }
    },
    // 监听重试次数用于超时判断
    retries(newValue) {
        if (newValue >= this.maxRetries && this.isPolling) {
            console.warn(`[LoadingView watcher] 达到最大重试次数 ${this.maxRetries}，停止轮询。`);
            this.localError = "报告生成时间过长或查询失败，请稍后尝试手动刷新或返回。";
            this.clearPollingIntervals(); // 停止轮询
        }
    }
  },
  methods: {
    ...mapActions(['fetchRandomTip', 'fetchReport', 'clearError', 'resetAssessment']),

    async getNewTip() {
      // (保持不变)
      console.log('[LoadingView method] getNewTip: 尝试获取新提示...');
      try {
        await this.fetchRandomTip();
        this.currentTipKey++;
        console.log('[LoadingView method] getNewTip: 新提示获取成功。');
      } catch (error) {
        console.error('[LoadingView method] getNewTip: 获取提示时出错:', error);
      }
    },

    // 模拟进度条
    startProgressSimulation() {
      // 清除之前的进度条
      if (this.progressInterval) clearInterval(this.progressInterval);
      this.progressValue = 0;
      
      this.progressInterval = setInterval(() => {
        // 如果报告已就绪，直接100%
        if (this.reportReady) {
          this.progressValue = 100;
          clearInterval(this.progressInterval);
          return;
        }
        
        // 正常情况下缓慢增加，但不超过95%
        if (this.progressValue < 95) {
          // 随机增加一小部分
          this.progressValue += Math.random() * 3;
          if (this.progressValue > 95) this.progressValue = 95;
        }
      }, 1000);
    },

    // +++ 清理所有定时器和 SSE 连接 +++
    clearPollingIntervals() {
      console.log("[LoadingView method] clearPollingIntervals: 清理所有定时器...");
      if (this.tipInterval) clearInterval(this.tipInterval);
      if (this.checkReportInterval) clearInterval(this.checkReportInterval);
      if (this.progressInterval) clearInterval(this.progressInterval);
      this.tipInterval = null;
      this.checkReportInterval = null;
      this.progressInterval = null;
      this.isPolling = false; // 标记轮询停止
      this.retries = 0; // 重置重试次数
    },
    // ++++++++++++++++++++++++++++++++

    closeEventSource() {
      // (保持不变)
      if (this.eventSource) {
        console.log("[LoadingView method] closeEventSource: 正在关闭 EventSource 连接...");
        this.eventSource.close();
        this.eventSource = null;
        console.log("[LoadingView method] closeEventSource: EventSource 连接已关闭。");
      }
    },

    // --- 修改 setupEventSource ---
    setupEventSource() {
      console.log('[LoadingView setupEventSource] 启动函数：尝试设置 SSE 连接...');
      if (!this.submissionId) {
        this.localError = "无法获取评估ID，无法订阅状态更新。";
        console.error("[LoadingView setupEventSource] 错误：无 submissionId。无法继续。");
        return; // 没有 ID 无法继续
      }
      if (this.eventSource) {
          console.warn("[LoadingView setupEventSource] 警告：EventSource 已存在。正在关闭旧连接。");
          this.closeEventSource();
      }

      const sseUrl = `/sse/report-status/${this.submissionId}`;
      console.log(`[LoadingView setupEventSource] 构造的 SSE URL: ${sseUrl}`);
      this.localError = ''; // 清除错误
      this.reportReady = false;

      try {
          console.log('[LoadingView setupEventSource] 准备创建新的 EventSource 对象...');
          this.eventSource = new globalThis.EventSource(sseUrl, { withCredentials: true });
          console.log('[LoadingView setupEventSource] EventSource 对象已成功创建 (尚未连接)。');

          this.eventSource.onopen = () => {
            console.log(`[LoadingView SSE] SSE 连接成功打开。评估 ID: ${this.submissionId}`);
            // SSE 连接成功，不需要启动轮询
          };

          // 监听 report_ready 事件
          this.eventSource.addEventListener('report_ready', async (event) => {
            console.log('[LoadingView SSE] 收到 "report_ready" 事件。');
            this.reportReady = true; // 标记收到事件
            this.closeEventSource(); // 关闭 SSE
            this.clearPollingIntervals(); // 确保轮询已停止
            try {
                console.log('[LoadingView SSE] 报告已就绪，触发 fetchReport...');
                await this.fetchReport(); // 调用 fetchReport 获取数据
                // 导航现在由 isValidReportAvailable watcher 处理
                console.log('[LoadingView SSE] fetchReport 完成，等待 watcher 导航。');
            } catch (error) {
                console.error('[LoadingView SSE] 处理 "report_ready" 事件后 fetchReport 出错:', error);
                this.localError = "收到报告就绪通知，但在获取报告内容时出错。";
            }
          });

          // 监听 report_failed 事件
          this.eventSource.addEventListener('report_failed', (event) => {
              console.error('[LoadingView SSE] 收到 "report_failed" 事件:', event.data);
              this.closeEventSource(); // 关闭 SSE
              this.clearPollingIntervals(); // 停止轮询
              try {
                  const eventData = JSON.parse(event.data || '{}');
                  this.localError = `报告生成失败: ${eventData?.error || '原因未知'}. 您可以尝试返回重新提交。`;
              } catch (e) {
                  this.localError = "报告生成失败，且无法解析服务器返回的错误详情。您可以尝试返回重新提交。";
              }
          });

          // --- 修改 onerror 处理，增加启动轮询 ---
          this.eventSource.onerror = (error) => {
            console.error(`[LoadingView SSE] SSE 连接发生错误。评估 ID: ${this.submissionId}。错误事件对象:`, error);
            this.closeEventSource(); // 关闭失败的 SSE 连接

            // *** 如果尚未开始轮询，则启动轮询作为后备 ***
            if (!this.isPolling) {
                console.warn("[LoadingView SSE onerror] SSE 连接失败，启动轮询作为后备方案。");
                // 设置提示信息，告知用户将尝试自动查询
                this.localError = `尝试自动查询状态...`;
                this.startPolling(); // <--- 启动轮询
                // 首次轮询检查
                setTimeout(() => {
                     if (this.isPolling) { this.checkReport(); }
                }, this.pollingIntervalMs / 2); // 首次检查可以快一点
            } else {
                 // 如果已经在轮询（例如，之前 onerror 已经触发过一次），则只更新错误信息
                 this.localError = `实时连接中断，继续尝试自动查询状态...`;
            }
          };
          // --- onerror 修改结束 ---

           this.eventSource.onmessage = (event) => { // 通用消息 (保持不变)
               console.log("[LoadingView SSE] 收到通用 SSE 消息:", event.data);
           };

           console.log('[LoadingView setupEventSource] EventSource 监听器设置完成。');

      } catch (error) { // 创建 EventSource 时的同步错误
          console.error(`[LoadingView setupEventSource] 创建 EventSource 对象期间发生同步错误:`, error);
          this.localError = `建立实时更新连接时遇到问题 (${error.message})。将尝试自动查询状态...`;
          this.eventSource = null;
          // *** 同步错误也应该启动轮询 ***
          if (!this.isPolling) {
              console.warn("[LoadingView setupEventSource catch] 创建 SSE 失败，启动轮询。");
              this.startPolling();
              setTimeout(() => {
                   if (this.isPolling) { this.checkReport(); }
              }, this.pollingIntervalMs / 2);
          }
      }
    },
    // --- setupEventSource 修改结束 ---

    // +++ 开始轮询的辅助函数 +++
    startPolling() {
      // 确保清理旧定时器
      this.clearPollingIntervals(); // 清理之前的，包括 tipInterval

      console.log(`[LoadingView method] startPolling: 启动轮询，间隔 ${this.pollingIntervalMs}ms。`);
      this.isPolling = true;
      this.retries = 0; // 重置重试次数

      // 重新启动提示定时器
      this.tipInterval = setInterval(this.getNewTip, this.tipIntervalMs);

      // 启动检查报告的定时器
      this.checkReportInterval = setInterval(() => {
        if (this.isPolling) {
          this.checkReport();
        } else {
           // 如果在 interval 触发时 isPolling 变为 false，清除自身
           console.log('[LoadingView checkReportInterval] Polling is inactive, clearing interval.');
           if (this.checkReportInterval) clearInterval(this.checkReportInterval);
           this.checkReportInterval = null;
        }
      }, this.pollingIntervalMs);
      
      // 启动进度模拟
      this.startProgressSimulation();
    },
    // +++++++++++++++++++++++++++

    // +++ 检查报告状态的轮询函数 +++
    async checkReport() {
      if (!this.isPolling || this.isCheckingReport) {
        console.log(`[LoadingView method] checkReport: 跳过检查 (isPolling: ${this.isPolling}, isCheckingReport: ${this.isCheckingReport})`);
        return;
      }
      if (!this.submissionId) {
        console.error("[LoadingView method] checkReport: 无 submissionId，无法检查报告！");
        this.localError = "无法获取评估ID，停止查询。";
        this.clearPollingIntervals();
        return;
      }

      this.isCheckingReport = true;
      console.log(`[LoadingView method] checkReport: 开始检查报告状态，尝试次数 ${this.retries + 1}/${this.maxRetries}，ID: ${this.submissionId}`);
      this.retries++; // 增加尝试次数

      try {
        // 调用 fetchReport action (它内部会处理404等情况)
        const result = await this.fetchReport();
        console.log('[LoadingView method] checkReport: fetchReport action 完成。');

        // 检查 action 返回结果是否指示报告未就绪 (例如返回了 { status: 404 })
        if (result?.status === 404) {
            console.log(`[LoadingView method] checkReport: 报告尚未就绪 (收到 404 状态)。`);
            // 不需要设置错误，等待下一次轮询或超时
        }
        // 如果 fetchReport 成功获取了报告，isValidReportAvailable watcher 会处理导航
        // 如果 fetchReport 内部遇到非 404 错误，它会抛出，由下面的 catch 处理

      } catch (error) {
        // fetchReport 抛出了除 404 以外的错误
        console.error('[LoadingView method] checkReport: 调用 fetchReport action 时捕获到错误:', error);
        const detail = error.response?.data?.detail || error.message || '未知错误';
        this.localError = `自动查询报告时遇到问题: ${detail}. 如长时间无响应，请尝试手动刷新或返回。`;
        // 发生严重错误时停止轮询
        if (error.response?.status !== 404) { // 确认不是"未找到"错误
             this.clearPollingIntervals();
        }
      } finally {
        this.isCheckingReport = false; // 确保解除锁定
        console.log(`[LoadingView method] checkReport: 检查结束。`);
      }
    },
    // ++++++++++++++++++++++++++++++

    // --- manualFetchReport 保持不变，但更新提示文字 ---
    async manualFetchReport() {
      if (!this.submissionId) {
          this.localError = "无法获取评估ID，无法手动刷新。";
          return;
      }
      console.log('[LoadingView method] manualFetchReport: 用户点击手动刷新。');
      this.isFetchingManually = true;
      this.localError = ''; // 清除提示
      try {
          await this.fetchReport();
          // 导航由 watcher 处理
          if (!this.isValidReportAvailable) {
             // 如果手动刷新后报告仍无效
             this.localError = "手动刷新完成，但报告仍未就绪。请再等待一段时间。";
          }
      } catch (error) {
          const detail = error.response?.data?.detail || error.message || '未知错误';
          // 只有在非 404 (未就绪) 错误时才强烈提示失败
          if (error.response?.status !== 404) {
            this.localError = `手动刷新失败: ${detail}`;
          } else {
            this.localError = "手动刷新完成，但报告仍未就绪。请再等待一段时间。";
          }
      } finally {
          this.isFetchingManually = false;
      }
    },
    // --- manualFetchReport 结束 ---

    // --- goBackToStart 保持不变 ---
    goBackToStart() {
        console.log('[LoadingView method] goBackToStart: 用户点击返回。');
        this.closeEventSource();
        this.clearPollingIntervals(); // 确保停止轮询
        this.resetAssessment();
        this.$router.push('/user-info');
    }
    // --- goBackToStart 结束 ---

  },
  created() {
    console.log('[LoadingView] Component created.');
    this.clearError(); // 清除 Vuex 全局错误
    this.localError = '';
    this.reportReady = false;

    // 立即获取提示
    this.getNewTip();
    // 提示定时器会在 startPolling 中启动
    
    // 启动进度条模拟
    this.startProgressSimulation();

    if (!this.submissionId) {
        console.error("[LoadingView created] CRITICAL: 无 submissionId!");
        this.localError = "无法获取评估ID，请返回重试。";
        // 不启动 SSE 或轮询
    } else {
        // 检查是否已有报告
        if (this.isValidReportAvailable) {
            console.log('[LoadingView created] 报告已存在，直接导航。');
            this.$router.push('/report');
        } else {
             console.log('[LoadingView created] 报告不存在，尝试启动 SSE。');
             this.setupEventSource(); // 尝试启动 SSE
        }
    }
  },
  beforeUnmount() {
    console.log('[LoadingView] Component unmounting.');
    this.closeEventSource();
    this.clearPollingIntervals(); // 确保清理所有定时器
  }
}
</script>

<style scoped>
.loading-page {
  padding-top: 60px;
  min-height: 100vh;
  background-color: var(--background-color);
  background-image: 
    radial-gradient(circle at 10% 20%, rgba(33, 150, 243, 0.05) 0%, transparent 25%),
    radial-gradient(circle at 90% 80%, rgba(3, 218, 198, 0.05) 0%, transparent 25%);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 30px 20px;
  min-height: calc(100vh - 60px);
}

.loading-visualization {
  margin-bottom: 40px;
  position: relative;
}

.brain-scan {
  position: relative;
  width: 150px;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 40px;
}

.brain-icon {
  font-size: 80px;
  color: var(--primary-color);
  z-index: 2;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 0 10px rgba(33, 150, 243, 0.5));
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 5px;
  background: linear-gradient(90deg, transparent, var(--secondary-color), transparent);
  animation: scanLine 2s ease-in-out infinite;
  z-index: 1;
  opacity: 0.7;
  box-shadow: 0 0 10px var(--secondary-color);
}

.scan-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border: 2px solid rgba(3, 218, 198, 0.3);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.neural-network {
  display: flex;
  position: relative;
  width: 200px;
  height: 100px;
  margin: 0 auto;
}

.neural-node {
  position: absolute;
  width: 10px;
  height: 10px;
  background-color: var(--primary-color);
  border-radius: 50%;
  z-index: 2;
}

/* 定位节点 */
.node-1 { top: 10%; left: 10%; animation: pulse 2s infinite 0.1s; }
.node-2 { top: 30%; left: 30%; animation: pulse 2s infinite 0.2s; }
.node-3 { top: 70%; left: 20%; animation: pulse 2s infinite 0.3s; }
.node-4 { top: 50%; left: 50%; animation: pulse 2s infinite 0.4s; }
.node-5 { top: 20%; left: 70%; animation: pulse 2s infinite 0.5s; }
.node-6 { top: 80%; left: 60%; animation: pulse 2s infinite 0.6s; }
.node-7 { top: 40%; left: 85%; animation: pulse 2s infinite 0.7s; }
.node-8 { top: 60%; left: 15%; animation: pulse 2s infinite 0.8s; }
.node-9 { top: 90%; left: 80%; animation: pulse 2s infinite 0.9s; }

.neural-line {
  position: absolute;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
  opacity: 0.3;
  transform-origin: left center;
  z-index: 1;
}

/* 连线样式 - 简化了具体连接，实际应用需要更精确定位 */
.line-1 { top: 15%; left: 10%; width: 100px; transform: rotate(20deg); animation: pulseLine 2s infinite 0.1s; }
.line-2 { top: 35%; left: 30%; width: 70px; transform: rotate(-10deg); animation: pulseLine 2s infinite 0.2s; }
.line-3 { top: 75%; left: 20%; width: 120px; transform: rotate(30deg); animation: pulseLine 2s infinite 0.3s; }
.line-4 { top: 55%; left: 50%; width: 90px; transform: rotate(5deg); animation: pulseLine 2s infinite 0.4s; }
.line-5 { top: 25%; left: 70%; width: 60px; transform: rotate(-25deg); animation: pulseLine 2s infinite 0.5s; }
.line-6 { top: 85%; left: 60%; width: 80px; transform: rotate(-15deg); animation: pulseLine 2s infinite 0.6s; }
.line-7 { top: 45%; left: 15%; width: 110px; transform: rotate(15deg); animation: pulseLine 2s infinite 0.7s; }
.line-8 { top: 65%; left: 15%; width: 100px; transform: rotate(20deg); animation: pulseLine 2s infinite 0.8s; }
.line-9 { top: 95%; left: 30%; width: 120px; transform: rotate(10deg); animation: pulseLine 2s infinite 0.9s; }
.line-10 { top: 15%; left: 40%; width: 90px; transform: rotate(-20deg); animation: pulseLine 2s infinite 1.0s; }
.line-11 { top: 55%; left: 60%; width: 70px; transform: rotate(-10deg); animation: pulseLine 2s infinite 1.1s; }
.line-12 { top: 75%; left: 70%; width: 60px; transform: rotate(15deg); animation: pulseLine 2s infinite 1.2s; }

.loading-text {
  text-align: center;
  margin-bottom: 30px;
}

h2 {
  font-size: 24px;
  color: var(--primary-color);
  margin-bottom: 16px;
  font-family: var(--heading-font);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.tech-highlight {
  display: inline-block;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 18px;
  margin-right: 8px;
}

.icon-spin {
  animation: rotate 4s linear infinite;
  color: var(--secondary-color);
  margin-left: 10px;
}

.loading-content p {
  color: var(--text-secondary);
  min-height: 1.5em;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 8px;
}

.status-badge.processing {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--primary-color);
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.polling-status {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.success-message {
  color: var(--success-color) !important;
  font-weight: 500;
}

.redirect-text {
  opacity: 0.7;
  animation: pulse 1s infinite;
}

.progress-container {
  width: 80%;
  max-width: 400px;
  margin: 20px auto 30px;
}

.progress-track {
  height: 8px;
  background-color: rgba(33, 150, 243, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-value {
  height: 100%;
  background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
  border-radius: 4px;
  transition: width 0.5s ease;
  position: relative;
}

.progress-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 60px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.7), transparent);
  animation: progressGlow 2s infinite;
  pointer-events: none;
}

.progress-text {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
  font-family: var(--heading-font);
}

.status-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #856404;
  background-color: #fff3cd;
  border: 1px solid #ffeeba;
  padding: 20px;
  margin-top: 20px;
  margin-bottom: 20px;
  text-align: center;
  width: 90%;
  max-width: 500px;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
}

.error-icon {
  color: var(--error-color);
  font-size: 32px;
  margin-bottom: 16px;
}

.error-text {
  font-size: 16px;
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@keyframes scanLine {
  0% { transform: translateY(0); opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { transform: translateY(150px); opacity: 0; }
}

@keyframes pulseLine {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

@keyframes progressGlow {
  0% { left: -100px; }
  100% { left: 100%; }
}
</style>