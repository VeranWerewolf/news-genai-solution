-- Initialize database schema for news articles metadata

-- Create articles table
CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(255) PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    source TEXT,
    published_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create topics table
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    CONSTRAINT unique_topic_name UNIQUE (name)
);

-- Create article_topics junction table
CREATE TABLE IF NOT EXISTS article_topics (
    article_id VARCHAR(255) NOT NULL,
    topic_id INTEGER NOT NULL,
    PRIMARY KEY (article_id, topic_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Create index on topics
CREATE INDEX IF NOT EXISTS idx_topic_name ON topics (name);

-- Create index on article titles for text search
CREATE INDEX IF NOT EXISTS idx_article_title ON articles USING GIN (to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_article_summary ON articles USING GIN (to_tsvector('english', summary));

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$ language 'plpgsql';

-- Create trigger for timestamp update
CREATE TRIGGER update_article_timestamp
BEFORE UPDATE ON articles
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();
