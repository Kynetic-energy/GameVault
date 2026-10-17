-- Demo credentials (LOCAL DEVELOPMENT ONLY):
-- admin / AdminDemo@123
-- player_one / PlayerDemo@123
-- player_two / PlayerDemo@123
-- Passwords below are Werkzeug-compatible PBKDF2-SHA256 hashes, never plaintext database values.
-- All companies, games, and payment references below are fictional.

USE gamevault;

START TRANSACTION;

INSERT INTO
    publishers (publisher_id, publisher_name)
VALUES (1, 'Pixel Harbor Publishing'),
    (2, 'Orbit Lantern Games'),
    (3, 'Copperleaf Interactive');

INSERT INTO
    developers (dev_id, dev_name)
VALUES (1, 'Moonforge Studio'),
    (2, 'Neon Trail Labs'),
    (3, 'Willowbyte Studio'),
    (4, 'Clockwork Kite');

INSERT INTO
    users (
        user_id,
        username,
        password_hash,
        email,
        email_verified,
        is_admin,
        affiliate_publisher_id
    )
VALUES (
        1,
        'admin',
        'pbkdf2:sha256:1000000$f147e1f32339ee6a$9fb808be94fd9a921d33daf481ae05bb1db46a2c0f1019d74b9ecb57850328a5',
        'admin@example.com',
        0,
        1,
        NULL
    ),
    (
        2,
        'player_one',
        'pbkdf2:sha256:1000000$087b15318a880d96$53ad1a8bafbd714dd4b255a59432ecef992bc428a2eae634757f3a84720bd151',
        'player.one@example.com',
        0,
        0,
        NULL
    ),
    (
        3,
        'player_two',
        'pbkdf2:sha256:1000000$57674fd2e935f29b$193d3c431c5664c277fcb052dab45610623d1f8d6789522d4c838c0164877610',
        'player.two@example.com',
        0,
        0,
        1
    );

INSERT INTO
    genres (genre_id, genre_name)
VALUES (1, 'Action'),
    (2, 'RPG'),
    (3, 'Racing'),
    (4, 'Puzzle'),
    (5, 'Simulation'),
    (6, 'Strategy'),
    (7, 'Adventure');

INSERT INTO
    platforms (platform_id, platform_name)
VALUES (1, 'Windows'),
    (2, 'Linux'),
    (3, 'macOS');

INSERT INTO
    games (
        game_id,
        game_name,
        description,
        publisher_id,
        developer_id,
        standard_price,
        discount_percent,
        release_date
    )
VALUES (
        1,
        'Emberfall Odyssey',
        'Explore a volcanic kingdom in a story-driven action RPG.',
        1,
        1,
        1499,
        20,
        '2025-03-14'
    ),
    (
        2,
        'Neon Circuit',
        'Race through glowing city circuits and unlock new vehicles.',
        2,
        2,
        999,
        10,
        '2025-06-20'
    ),
    (
        3,
        'Garden of Clouds',
        'Build a peaceful floating garden and trade your harvest.',
        3,
        3,
        799,
        0,
        '2025-09-05'
    ),
    (
        4,
        'Clockwork Riddles',
        'Solve mechanical puzzles inside an abandoned observatory.',
        1,
        4,
        499,
        50,
        '2024-11-15'
    ),
    (
        5,
        'Starbound Tactics',
        'Command a small fleet in turn-based space battles.',
        2,
        1,
        1299,
        25,
        '2025-12-12'
    ),
    (
        6,
        'Lantern Valley',
        'Discover hidden paths in a hand-painted adventure world.',
        3,
        3,
        599,
        0,
        '2026-01-23'
    ),
    (
        7,
        'Arena Sparks',
        'A free action game with short arena challenges.',
        2,
        2,
        0,
        0,
        '2026-02-06'
    ),
    (
        8,
        'Frostline Expedition',
        'Lead an expedition through a frozen wilderness.',
        1,
        4,
        899,
        100,
        '2026-04-10'
    );

INSERT INTO
    game_genres (game_id, genre_id)
VALUES (1, 1),
    (1, 2),
    (1, 7),
    (2, 3),
    (3, 5),
    (4, 4),
    (5, 6),
    (6, 7),
    (7, 1),
    (8, 7),
    (8, 6);

INSERT INTO
    game_platforms (game_id, platform_id)
VALUES (1, 1),
    (1, 2),
    (2, 1),
    (3, 1),
    (3, 2),
    (3, 3),
    (4, 1),
    (4, 2),
    (4, 3),
    (5, 1),
    (5, 2),
    (6, 1),
    (6, 3),
    (7, 1),
    (8, 1),
    (8, 2);

INSERT INTO
    payments (
        transaction_id,
        payee_account_no,
        recipient_account_no,
        payment_time,
        amount,
        payment_status
    )
VALUES (
        1,
        'DEMO-PAYER-002',
        'DEMO-GAMEVAULT',
        '2026-10-15 10:00:00',
        2098.3,
        'SUCCESS'
    ),
    (
        2,
        'DEMO-PAYER-003',
        'DEMO-GAMEVAULT',
        '2026-10-15 11:00:00',
        249.5,
        'SUCCESS'
    ),
    (
        3,
        'DEMO-PAYER-002',
        'DEMO-GAMEVAULT',
        '2026-10-16 09:00:00',
        974.25,
        'FAILED'
    ),
    (
        4,
        'DEMO-PAYER-003',
        'DEMO-GAMEVAULT',
        '2026-10-16 12:00:00',
        799,
        'REFUNDED'
    );

INSERT INTO
    orders (
        order_id,
        user_id,
        order_date,
        order_status,
        transaction_id
    )
VALUES (
        1,
        2,
        '2026-10-15 10:00:00',
        'PAID',
        1
    ),
    (
        2,
        3,
        '2026-10-15 11:00:00',
        'PAID',
        2
    ),
    (
        3,
        2,
        '2026-10-16 09:00:00',
        'CANCELLED',
        3
    ),
    (
        4,
        3,
        '2026-10-16 12:00:00',
        'REFUNDED',
        4
    ),
    (
        5,
        3,
        '2026-10-17 08:00:00',
        'PENDING',
        NULL
    );

INSERT INTO
    order_items (
        order_item_id,
        order_id,
        game_id,
        price_paid
    )
VALUES (1, 1, 1, 1199.2),
    (2, 1, 2, 899.1),
    (3, 2, 4, 249.5),
    (4, 3, 5, 974.25),
    (5, 4, 3, 799),
    (6, 5, 6, 599);

INSERT INTO
    cart_items (
        cart_item_id,
        user_id,
        game_id
    )
VALUES (1, 2, 5),
    (2, 2, 3),
    (3, 3, 6),
    (4, 3, 7);

INSERT INTO
    wishlists (wishlist_id, user_id, game_id)
VALUES (1, 2, 4),
    (2, 2, 5),
    (3, 3, 1),
    (4, 3, 8);

INSERT INTO
    reviews (
        user_id,
        game_id,
        rating,
        review_text
    )
VALUES (
        2,
        1,
        4.5,
        'Enjoyed the exploration and character progression.'
    ),
    (
        2,
        2,
        4.0,
        'Fast races and fun tracks; a few more modes would help.'
    ),
    (
        3,
        4,
        5.0,
        'Creative puzzles and a satisfying difficulty curve.'
    );

-- Reconcile cached averages whether or not review triggers are installed.
-- Keeping this in the seed allows loading schema.sql + seed.sql independently.
UPDATE games AS g
LEFT JOIN (
    SELECT game_id, ROUND(AVG(rating), 2) AS calculated_average
    FROM reviews
    GROUP BY
        game_id
) AS r ON r.game_id = g.game_id
SET
    g.average_rating = COALESCE(r.calculated_average, 0.00);

COMMIT;