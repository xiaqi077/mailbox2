<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// App 根组件
</script>

<style lang="scss">
#app {
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  background-color: #f5f7fa;
  color: #1f2937;
  line-height: 1.6;
}

// 暗色模式
html.dark {
  body {
    background-color: #0f172a;
    color: #e5e7eb;
  }
}
</style>