from typing import Dict
from typing import runtime_checkable
from typing import Type
from typing import TypeVar

_protocol_translator: Dict[Type, Type] = {}


ProtocolType = TypeVar("ProtocolType", bound=type)


def translate_protocol(type_: Type[ProtocolType]) -> Type[ProtocolType]:
    value = _protocol_translator.get(type_) or runtime_checkable(type_)
    _protocol_translator[type_] = value
    return value
