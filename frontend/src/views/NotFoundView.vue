<template>
  <div class="not-found">
    <div class="content">
      <h1 class="title">404</h1>
      <p class="subtitle">页面未找到</p>
      <p class="description">抱歉，您访问的页面不存在或已被移除</p>
      <el-button type="primary" size="large" @click="$router.push('/')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  
  .content {
    text-align: center;
    padding: 40px;
    
    .title {
      font-size: 120px;
      font-weight: 700;
      color: #409eff;
      margin: 0;
      line-height: 1;
    }
    
    .subtitle {
      font-size: 28px;
      font-weight: 600;
      color: #303133;
      margin: 16px 0 8px;
    }
    
    .description {
      font-size: 16px;
      color: #909399;
      margin: 0 0 24px;
    }
  }
}
</style>
