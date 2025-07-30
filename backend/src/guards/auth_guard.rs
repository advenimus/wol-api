use rocket::request::{self, FromRequest, Request};
use rocket::outcome::Outcome;
use rocket::http::Status;
use std::fs;
use base64::{Engine as _, engine::general_purpose};

pub struct AuthGuard;

#[derive(Debug)]
pub enum AuthError {
    Missing,
    Invalid,
}

#[rocket::async_trait]
impl<'r> FromRequest<'r> for AuthGuard {
    type Error = AuthError;

    async fn from_request(request: &'r Request<'_>) -> request::Outcome<Self, Self::Error> {
        // Get Authorization header
        let auth_header = match request.headers().get_one("Authorization") {
            Some(header) => header,
            None => return Outcome::Failure((Status::Unauthorized, AuthError::Missing)),
        };

        // Check if it's Basic auth
        if !auth_header.starts_with("Basic ") {
            return Outcome::Failure((Status::Unauthorized, AuthError::Invalid));
        }

        // Decode the base64 credentials
        let encoded_credentials = &auth_header[6..]; // Skip "Basic "
        let decoded_bytes = match general_purpose::STANDARD.decode(encoded_credentials) {
            Ok(bytes) => bytes,
            Err(_) => return Outcome::Failure((Status::Unauthorized, AuthError::Invalid)),
        };

        let credentials_str = match String::from_utf8(decoded_bytes) {
            Ok(s) => s,
            Err(_) => return Outcome::Failure((Status::Unauthorized, AuthError::Invalid)),
        };

        // Split username:password
        let parts: Vec<&str> = credentials_str.splitn(2, ':').collect();
        if parts.len() != 2 {
            return Outcome::Failure((Status::Unauthorized, AuthError::Invalid));
        }

        let username = parts[0];
        let password = parts[1];

        // Load credentials from file
        let credentials_content = match fs::read_to_string("credentials.txt") {
            Ok(content) => content,
            Err(_) => {
                eprintln!("Failed to read credentials.txt file");
                return Outcome::Failure((Status::InternalServerError, AuthError::Invalid));
            }
        };

        // Check credentials
        for line in credentials_content.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            
            let cred_parts: Vec<&str> = line.splitn(2, ':').collect();
            if cred_parts.len() == 2 {
                let file_username = cred_parts[0].trim();
                let file_password = cred_parts[1].trim();
                
                if username == file_username && password == file_password {
                    return Outcome::Success(AuthGuard);
                }
            }
        }

        Outcome::Failure((Status::Unauthorized, AuthError::Invalid))
    }
}