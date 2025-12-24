/**
 * API Configuration
 * 配置后端 API 地址
 */

// 动态获取当前主机名，解决 localhost vs 127.0.0.1 的不一致问题
const currentHostname = window.location.hostname || 'localhost';
const DEV_API_URL = `http://${currentHostname}:8000/api`;

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
  DOCUMENTS: `${API_BASE_URL}/documents`,
  AGENT_CHAT: `${API_BASE_URL}/agent/chat`,
  AGENT_STATUS: `${API_BASE_URL}/agent/status`,
  HEALTH: `http://${currentHostname}:8000/health`
};

// 导出配置信息（调试用）
export const config = {
  apiUrl: API_BASE_URL,
  environment: process.env.NODE_ENV,
  backend: `http://${currentHostname}:8000`
};

export default API_BASE_URL;
