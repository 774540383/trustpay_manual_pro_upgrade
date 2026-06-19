from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    main_bot_token: str = Field(alias="MAIN_BOT_TOKEN")
    kyc_bot_token: str = Field(alias="KYC_BOT_TOKEN")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change-me", alias="ADMIN_PASSWORD")
    public_base_url: str = Field(default="http://localhost:8000", alias="PUBLIC_BASE_URL")
    whatsapp_url: str = Field(default="https://wa.me/967700000000", alias="WHATSAPP_URL")
    brand_name: str = Field(default="TrustPay", alias="BRAND_NAME")
    database_path: str = Field(default="/app/data/trustpay.db", alias="DATABASE_PATH")
    upload_dir: str = Field(default="/app/data/uploads", alias="UPLOAD_DIR")

    @property
    def admin_id_list(self) -> list[int]:
        ids=[]
        for x in self.admin_ids.split(','):
            x=x.strip()
            if x.isdigit(): ids.append(int(x))
        return ids

    class Config:
        env_file = ".env"
        populate_by_name = True

settings = Settings()
