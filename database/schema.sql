-- DROP DATABASE IF EXISTS gamevault;
CREATE DATABASE IF NOT EXISTS gamevault CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE gamevault;

-- 1. Publishers
CREATE TABLE publishers (
    publisher_id INT AUTO_INCREMENT PRIMARY KEY,
    publisher_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE = InnoDB;

-- 2. Developers
CREATE TABLE developers (
    dev_id INT AUTO_INCREMENT PRIMARY KEY,
    dev_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE = InnoDB;

-- 3. Users
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    affiliate_publisher_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_verified CHECK (email_verified IN (0, 1)),
    CONSTRAINT chk_users_admin CHECK (is_admin IN (0, 1)),
    CONSTRAINT fk_user_publisher FOREIGN KEY (affiliate_publisher_id) REFERENCES publishers (publisher_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 4. Genres
CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(50) NOT NULL UNIQUE
) ENGINE = InnoDB;

-- 5. Platforms
CREATE TABLE platforms (
    platform_id INT AUTO_INCREMENT PRIMARY KEY,
    platform_name VARCHAR(50) NOT NULL UNIQUE
) ENGINE = InnoDB;

-- 6. Games
CREATE TABLE games (
    game_id INT AUTO_INCREMENT PRIMARY KEY,
    game_name VARCHAR(150) NOT NULL,
    description TEXT,
    thumbnail_url VARCHAR(255),
    publisher_id INT NOT NULL,
    developer_id INT NOT NULL,
    standard_price DECIMAL(10, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    release_date DATE NULL,
    average_rating DECIMAL(3, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT chk_game_price CHECK (standard_price >= 0),
    CONSTRAINT chk_game_discount CHECK (
        discount_percent BETWEEN 0 AND 100
    ),
    CONSTRAINT chk_game_rating CHECK (
        average_rating BETWEEN 0 AND 5
    ),
    CONSTRAINT fk_game_publisher FOREIGN KEY (publisher_id) REFERENCES publishers (publisher_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_game_developer FOREIGN KEY (developer_id) REFERENCES developers (dev_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 7. Game genres
CREATE TABLE game_genres (
    game_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (game_id, genre_id),
    CONSTRAINT fk_gg_game FOREIGN KEY (game_id) REFERENCES games (game_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gg_genre FOREIGN KEY (genre_id) REFERENCES genres (genre_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 8. Game platforms
CREATE TABLE game_platforms (
    game_id INT NOT NULL,
    platform_id INT NOT NULL,
    PRIMARY KEY (game_id, platform_id),
    CONSTRAINT fk_gp_game FOREIGN KEY (game_id) REFERENCES games (game_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_gp_platform FOREIGN KEY (platform_id) REFERENCES platforms (platform_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 9. Cart items: one logical cart per user, no quantities.
CREATE TABLE cart_items (
    cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_id INT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cart_user_game UNIQUE (user_id, game_id),
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cart_game FOREIGN KEY (game_id) REFERENCES games (game_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 10. Payments: simulation only; use dummy account references.
-- Original column names retained for compatibility with the team README.
-- payee_account_no is ambiguously named: use it as the simulated payer reference
-- in this prototype; rename consistently across the project if the team agrees.
CREATE TABLE payments (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    payee_account_no VARCHAR(50) NOT NULL,
    recipient_account_no VARCHAR(50) NOT NULL,
    payment_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0),
    CONSTRAINT chk_payment_status CHECK (
        payment_status IN (
            'SUCCESS',
            'FAILED',
            'REFUNDED'
        )
    )
) ENGINE = InnoDB;

-- 11. Orders: at most one payment per order and one order per payment.
-- Retry after a failed simulated payment creates a new order.
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    order_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    transaction_id INT NULL,
    CONSTRAINT uq_order_transaction UNIQUE (transaction_id),
    CONSTRAINT chk_order_status CHECK (
        order_status IN (
            'PENDING',
            'PAID',
            'CANCELLED',
            'REFUNDED'
        )
    ),
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_payment FOREIGN KEY (transaction_id) REFERENCES payments (transaction_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 12. Order items: preserve the price charged at checkout.
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    game_id INT NOT NULL,
    price_paid DECIMAL(10, 2) NOT NULL,
    CONSTRAINT uq_order_game UNIQUE (order_id, game_id),
    CONSTRAINT chk_price_paid CHECK (price_paid >= 0),
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oi_game FOREIGN KEY (game_id) REFERENCES games (game_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 13. Reviews: one review per user/game; half-star increments.
CREATE TABLE reviews (
    user_id INT NOT NULL,
    game_id INT NOT NULL,
    rating DECIMAL(2, 1) NOT NULL,
    review_text TEXT,
    review_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, game_id),
    CONSTRAINT chk_review_rating CHECK (
        rating IN (
            0.0,
            0.5,
            1.0,
            1.5,
            2.0,
            2.5,
            3.0,
            3.5,
            4.0,
            4.5,
            5.0
        )
    ),
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_review_game FOREIGN KEY (game_id) REFERENCES games (game_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 14. Wishlists
CREATE TABLE wishlists (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_id INT NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wishlist_user_game UNIQUE (user_id, game_id),
    CONSTRAINT fk_wishlist_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_wishlist_game FOREIGN KEY (game_id) REFERENCES games (game_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;