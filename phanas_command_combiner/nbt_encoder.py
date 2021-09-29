from abc import ABCMeta, abstractmethod
import json
from typing import Union

__all__ = [
    'NBTNode', 'RawNBT',
    'IntegralNode', 'Byte', 'Short', 'Int', 'Long',
    'DecimalNode', 'Float', 'Double',
    'JsonComponent',
    'NBTEncoder'
]


class NBTNode(metaclass=ABCMeta):

    @abstractmethod
    def encode(self) -> str:
        pass


class RawNBT(NBTNode):

    def __init__(self, text: str):
        self.text = text

    def encode(self):
        return self.text


class IntegralNode(NBTNode, metaclass=ABCMeta):
    min = 0
    max = 0
    suffix = ''

    def __init__(self, value: int):
        if value < self.min or value > self.max:
            raise ValueError(
                f"{self.__class__.__name__} must be between {self.min} and "
                f"{self.max} (inclusive), got {value}"
            )
        self.value = value

    def encode(self):
        return f'{self.value}{self.suffix}'


class Byte(IntegralNode):
    min = -(1 << 7)
    max = (1 << 7) - 1
    suffix = 'b'


class Short(IntegralNode):
    min = -(1 << 15)
    max = (1 << 15) - 1
    suffix = 's'


class Int(IntegralNode):
    min = -(1 << 31)
    max = (1 << 31) - 1


class Long(IntegralNode):
    min = -(1 << 63)
    max = (1 << 63) - 1
    suffix = 'L'


class DecimalNode(NBTNode, metaclass=ABCMeta):
    suffix = ''

    def __init__(self, value: float, precision: int = 6):
        self.value = value
        self.precision = precision

    def encode(self):
        return f'{self.value:.6f}{self.suffix}'


class Float(DecimalNode):
    suffix = 'f'


class Double(DecimalNode):
    pass


class JsonComponent(NBTNode):

    def __init__(self, json_: Union[str, list, dict], as_str = True):
        """
        A JSON chat component
        :param json_: the json structure
        :param as_str: whether this field should be encoded as a string
        """
        self.json = json_
        self.as_str = as_str

    def encode(self):
        dump = json.dumps(self.json)
        if self.as_str:
            return repr(dump)
        return dump


class NBTEncoder:

    def __init__(self, quote_strings: bool = True):
        self.quote_strings = quote_strings

    def encode(self, obj):
        if isinstance(obj, NBTNode):
            return obj.encode()

        if isinstance(obj, dict):
            return self.encode_dict(obj)

        if isinstance(obj, list):
            return self.encode_list(obj)

        if isinstance(obj, str):
            return self.encode_str(obj)

        if isinstance(obj, float):
            return self.encode_float(obj)

        if isinstance(obj, bool):
            # bools are also ints, so do this before ints
            return self.encode_bool(obj)

        if isinstance(obj, int) and not isinstance(obj, bool):
            return self.encode_int(obj)

        if obj is None:
            return self.encode_none()

        raise ValueError(
            f"Failed to match type of {obj} ({type(obj)}) to any NBT type"
        )

    def encode_dict(self, obj: dict) -> str:
        if not obj:
            return '{}'

        items = ['{']
        for k, v in obj.items():
            items.extend([k, ':', self.encode(v), ','])
        items[-1] = '}'
        return ''.join(items)

    def encode_list(self, obj: list) -> str:
        if not obj:
            return '[]'

        items = ['[']
        for i in obj:
            items.extend([self.encode(i), ','])
        items[-1] = ']'
        return ''.join(items)

    def encode_str(self, obj: str) -> str:
        if self.quote_strings:
            return repr(obj)
        return obj

    def encode_float(self, obj: float) -> str:
        return Float(obj).encode()

    def encode_int(self, obj: int) -> str:
        return Int(obj).encode()

    def encode_bool(self, obj: bool) -> str:
        return str(obj).lower()

    def encode_none(self) -> str:
        return 'null'
