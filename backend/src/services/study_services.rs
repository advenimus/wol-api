use crate::models::bible_verse::BibleVerse;
use crate::models::study_content::{StudyContent, VerseWithStudy, VerseRange};
use rocket::serde::json::serde_json;
use sqlx::{Pool, Postgres, Row};
use std::process::Command;

pub async fn get_verse_with_study(
    pool: &Pool<Postgres>,
    book: i32,
    chapter: i32,
    verse: i32,
    force_fetch: bool,
) -> Result<Option<VerseWithStudy>, sqlx::Error> {
    // If force_fetch is true, delete existing study content to ensure fresh scraping
    if force_fetch {
        println!("Force fetch requested - clearing existing study content for book {}, chapter {}", book, chapter);
        sqlx::query("DELETE FROM study_content WHERE book_num = $1 AND chapter = $2")
            .bind(book)
            .bind(chapter)
            .execute(pool)
            .await?;
        
        // Also clear verse study_notes to force fresh scraping
        sqlx::query("UPDATE verses SET study_notes = NULL WHERE book_num = $1 AND chapter = $2")
            .bind(book)
            .bind(chapter)
            .execute(pool)
            .await?;
    }

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
            // Study content missing or force_fetch requested - try to scrape it
            if force_fetch {
                println!("Force fetch: attempting to scrape study content for book {}, chapter {}...", book, chapter);
            } else {
                println!("Study content missing for book {}, chapter {}, attempting to scrape...", book, chapter);
            }
            
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

        // If we force_fetch, we need to re-query the verse to get updated study_notes
        let bible_verse = if force_fetch {
            // Re-query the verse after scraping to get updated study_notes
            let updated_verse_row = sqlx::query("SELECT * FROM verses WHERE book_num = $1 AND chapter = $2 AND verse_num = $3")
                .bind(book)
                .bind(chapter)
                .bind(verse)
                .fetch_optional(pool)
                .await?;

            if let Some(row) = updated_verse_row {
                BibleVerse {
                    book_num: row.get("book_num"),
                    book_name: row.get("book_name"),
                    chapter: row.get("chapter"),
                    verse_num: row.get("verse_num"),
                    verse_text: row.get("verse_text"),
                    study_notes: row.get("study_notes"),
                }
            } else {
                bible_verse
            }
        } else {
            bible_verse
        };

        Ok(Some(VerseWithStudy {
            verse: bible_verse,
            study_content,
        }))
    } else {
        // Verse not found - try to scrape it
        if force_fetch {
            println!("Force fetch: attempting to scrape verse content for book {}, chapter {}, verse {}...", book, chapter, verse);
        } else {
            println!("Verse missing for book {}, chapter {}, verse {}, attempting to scrape...", book, chapter, verse);
        }
        
        if scrape_verse_content(book, chapter, verse).await {
            // Retry the verse query after scraping
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

                // Also try to get study content after verse scraping
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
                    None
                };

                Ok(Some(VerseWithStudy {
                    verse: bible_verse,
                    study_content,
                }))
            } else {
                Ok(None)
            }
        } else {
            Ok(None)
        }
    }
}

async fn scrape_verse_content(book: i32, chapter: i32, verse: i32) -> bool {
    // Use the same scraper that handles both verses and study content
    let output = Command::new("python3")
        .arg("scripts/scrape_with_study_notes_docker.py")
        .arg(&book.to_string())
        .arg(&chapter.to_string())
        .output();
    
    match output {
        Ok(result) => {
            if result.status.success() {
                println!("Successfully scraped verse content for book {}, chapter {}, verse {}", book, chapter, verse);
                true
            } else {
                eprintln!("Verse scraping failed: {}", String::from_utf8_lossy(&result.stderr));
                false
            }
        }
        Err(e) => {
            eprintln!("Failed to execute verse scraping script: {}", e);
            false
        }
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

pub async fn get_verse_range(
    pool: &Pool<Postgres>,
    book: i32,
    chapter: i32,
    start_verse: i32,
    end_verse: i32,
) -> Result<Option<VerseRange>, sqlx::Error> {
    // Get all verses in the range
    let verse_rows = sqlx::query("SELECT * FROM verses WHERE book_num = $1 AND chapter = $2 AND verse_num >= $3 AND verse_num <= $4 ORDER BY verse_num")
        .bind(book)
        .bind(chapter)
        .bind(start_verse)
        .bind(end_verse)
        .fetch_all(pool)
        .await?;

    if verse_rows.is_empty() {
        return Ok(None);
    }

    let mut combined_text = String::new();
    let mut study_notes = Vec::new();
    let mut book_name = String::new();

    for (index, row) in verse_rows.iter().enumerate() {
        if index == 0 {
            book_name = row.get("book_name");
        }
        
        // Add verse text to combined text
        let verse_text: String = row.get("verse_text");
        if index > 0 {
            combined_text.push(' ');
        }
        combined_text.push_str(&verse_text);
        
        // Extract study notes text if present
        let study_notes_json: Option<serde_json::Value> = row.get("study_notes");
        if let Some(notes_json) = study_notes_json {
            if let Some(notes_array) = notes_json.as_array() {
                for note in notes_array {
                    if let Some(content_array) = note.get("content").and_then(|c| c.as_array()) {
                        for content_item in content_array {
                            if let Some(text) = content_item.get("text").and_then(|t| t.as_str()) {
                                study_notes.push(text.to_string());
                            }
                        }
                    }
                }
            }
        }
    }

    let verse_range_str = if start_verse == end_verse {
        start_verse.to_string()
    } else {
        format!("{}-{}", start_verse, end_verse)
    };

    Ok(Some(VerseRange {
        book_num: book,
        book_name,
        chapter,
        verse_range: verse_range_str,
        combined_text,
        study_notes,
    }))
}