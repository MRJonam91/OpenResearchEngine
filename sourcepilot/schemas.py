"""Strict request contracts shared by the local API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_IDENTIFIER = 2 ** 63 - 1
Identifier = Annotated[int, Field(strict=True, gt=0, le=MAX_IDENTIFIER)]
RouteIdentifier = Annotated[int, Field(gt=0, le=MAX_IDENTIFIER)]
Statement = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=5000)]


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class URLInput(Payload):
    url: Annotated[str, Field(strict=True, min_length=1, max_length=8192)]


class ClaimInput(Payload):
    text: Statement
    passage_id: Identifier


class TextInput(Payload):
    text: Statement


class ReviewInput(Payload):
    status: Literal["proposed", "approved", "uncertain", "rejected"]
    note: Annotated[str, Field(strict=True, max_length=5000)] = ""


class EvidenceInput(Payload):
    passage_id: Identifier
    stance: Literal["supports", "challenges", "context"]
