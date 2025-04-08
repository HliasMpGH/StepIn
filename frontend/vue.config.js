const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // Disable linting during save
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  outputDir: '../static/frontend',
  publicPath: process.env.NODE_ENV === 'production' ? '/static/frontend/' : '/'
})