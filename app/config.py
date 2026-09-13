import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "payflow-dev-secret-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
