use rocket::serde::json::serde_json;
use serde::{Deserialize, Serialize};
use sqlx;

#[derive(sqlx::FromRow, Serialize, Deserialize, Debug)]
pub struct BibleVerse {
    pub book_num: i32,
    pub book_name: String,
    pub chapter: i32,
    pub verse_num: i32,
    pub verse_text: String,
    pub study_notes: Option<serde_json::Value>,
}
