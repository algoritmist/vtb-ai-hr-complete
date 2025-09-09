from typing import Optional
from common.schemas import UserSchema


class CandidateSchema(UserSchema):
    resume: Optional[str] = None
