/**
 * API Configuration
 * 配置后端 API 地址
 */

// 开发环境 API 地址
const DEV_API_URL = 'http://localhost:8000/api';

// 生产环境 API 地址（部署后修改）
const PROD_API_URL = '/api';

// 根据环境自动选择
export const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? PROD_API_URL 
  : DEV_API_URL;

// 导出完整的 API 端点
export const API_ENDPOINTS = {
  UPLOAD: `${API_BASE_URL}/upload`,
  SEARCH: `${API_BASE_URL}/search`,
  PARSE: `${API_BASE_URL}/parse`,
  RETRIEVE: `${API_BASE_URL}/retrieve`,
  HEALTH: 'http://localhost:8000/health'
};

// 导出配置信息（调试用）
export const config = {
  apiUrl: API_BASE_URL,
  environment: process.env.NODE_ENV,
  backend: 'http://localhost:8000'
};

export default API_BASE_URL;
