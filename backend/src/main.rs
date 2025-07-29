use rocket;
use sqlx::{postgres::PgPoolOptions, Pool, Postgres};

mod guards;
mod models;
mod routes;
mod services;

#[rocket::get("/")]
fn home() -> &'static str {
    "Hello, world!"
}

#[rocket::launch]
async fn entrypoint() -> rocket::Rocket<rocket::Build> {
    rocket::build()
        .manage(init_db_pool().await)
        .mount("/", rocket::routes![routes::health::health_check])
        .mount("/api/v1", rocket::routes![home, routes::verse::get_verse, routes::study::get_verse_with_study, routes::health::health_check_v1])
}

async fn init_db_pool() -> Pool<Postgres> {
    println!("Connecting to database...");
    let pool_result = PgPoolOptions::new()
        .acquire_timeout(std::time::Duration::from_secs(10))
        .connect("postgresql://postgres:postgres@db:5432/wol-api")
        .await;

    return pool_result.unwrap();
}
