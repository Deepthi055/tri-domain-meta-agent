from core.config import Settings


def test_database_defaults_to_sqlite_when_not_configured(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    settings = Settings(_env_file=None)
    assert settings.DATABASE_URL.startswith('sqlite')


def test_database_accepts_supabase_postgres_url(monkeypatch):
    monkeypatch.setenv(
        'DATABASE_URL',
        'postgresql://postgres:password@db.xxxxxx.supabase.co:5432/postgres?sslmode=require',
    )
    settings = Settings(_env_file=None)
    assert 'supabase.co' in settings.DATABASE_URL
    assert 'sslmode=require' in settings.DATABASE_URL
