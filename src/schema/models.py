from pydantic import BaseModel, Field


class ColumnDef(BaseModel):
    name: str
    type: str = "string"
    required: bool = False
    description: str = ""


class Schema(BaseModel):
    name: str
    description: str = ""
    columns: list[ColumnDef]


class MappingRule(BaseModel):
    model_config = {"populate_by_name": True}
    from_: str = Field(alias="from")
    to: str


class SupplierMapping(BaseModel):
    supplier: str
    name: str
    description: str = ""
    mapping: list[MappingRule]
