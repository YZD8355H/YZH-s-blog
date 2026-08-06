# 部署指南

本站构建产物是**纯静态文件**（`site/` 目录），可以部署到任意静态托管或服务器。

## 方案一：GitHub Pages（免费，5 分钟）

无需服务器，直接在 GitHub 仓库启用：

1. 打开仓库 **Settings → Pages**
2. Source 选择 **Deploy from a branch** → 分支选 `main` → 目录选 `/site`（或 `/root` 配合 CI）
3. 保存后等待 1-2 分钟，访问 `https://YZD8355H.github.io/YZH-s-blog/`

> 注意：仓库里 `site/` 未提交（已被 .gitignore 排除）。用 GitHub Pages 有两种做法：
> - **A. 临时上传**：`uv run build.py` 后把 `site/` 内容手动上传（网页上传或 git push 临时允许跟踪）
> - **B. GitHub Actions 自动构建**（推荐，见文末 workflow）

## 方案二：自建服务器 + Nginx（你要的）

### 1. 准备

- 一台服务器（Ubuntu/Debian 示例），已有 Nginx：
  ```bash
  sudo apt update && sudo apt install -y nginx
  ```

### 2. 上传站点文件（二选一）

**方式 A：本地构建，直接上传**（最简单）

```bash
# 本地
uv run build.py
scp -r site/ 用户名@服务器IP:/var/www/yzh-blog/
```

**方式 B：服务器上自动构建**（推荐，以后更新只跑一条命令）

```bash
# 服务器上
sudo apt install -y git python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh   # 安装 uv
source ~/.bashrc

sudo mkdir -p /var/www/yzh-blog
sudo chown -R $USER /var/www/yzh-blog
git clone https://github.com/YZD8355H/YZH-s-blog.git /var/www/yzh-blog/src
cd /var/www/yzh-blog/src && uv sync
```

> 国内服务器 clone GitHub 慢时用镜像：
> ```bash
> git clone https://ghproxy.com/https://github.com/YZD8355H/YZH-s-blog.git src
> ```

### 3. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/yzh-blog
```

```nginx
server {
    listen 80;
    server_name 你的域名或服务器IP;

    root /var/www/yzh-blog/src/site;   # 方式A 则改为 /var/www/yzh-blog;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # 静态资源缓存
    location ~* \.(css|js|svg|png|jpg|webp)$ {
        expires 7d;
        add_header Cache-Control "public";
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/yzh-blog /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

打开 `http://服务器IP` 即可访问。

### 4. HTTPS（证书，强烈建议）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

certbot 自动配置证书和跳转，每 90 天自动续期。

### 5. 日常更新文章

```bash
# 服务器上
cd /var/www/yzh-blog/src
git pull
uv run build.py
```

或保存为更新脚本 `update.sh`：

```bash
#!/bin/bash
cd /var/www/yzh-blog/src
git pull && uv run build.py
```

### 6. 防火墙

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## 方案三：Cloudflare Pages（国内访问最快的免费方案）

1. 注册 Cloudflare → Workers & Pages → Create → 连接 GitHub 仓库
2. Build command 填 `uv run build.py`，Output directory 填 `site`
3. 自动获得 `xxx.pages.dev` 域名，国内访问速度比 GitHub Pages 好

## 附：GitHub Actions 自动构建（配合方案一）

仓库 `.github/workflows/deploy.yml`：

```yaml
name: Build & Deploy
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync && uv run build.py
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - uses: actions/deploy-pages@v4
```

## 常见问题

| 问题 | 解决 |
|---|---|
| GitHub 访问慢/超时 | 用 ghproxy 镜像 clone；或服务器直连 `git pull` 前先 `git config --global http.lowSpeedLimit 0` |
| 中文标签页 404 | 确认 Nginx `charset utf-8;`（中文 URL 是编码后的，一般无需额外配置） |
| 端口被占 | `sudo ss -tlnp | grep 80` 检查 |
| 修改了模板/CSS 不生效 | 重新 `uv run build.py`，浏览器 Ctrl+F5 强刷 |
