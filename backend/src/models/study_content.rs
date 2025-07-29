use rocket::serde::json::serde_json;
use serde::{Deserialize, Serialize};
use sqlx;

#[derive(sqlx::FromRow, Serialize, Deserialize, Debug)]
pub struct StudyContent {
    pub id: i32,
    pub book_num: i32,
    pub chapter: i32,
    pub outline: Vec<String>,
    pub study_articles: serde_json::Value,
    pub cross_references: serde_json::Value,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct StudyArticle {
    pub title: String,
    pub url: String,
    #[serde(rename = "type")]
    pub article_type: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CrossReference {
    pub reference: String,
    pub url: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct VerseWithStudy {
    pub verse: super::bible_verse::BibleVerse,
    pub study_content: Option<StudyContent>,
}