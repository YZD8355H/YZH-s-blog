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

### 阿里云 ECS（成都节点）专属步骤

> 阿里云与普通 VPS 的差别只有两处：**安全组**（云控制台放行端口）和**备案**（国内节点域名必须 ICP 备案）。系统通常是 Alibaba Cloud Linux / CentOS，命令用 `dnf`（旧版用 `yum`）。

**第 0 步 · 安全组放行端口（必做，否则外网访问不通）**

阿里云控制台 → ECS 实例 → 安全组 → 配置规则 → 添加入方向规则：

| 协议 | 端口 | 授权对象 |
|---|---|---|
| TCP | 80 | 0.0.0.0/0 |
| TCP | 443 | 0.0.0.0/0 |
| TCP | 22 | 你的 IP（安全起见不要全放行） |

**第 0.5 步 · 备案确认**

- 有域名且要绑定域名 → 必须先 ICP 备案（阿里云控制台 → 备案系统，约 1-2 周），未备案域名访问会被拦截
- 没有域名 / 备案中 → **用服务器 IP 直接访问**（http://IP），无需备案
- 备案通过后域名才能解析并访问

**第 1 步 · 装环境**（SSH 登录后执行）：

```bash
sudo dnf install -y nginx git curl    # 老系统用 yum
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc
```

**第 2 步 · 拉取代码并构建**：

```bash
sudo mkdir -p /var/www/yzh-blog
sudo chown -R $USER /var/www/yzh-blog

# 国内服务器 clone GitHub 慢/失败时，用 ghproxy 镜像：
git clone https://ghproxy.com/https://github.com/YZD8355H/YZH-s-blog.git /var/www/yzh-blog/src
# 能直连就正常 clone 即可

cd /var/www/yzh-blog/src
uv sync && uv run build.py
ls site/          # 确认生成了 index.html
```

**第 3 步 · 配 Nginx**：

```bash
sudo vim /etc/nginx/conf.d/yzh-blog.conf    # CentOS/Alibaba Cloud Linux 用 conf.d
```

```nginx
server {
    listen 80;
    server_name 你的域名或服务器IP;   # 没域名就填 IP

    root /var/www/yzh-blog/src/site;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
    location ~* \.(css|js|svg|png|jpg|webp)$ {
        expires 7d;
        add_header Cache-Control "public";
    }
    error_page 404 /404.html;
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

浏览器打开 `http://服务器IP` 即可访问。

**第 4 步 · HTTPS（有备案域名时）**

```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

**日常更新文章**：

```bash
cd /var/www/yzh-blog/src && git pull && uv run build.py
```

> 更省事：本机构建后只上传产物 —— `scp -r site/ 用户名@IP:/var/www/yzh-blog/`（root 指向 /var/www/yzh-blog 即可）。

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
