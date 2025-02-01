from pydantic import BaseModel


class UserPorfolioShareConsentRequst(BaseModel):
    sharing: bool
