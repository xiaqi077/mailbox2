# Mailbox2

Mailbox Manager 2 - 邮箱管理系统

## 特性

- 📧 多邮箱账户管理
- 📥 批量导入账户
- 🔒 OAuth2 认证支持
- 📊 实时监控邮件
- 🌐 Web 界面

## 快速开始

查看 [DEPLOY.md](DEPLOY.md) 了解详细部署步骤。

## 默认账号

- 用户名: 
- 密码: 

**注意**: 首次登录后请立即修改默认密码。

## 修复内容

本版本修复了以下问题:

1. ✅ 登录 API 支持 form-data 和 JSON 格式
2. ✅ 修复批量导入 URL (从 localhost 改为相对路径)
3. ✅ 修复 CORS 跨域配置
4. ✅ 添加 Nginx 反向代理配置
5. ✅ 添加 SSL 证书自动续期

## 许可证

MIT License
