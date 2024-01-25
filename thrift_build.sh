thrift --gen py -out .\ .\thrift\com.milvus.nats.thrift

thrift --gen html -out .\src\services\status_server\static .\thrift\com.milvus.nats.thrift
