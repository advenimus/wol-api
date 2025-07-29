use crate::guards::db_guard::DbGuard;
use crate::services::study_services;
use rocket::serde::json::{Json, serde_json, Value};
use rocket::{get, State};
use sqlx::{Pool, Postgres};

#[get("/study/<book>/<chapter>/<verse>?<fields>&<limit>")]
pub async fn get_verse_with_study(
    pool: &State<Pool<Postgres>>,
    book: i32,
    chapter: i32,
    verse: i32,
    fields: Option<String>,
    limit: Option<usize>,
    _db_guard: DbGuard<'_>,
) -> Result<Json<Value>, rocket::response::status::NotFound<String>> {
    match study_services::get_verse_with_study(pool, book, chapter, verse).await {
        Ok(Some(verse_with_study)) => {
            // Convert to JSON Value for filtering
            let mut json_value = serde_json::to_value(verse_with_study).unwrap();
            
            // Apply field filtering if specified
            if let Some(fields_str) = &fields {
                json_value = filter_fields(json_value, fields_str, limit);
            }
            
            Ok(Json(json_value))
        },
        Ok(None) => Err(rocket::response::status::NotFound("Verse not found".to_string())),
        Err(e) => {
            eprintln!("Database error: {}", e);
            Err(rocket::response::status::NotFound("Database error".to_string()))
        }
    }
}

fn filter_fields(data: Value, fields: &str, limit: Option<usize>) -> Value {
    let field_list: Vec<&str> = fields.split(',').map(|s| s.trim()).collect();
    let mut result = serde_json::Map::new();
    
    // Sort fields to ensure verse properties come first (paths without dots)
    let mut sorted_fields = field_list.clone();
    sorted_fields.sort_by(|a, b| {
        let a_is_direct = !a.contains('.');
        let b_is_direct = !b.contains('.');
        match (a_is_direct, b_is_direct) {
            (true, false) => std::cmp::Ordering::Less,
            (false, true) => std::cmp::Ordering::Greater,
            _ => a.cmp(b)
        }
    });
    
    for field_path in sorted_fields {
        if let Some(mut value) = extract_field_value(&data, field_path) {
            // Apply limit to arrays if limit is specified
            if let Some(limit_count) = limit {
                if let Value::Array(ref arr) = value {
                    if arr.len() > limit_count {
                        let limited_arr: Vec<Value> = arr.iter().take(limit_count).cloned().collect();
                        value = Value::Array(limited_arr);
                    }
                }
            }
            
            // Use the last component of the path as the key
            let final_key = field_path.split('.').last().unwrap_or(field_path);
            result.insert(final_key.to_string(), value);
        }
    }
    
    Value::Object(result)
}

fn extract_field_value(data: &Value, field_path: &str) -> Option<Value> {
    extract_field_recursive(data, &field_path.split('.').collect::<Vec<_>>())
}

fn extract_field_recursive(data: &Value, path_parts: &[&str]) -> Option<Value> {
    if path_parts.is_empty() {
        return Some(data.clone());
    }
    
    let current_part = path_parts[0];
    let remaining_parts = &path_parts[1..];
    
    match data {
        Value::Object(obj) => {
            let field_value = obj.get(current_part)?;
            
            if remaining_parts.is_empty() {
                Some(field_value.clone())
            } else {
                extract_field_recursive(field_value, remaining_parts)
            }
        },
        Value::Array(arr) => {
            // For arrays, collect values from all elements
            let mut collected = Vec::new();
            
            for item in arr {
                if let Some(value) = extract_field_recursive(item, path_parts) {
                    // If the extracted value is an array, flatten it
                    match value {
                        Value::Array(inner_arr) => {
                            collected.extend(inner_arr);
                        },
                        _ => collected.push(value),
                    }
                }
            }
            
            if collected.is_empty() {
                None
            } else {
                Some(Value::Array(collected))
            }
        },
        _ => None,
    }
}

