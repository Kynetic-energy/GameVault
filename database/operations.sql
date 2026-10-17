USE gamevault;

-- ============================================================
-- 1. REVIEW AVERAGE TRIGGERS
-- ============================================================
-- The normal application edits only rating/text, not review identifiers.
-- The update trigger also handles explicit game_id changes in SQL.
-- Foreign-key cascades do not fire review triggers. Reconcile averages
-- after administrative cascade deletes/updates or bulk imports.

DROP TRIGGER IF EXISTS trg_update_avg_rating_insert;

DROP TRIGGER IF EXISTS trg_update_avg_rating_update;

DROP TRIGGER IF EXISTS trg_update_avg_rating_delete;

DELIMITER $$

CREATE TRIGGER trg_update_avg_rating_insert
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    UPDATE games
    SET average_rating = (
        SELECT COALESCE(ROUND(AVG(r.rating), 2), 0.00)
        FROM reviews AS r
        WHERE r.game_id = NEW.game_id
    )
    WHERE game_id = NEW.game_id;
END$$

CREATE TRIGGER trg_update_avg_rating_update
AFTER UPDATE ON reviews
FOR EACH ROW
BEGIN
    IF OLD.game_id <> NEW.game_id THEN
        UPDATE games
        SET average_rating = (
            SELECT COALESCE(ROUND(AVG(r.rating), 2), 0.00)
            FROM reviews AS r
            WHERE r.game_id = OLD.game_id
        )
        WHERE game_id = OLD.game_id;
    END IF;

    UPDATE games
    SET average_rating = (
        SELECT COALESCE(ROUND(AVG(r.rating), 2), 0.00)
        FROM reviews AS r
        WHERE r.game_id = NEW.game_id
    )
    WHERE game_id = NEW.game_id;
END$$

CREATE TRIGGER trg_update_avg_rating_delete
AFTER DELETE ON reviews
FOR EACH ROW
BEGIN
    UPDATE games
    SET average_rating = (
        SELECT COALESCE(ROUND(AVG(r.rating), 2), 0.00)
        FROM reviews AS r
        WHERE r.game_id = OLD.game_id
    )
    WHERE game_id = OLD.game_id;
END$$

DELIMITER;

-- ============================================================
-- 2. VIEWS
-- ============================================================
-- SQL SECURITY INVOKER: callers need privileges on underlying tables.
-- Views expose no passwords or account references.
-- Aggregate review statistics before joining other relationships so
-- multiple genres/platforms cannot inflate review counts.

CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_game_catalog AS
SELECT
    g.game_id,
    g.game_name,
    g.description,
    g.thumbnail_url,
    g.publisher_id,
    p.publisher_name,
    g.developer_id,
    d.dev_name AS developer_name,
    g.standard_price,
    g.discount_percent,
    ROUND(
        g.standard_price * (1 - g.discount_percent / 100),
        2
    ) AS current_price,
    g.release_date,
    g.average_rating,
    COALESCE(rs.review_count, 0) AS review_count
FROM
    games AS g
    JOIN publishers AS p ON p.publisher_id = g.publisher_id
    JOIN developers AS d ON d.dev_id = g.developer_id
    LEFT JOIN (
        SELECT game_id, COUNT(*) AS review_count
        FROM reviews
        GROUP BY
            game_id
    ) AS rs ON rs.game_id = g.game_id;

-- One row per qualifying paid order item, NOT one row per payment.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_paid_order_items AS
SELECT o.order_id, o.user_id, o.order_date, o.transaction_id, oi.order_item_id, oi.game_id, g.game_name, oi.price_paid
FROM
    orders AS o
    JOIN payments AS p ON p.transaction_id = o.transaction_id
    JOIN order_items AS oi ON oi.order_id = o.order_id
    JOIN games AS g ON g.game_id = oi.game_id
WHERE
    o.order_status = 'PAID'
    AND p.payment_status = 'SUCCESS';

-- Deduplicate ownership if historical duplicate purchases exist.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_owned_games AS
SELECT
    user_id,
    game_id,
    game_name,
    MIN(order_date) AS first_purchase_date
FROM vw_paid_order_items
GROUP BY
    user_id,
    game_id,
    game_name;

-- One row per order, preserving pending orders without payment.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_order_summary AS
SELECT
    o.order_id,
    o.user_id,
    o.order_date,
    o.order_status,
    o.transaction_id,
    p.payment_status,
    p.amount AS payment_amount,
    COALESCE(i.item_count, 0) AS item_count,
    COALESCE(i.order_total, 0.00) AS order_total
FROM
    orders AS o
    LEFT JOIN payments AS p ON p.transaction_id = o.transaction_id
    LEFT JOIN (
        SELECT
            order_id,
            COUNT(*) AS item_count,
            SUM(price_paid) AS order_total
        FROM order_items
        GROUP BY
            order_id
    ) AS i ON i.order_id = o.order_id;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_game_sales AS
SELECT
    g.game_id,
    g.game_name,
    COUNT(s.order_item_id) AS copies_sold,
    COALESCE(SUM(s.price_paid), 0.00) AS sales_revenue
FROM
    games AS g
    LEFT JOIN vw_paid_order_items AS s ON s.game_id = g.game_id
GROUP BY
    g.game_id,
    g.game_name;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW vw_discounted_wishlist AS
SELECT w.user_id, w.game_id, w.added_at, c.game_name, c.standard_price, c.discount_percent, c.current_price
FROM
    wishlists AS w
    JOIN vw_game_catalog AS c ON c.game_id = w.game_id
WHERE
    c.discount_percent > 0;

-- ============================================================
-- 3. STORED PROCEDURES
-- ============================================================

DROP PROCEDURE IF EXISTS sp_sales_summary;

DROP PROCEDURE IF EXISTS sp_recalculate_average_ratings;

DELIMITER $$

-- Inclusive start, exclusive end: [p_start, p_end).
-- Example: October uses 2026-10-01 through 2026-11-01.
-- Returns one row; dates filter order_date, not payment_time.
CREATE PROCEDURE sp_sales_summary(
    IN p_start DATETIME,
    IN p_end DATETIME
)
SQL SECURITY INVOKER
READS SQL DATA
BEGIN
    IF p_start IS NULL OR p_end IS NULL OR p_start >= p_end THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Provide a start datetime earlier than end datetime';
    END IF;

    SELECT
        COUNT(*) AS paid_orders,
        COUNT(DISTINCT o.user_id) AS paying_customers,
        COALESCE(SUM(p.amount), 0.00) AS payment_revenue
    FROM orders AS o
    JOIN payments AS p ON p.transaction_id = o.transaction_id
    WHERE o.order_status = 'PAID'
      AND p.payment_status = 'SUCCESS'
      AND o.order_date >= p_start
      AND o.order_date < p_end;
END$$

-- Setup/administrative repair only. Run after bulk imports or cascade
-- changes that bypass review triggers. Do not expose a public route.
CREATE PROCEDURE sp_recalculate_average_ratings()
SQL SECURITY INVOKER
MODIFIES SQL DATA
BEGIN
    UPDATE games AS g
    LEFT JOIN (
        SELECT game_id, ROUND(AVG(rating), 2) AS calculated_average
        FROM reviews
        GROUP BY game_id
    ) AS r ON r.game_id = g.game_id
    SET g.average_rating = COALESCE(r.calculated_average, 0.00);
END$$

DELIMITER;

-- Bring existing seeded/imported data into sync.
CALL sp_recalculate_average_ratings ();