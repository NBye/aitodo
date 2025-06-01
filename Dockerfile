FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN sed -i 's|http://.*.ubuntu.com|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get clean \
    && apt-get update
 
RUN apt-get install -y wget curl net-tools vim
RUN apt-get install -y openjdk-21-jdk
RUN apt-get install -y apt-transport-https gnupg software-properties-common

RUN apt-get install -y \
    bzip2 \
    ca-certificates \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    libmagic-dev \
    git \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 下载并安装 Anaconda3
ENV CONDA_DIR=/opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH
RUN wget --quiet https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh -O /tmp/anaconda.sh && \
    /bin/bash /tmp/anaconda.sh -b -p $CONDA_DIR && \
    rm /tmp/anaconda.sh && \
    $CONDA_DIR/bin/conda clean -ya

# 安装环境 source /opt/conda/etc/profile.d/conda.sh
RUN echo 'source /opt/conda/etc/profile.d/conda.sh' >> /root/.bashrc
COPY api/environment.yml /environment.yml
RUN bash -c "source /opt/conda/etc/profile.d/conda.sh && conda env create -f /environment.yml" && rm -f /environment.yml

# 安装nodejs
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN wget https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz && \
    tar -xJf node-v22.14.0-linux-x64.tar.xz && \
    mv node-v22.14.0-linux-x64 /usr/local/node && \
    ln -s /usr/local/node/bin/node /usr/local/bin/node && \
    ln -s /usr/local/node/bin/npm /usr/local/bin/npm && \
    ln -s /usr/local/node/bin/npx /usr/local/bin/npx && \
    rm node-v22.14.0-linux-x64.tar.xz
RUN npm install -g yarn
RUN ln -s /usr/local/node/bin/* /usr/bin/

# 安装 Redis 6.2
RUN apt-get update && apt-get install -y redis-server
RUN rm -rf /var/lib/apt/lists/*

# 安装 Elasticsearch 8.13.3
RUN wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.13.3-amd64.deb \
    && dpkg -i elasticsearch-8.13.3-amd64.deb \
    && rm elasticsearch-8.13.3-amd64.deb

# 安装 Code Server (最新版本)
RUN curl -fsSL https://code-server.dev/install.sh | sh

# 配置 Supervisor 统一管理服务
COPY data/supervisor/service.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露端口（Redis:6379, Elasticsearch:9200/9300）
EXPOSE 6379 9200 9300 9001 6000 6100 6200 8080

CMD ["/usr/bin/supervisord"]
