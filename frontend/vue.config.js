const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // <--- Add this line to disable ESLint during dev/build
  devServer: {
    host: '0.0.0.0', // Allows connections from any network interface
    port: 8080, // Matches your current server port
    client: {
      webSocketURL: 'ws://0.0.0.0:8080/ws', // Ensures WebSocket URL is consistent
      logging: 'verbose', // Enables detailed logging for debugging
    },
    allowedHosts: 'all', // Allows connections from any host
  },
})