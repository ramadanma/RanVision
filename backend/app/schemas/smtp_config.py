from pydantic import BaseModel


class SmtpConfigOut(BaseModel):
    host: str
    port: int
    username: str
    from_addr: str
    use_tls: bool


class SmtpConfigUpdate(BaseModel):
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    from_addr: str | None = None
    use_tls: bool | None = None
