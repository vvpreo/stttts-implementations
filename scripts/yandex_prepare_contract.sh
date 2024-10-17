#!/bin/sh

pip install grpcio grpcio-tools

git clone https://github.com/yandex-cloud/cloudapi yandex_cloudapi

curdir=$(pwd)

cd yandex_cloudapi && \
mkdir ../src/yandex_stt && \
python3 -m grpc_tools.protoc -I . -I third_party/googleapis \
   --python_out=../src/yandex_stt \
   --grpc_python_out=../src/yandex_stt \
     google/api/http.proto \
     google/api/annotations.proto \
     yandex/cloud/api/operation.proto \
     google/rpc/status.proto \
     yandex/cloud/operation/operation.proto \
     yandex/cloud/validation.proto \
     yandex/cloud/ai/stt/v3/stt_service.proto \
     yandex/cloud/ai/stt/v3/stt.proto


cd "$curdir" || exit 1
rm -rf yandex_cloudapi