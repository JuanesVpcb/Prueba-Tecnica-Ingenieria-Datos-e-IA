INSERT INTO marketing_spend_raw (spend_date, channel, campaign_name, campaign_cost, impressions, clicks)
VALUES
    ('2026-06-01', 'FACEBOOK', 'brand_awareness_q2', 320.50, 45200, 1880),
    ('2026-06-01', 'GOOGLE', 'search_intent_q2', 410.00, 28900, 1742),
    ('2026-06-02', 'FACEBOOK', 'retargeting_week_1', 210.25, 31100, 1320),
    ('2026-06-02', 'INSTAGRAM', 'influencer_boost_week_1', 185.75, 26850, 1204),
    ('2026-06-03', 'GOOGLE', 'search_intent_q2', 430.10, 30120, 1821),
    ('2026-06-03', 'EMAIL', 'newsletter_june_launch', 45.00, 10450, 834),
    ('2026-06-04', 'FACEBOOK', 'lookalike_audience_june', 280.00, 37680, 1495),
    ('2026-06-04', 'INSTAGRAM', 'stories_conversion_june', 199.30, 25500, 1109),
    ('2026-06-05', 'GOOGLE', 'search_brand_protection', 390.60, 27440, 1688),
    ('2026-06-05', 'EMAIL', 'promo_midyear_flash_sale', 60.00, 11820, 915)
ON CONFLICT (spend_date, channel, campaign_name) DO NOTHING;
