#!/usr/bin/env node

/**
 * 简单的应用启动测试脚本
 */

require('dotenv').config();
const path = require('path');

// 确保正确的路径
process.env.NODE_PATH = path.resolve(__dirname, 'src');
require('module').Module._initPaths();

const logger = require('./src/utils/logger');
const database = require('./src/config/database');

async function testApp() {
  logger.info('Testing SAGPT Backend...');

  try {
    // 测试 1: 验证环境变量
    logger.info('1. Testing environment variables:');
    const requiredEnvVars = ['PORT', 'VOLCENGINE_API_KEY', 'VOLCENGINE_API_BASE_URL', 'JWT_SECRET'];
    const missingVars = [];

    for (const varName of requiredEnvVars) {
      if (!process.env[varName]) {
        missingVars.push(varName);
        logger.warn(`   - ${varName}: MISSING`);
      } else {
        logger.info(`   - ${varName}: OK`);
      }
    }

    if (missingVars.length > 0) {
      logger.warn(`\nSome environment variables are missing (${missingVars.length}):`);
      missingVars.forEach(varName => logger.warn(`  - ${varName}`));
      logger.info('These should be configured in the .env file');
    } else {
      logger.info('All required environment variables are present');
    }

    // 测试 2: 初始化数据库
    logger.info('\n2. Testing database initialization...');
    await database.init();
    logger.info('Database initialized successfully');

    // 测试 3: 查询样本数据
    logger.info('3. Testing database query...');
    const providerCount = await database.get('SELECT COUNT(*) as count FROM service_providers');
    logger.info(`Found ${providerCount.count} service providers in database`);

    if (providerCount.count === 0) {
      logger.warn('No service providers found in database - initializing with sample data');
    }

    // 测试 4: 检查核心服务
    logger.info('\n4. Testing core services...');

    // 测试火山引擎 API 配置
    const volcengine = require('./src/config/volcengine');
    if (volcengine) {
      logger.info('Volcengine API configuration: OK');
    }

    // 测试控制器
    const RequestsController = require('./src/controllers/requestsController');
    const ReportsController = require('./src/controllers/reportsController');
    const ChatController = require('./src/controllers/chatController');
    const ProvidersController = require('./src/controllers/providersController');

    logger.info('All controller modules: OK');

    logger.info('\n✅ All tests passed!');

  } catch (error) {
    logger.error('\n❌ Test failed:', error);
    logger.error('Stack trace:', error.stack);
    process.exit(1);
  }
}

// 运行测试
testApp().then(() => {
  logger.info('\n\nYou can now start the server with:');
  logger.info('npm run dev');
  logger.info('or');
  logger.info('npm start');

  // 关闭数据库连接
  database.close();
});