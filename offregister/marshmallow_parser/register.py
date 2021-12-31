from marshmallow.fields import Bool, Dict, Int, List, Nested, Str
from marshmallow.schema import Schema

from offregister.marshmallow_parser import ConfMetaSchema


class ExecFilter(Schema):
    op = Str()
    val = Int()
    exclude = List(Str())
    include = List(Str())


class Register(ConfMetaSchema):
    module = Str()
    cluster_name = Str()
    args = List(Str())
    kwargs = Dict()
    provisioner = Str()
    exec_filter = Nested(ExecFilter())
    stateful = Bool()

    dependencies = Nested("Register", many=True, exclude=("dependencies",))


class RegisterConfig(ConfMetaSchema):
    multicluster_name = Str()
    stateful = Bool()
    register = Nested(Register, many=True)

    dependencies = Nested("RegisterConfig", many=True, exclude=("dependencies",))
