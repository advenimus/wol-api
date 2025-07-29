use crate::guards::db_guard::DbGuard;
use rocket::serde::json::{Json, serde_json, Value};
use rocket::{get, State};
use sqlx::{Pool, Postgres};

#[get("/health")]
pub async fn health_check(
    pool: &State<Pool<Postgres>>,
    _db_guard: DbGuard<'_>,
) -> Json<Value> {
    // Test database connection
    let db_status = match sqlx::query("SELECT 1").fetch_one(pool.inner()).await {
        Ok(_) => "connected",
        Err(_) => "disconnected",
    };

    Json(serde_json::json!({
        "status": "ok",
        "database": db_status,
        "service": "wol-api",
        "version": "1.0.0"
    }))
}

#[get("/api/v1/health")]
pub async fn health_check_v1(
    pool: &State<Pool<Postgres>>,
    _db_guard: DbGuard<'_>,
) -> Json<Value> {
    health_check(pool, _db_guard).await
}