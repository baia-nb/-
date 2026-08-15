/*
 * 前端 API 地址配置。
 * - 同源部署（前端与后端在同一域名）：保持 '/api'
 * - 分离部署（Cloudflare Pages 前端 + Render 后端）：改为你的 Render 后端地址，例如
 *     window.API_BASE = 'https://netease-mc-converter.onrender.com';
 * 也可在访问时通过 URL 参数临时覆盖：  ?api=https://你的后端地址
 */
window.API_BASE = '/api';
