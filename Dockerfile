FROM rust:latest

RUN apt-get update && apt-get --no-install-recommends install -y iputils-ping python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for scraping
RUN pip3 install --break-system-packages requests beautifulsoup4 psycopg2-binary

RUN useradd --create-home appuser
WORKDIR /home/appuser
VOLUME /home/appuser

COPY ./backend /home/appuser/
COPY ./scripts /home/appuser/scripts/
# Note: credentials.txt must be created manually on the server for security
# See credentials.txt.example for format

# ensure rust is on the latest stable version
# RUN rustup update && rustup default stable

# RUN cargo clean && \
#     cargo install --path . && \
#     cargo build

EXPOSE 8000
CMD ["cargo", "run", "--bin", "backend"]

# http://127.0.0.1:8000/api/v1/bible-verses
