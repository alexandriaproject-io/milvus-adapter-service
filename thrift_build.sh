#!/bin/bash

# Check the first argument for the language flag and use the second argument as the output directory if provided
if [[ "$1" == "--py" ]]; then
    py_outdir="${2:-./}" # Corrected syntax for default value
    mkdir -p "$py_outdir"
    thrift --gen py -out $py_outdir ./thrift/com.milvus.nats.thrift

elif [[ "$1" == "--html" ]]; then
    html_outdir="${2:-./src/services/status_server/static}" # Corrected syntax for default value
    mkdir -p "$html_outdir"
    thrift --gen html -out $html_outdir ./thrift/com.milvus.nats.thrift

elif [[ "$1" == "--golang" ]]; then
    golang_outdir="${2:-./}" # Corrected syntax for default value
    mkdir -p "$golang_outdir"
    thrift --gen go -out $golang_outdir ./thrift/com.milvus.nats.thrift

elif [[ "$1" == "--ts" ]]; then
    ts_outdir="${2:-./}" # Assuming default TypeScript output directory
    mkdir -p "$ts_outdir"
    # Assuming "ts" as the generator name for TypeScript, adjust as needed
    thrift --gen js:ts -out $ts_outdir ./thrift/com.milvus.nats.thrift
fi