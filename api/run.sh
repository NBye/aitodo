#!/bin/bash
echo "start $1 $2"
source /opt/conda/etc/profile.d/conda.sh
conda activate aitodo

export QUART_ENV='production'
export AITODO_PROT=6100
export AITODO_HOST='http://localhost:6200'
export AITODO_ROOT_DIR='/aitodo/api'
export ES_CONNECT_SETTING_HOST="http://localhost:9200"
export EMAIL_SENDER="netsound@foxmail.com"
export EMAIL_AUTH="ltqcpwtgafgdeajg"
export EMAIL_SMTP="smtp.qq.com"
export EMAIL_PORT="587"
export EMAIL_LABEL="网音·AiTodo"


if [ "$1" = "consumer" ]; then
    cd "$AITODO_ROOT_DIR" || exit 1
    echo $AITODO_ROOT_DIR
    python consumer.py -n $2

elif [ "$1" = "production" ]; then
    fuser -k $AITODO_PROT/tcp
    cd "$AITODO_ROOT_DIR" || exit 1
    echo $AITODO_ROOT_DIR
    uvicorn api:app --host 0.0.0.0 --port $AITODO_PROT --workers 4 --timeout-keep-alive 300 --log-level info
else
    export QUART_ENV='development'
    fuser -k $AITODO_PROT/tcp
    uvicorn api:app --host 0.0.0.0 --port $AITODO_PROT --workers 4 --timeout-keep-alive 300 --log-level debug --reload 
fi