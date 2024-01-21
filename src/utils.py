from logger import log
from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport
from typing import Type, TypeVar, Any, Union

T = TypeVar('T')  # Generic type variable


def thrift_to_binary(thrift_obj):
    transport = TTransport.TMemoryBuffer()
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    thrift_obj.write(protocol)
    return transport.getvalue()


def thrift_read(binary_data: Any, thrift_class: Type[T]) -> T:
    try:
        transport = TTransport.TMemoryBuffer(binary_data)
        record = thrift_class()
        record.read(TBinaryProtocol.TBinaryProtocol(transport))
        return record
    except Exception as e:
        log.error("Error: %s", e)
        return None
