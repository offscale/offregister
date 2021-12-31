from marshmallow.decorators import post_load
from marshmallow.fields import Nested, Str
from marshmallow.schema import Schema


class KvServerSchema(Schema):
    url = Str()
    type = Str()
    version = Str()

    class IUnmarshalResult:
        """Interface; used exclusively for typing"""

        @property
        def data(self):
            """
            :return: UDT object populated with parsed content
            :rtype: ``KvServer``
            """
            raise NotImplementedError()

        @property
        def error(self):
            raise NotImplementedError()

    @post_load(pass_many=True)
    def to_obj(self, in_data, many):
        """
        To UDT object

        :keyword in_data: Parsed content
        :type in_data: ``str|[str]|[{}]|{}``

        :keyword many: Set to true when `pass_many=True`
        :type many: ``bool``

        :return: Namedtuple of (`errors`, `data`); with `data` containing parsed UDT object
        :rtype: ``ConfMetaSchema.IUnmarshalResult``
        """
        return KvServer(**in_data)


class KvServer(object):
    def __init__(self, url, type, version):
        self.url = url  # type: str
        self.type = type  # type: str
        self.version = version  # type: str


class ConfMetaSchema(Schema):
    name = Str()
    description = Str()
    version = Str()
    default_pick = Str()
    kv_server = Nested(KvServerSchema)

    class IUnmarshalResult:
        """Interface; used exclusively for typing"""

        @property
        def data(self):
            """
            :return: UDT object populated with parsed content
            :rtype: ``ConfMeta``
            """
            raise NotImplementedError()

        @property
        def error(self):
            raise NotImplementedError()

    @post_load(pass_many=True)
    def to_obj(self, in_data, many):
        """
        To UDT object

        :keyword in_data: Parsed content
        :type in_data: ``str|[str]|[{}]|{}``

        :keyword many: Set to true when `pass_many=True`
        :type many: ``bool``

        :return: Namedtuple of (`errors`, `data`); with `data` containing parsed UDT object
        :rtype: ``ConfMetaSchema.IUnmarshalResult``
        """
        return ConfMeta(**in_data)


class ConfMeta(object):
    def __init__(self, name, description, version, default_pick, kv_server):
        self.name = name  # type: str
        self.description = description  # type: str
        self.version = version  # type: str
        self.default_pick = default_pick  # type: str
        self.kv_server = KvServer(**kv_server)
