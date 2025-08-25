FROM rust:latest

RUN apt-get update && apt-get --no-install-recommends install -y iputils-ping python3 python3-pip postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for scraping
RUN pip3 install --break-system-packages requests beautifulsoup4 psycopg2-binary

RUN useradd --create-home appuser
WORKDIR /home/appuser
VOLUME /home/appuser

COPY ./backend /home/appuser/
COPY ./scripts /home/appuser/scripts/
COPY ./data /home/appuser/data/
# Note: credentials.txt must be created manually on the server for security
# See credentials.txt.example for format


# ensure rust is on the latest stable version
# RUN rustup update && rustup default stable

# RUN cargo clean && \
#     cargo install --path . && \
#     cargo build

EXPOSE 8000

# Make scripts executable
RUN chmod +x /home/appuser/scripts/*.sh
RUN chmod +x /home/appuser/scripts/*.py

# Start both the health monitor and the main backend
CMD ["/home/appuser/scripts/start_services.sh"]

# http://127.0.0.1:8000/api/v1/bible-verses
