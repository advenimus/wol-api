use crate::models::bible_verse::BibleVerse;
use crate::models::study_content::{StudyContent, VerseWithStudy};
use sqlx::{Pool, Postgres, Row};
use std::process::Command;

pub async fn get_verse_with_study(
    pool: &Pool<Postgres>,
    book: i32,
    chapter: i32,
    verse: i32,
) -> Result<Option<VerseWithStudy>, sqlx::Error> {
    // Get the verse
    let verse_row = sqlx::query("SELECT * FROM verses WHERE book_num = $1 AND chapter = $2 AND verse_num = $3")
        .bind(book)
        .bind(chapter)
        .bind(verse)
        .fetch_optional(pool)
        .await?;

    if let Some(row) = verse_row {
        let bible_verse = BibleVerse {
            book_num: row.get("book_num"),
            book_name: row.get("book_name"),
            chapter: row.get("chapter"),
            verse_num: row.get("verse_num"),
            verse_text: row.get("verse_text"),
            study_notes: row.get("study_notes"),
        };

        // Get study content for the chapter
        let study_row = sqlx::query("SELECT * FROM study_content WHERE book_num = $1 AND chapter = $2")
            .bind(book)
            .bind(chapter)
            .fetch_optional(pool)
            .await?;

        let study_content = if let Some(study_row) = study_row {
            Some(StudyContent {
                id: study_row.get("id"),
                book_num: study_row.get("book_num"),
                chapter: study_row.get("chapter"),
                outline: study_row.get("outline"),
                study_articles: study_row.get("study_articles"),
                cross_references: study_row.get("cross_references"),
            })
        } else {
            // Study content missing - try to scrape it
            println!("Study content missing for book {}, chapter {}, attempting to scrape...", book, chapter);
            
            if scrape_study_content(book, chapter).await {
                // Retry query after scraping
                let study_row = sqlx::query("SELECT * FROM study_content WHERE book_num = $1 AND chapter = $2")
                    .bind(book)
                    .bind(chapter)
                    .fetch_optional(pool)
                    .await?;
                
                if let Some(study_row) = study_row {
                    Some(StudyContent {
                        id: study_row.get("id"),
                        book_num: study_row.get("book_num"),
                        chapter: study_row.get("chapter"),
                        outline: study_row.get("outline"),
                        study_articles: study_row.get("study_articles"),
                        cross_references: study_row.get("cross_references"),
                    })
                } else {
                    None
                }
            } else {
                None
            }
        };

        Ok(Some(VerseWithStudy {
            verse: bible_verse,
            study_content,
        }))
    } else {
        Ok(None)
    }
}

async fn scrape_study_content(book: i32, chapter: i32) -> bool {
    let output = Command::new("python3")
        .arg("scripts/scrape_with_study_notes_docker.py")
        .arg(&book.to_string())
        .arg(&chapter.to_string())
        .output();
    
    match output {
        Ok(result) => {
            if result.status.success() {
                println!("Successfully scraped study content for book {}, chapter {}", book, chapter);
                true
            } else {
                eprintln!("Scraping failed: {}", String::from_utf8_lossy(&result.stderr));
                false
            }
        }
        Err(e) => {
            eprintln!("Failed to execute scraping script: {}", e);
            false
        }
    }
}