# -*- coding: utf-8 -*-
from marshmallow.decorators import post_load
from marshmallow.fields import Dict, List, Nested, Str
from marshmallow.schema import Schema

from offregister.marshmallow_parser import ConfMeta, ConfMetaSchema


class ProviderSchema(Dict):
    name = Str()
    region = Str()


class SshSchema(Schema):
    public_key_path = Str()
    private_key_path = Str()
    key_name = Str()
    node_password = Str()


class CredSchema(Schema):
    cred = Dict()
    ssh = Nested(SshSchema)
    key_name = Str()
    security_groups = List(Str())
    create_with = Dict()
    provider = ProviderSchema()


class AuthConfigSchema(ConfMetaSchema):
    _obj = None

    auth = Nested(CredSchema, many=True)

    class IUnmarshalResult:
        """Interface; used exclusively for typing"""

        @property
        def data(self):
            """
            :return: UDT object populated with parsed content
            :rtype: ```AuthConfig```
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
        :type in_data: ```Union[str,dict,List[Union[str,dict]]]```

        :keyword many: Set to true when `pass_many=True`
        :type many: ```bool```

        :return: UDT object populated with parsed content
        :rtype: ```AuthConfig```
        """
        return AuthConfig(**in_data)

        def load(self, data, many=None, partial=None):
            """Deserialize a data structure to an object defined by this Schema's fields and `make_object`.

            :keyword data: The data to deserialize.
            :type data: ```dict```

            :keyword many: Whether to deserialize `data` as a collection. If `None`, the value for `self.many` is used.
            :type many: ```bool```

            :keyword partial: Whether to ignore missing fields. If `None`,
                the value for `self.partial` is used. If its value is an iterable,
                only missing fields listed in that iterable will be ignored.
            :type partial: ```Union[bool,tuple]```

            :return: Namedtuple of (`errors`, `data`); with `data` containing parsed UDT object
            :rtype: ```AuthConfigSchema.IUnmarshalResult```
            """
            return super(AuthConfigSchema, self).load(
                data=data, many=many, partial=partial
            )


class AuthConfig(ConfMeta):
    def __init__(self, auth, **config_meta_opts):
        super(AuthConfig, self).__init__(**config_meta_opts)
        self.auth = auth
