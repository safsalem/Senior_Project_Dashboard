-- Enable UUID generation
DROP TABLE IF EXISTS public.alerts CASCADE;
DROP TABLE IF EXISTS public.sensor_readings CASCADE;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ====================================
-- 1) SENSOR READINGS TABLE
-- ====================================
CREATE TABLE IF NOT EXISTS public.sensor_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reading_time TIMESTAMPTZ NOT NULL UNIQUE,
    temperature NUMERIC(5,2) NOT NULL,
    nox NUMERIC(10,2) NOT NULL,
    co NUMERIC(10,2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_time
ON public.sensor_readings (reading_time DESC);


-- ====================================
-- 2) ALERTS TABLE
-- ====================================
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reading_id UUID REFERENCES public.sensor_readings(id) ON DELETE CASCADE,
    reading_time TIMESTAMPTZ,
    alert_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_type VARCHAR(50) NOT NULL,
    alert_value VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'New',
    message TEXT,
    CONSTRAINT chk_alert_status
        CHECK (status IN ('New', 'Acknowledged', 'Resolved'))
);

CREATE INDEX IF NOT EXISTS idx_alerts_status
ON public.alerts (status);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_time
ON public.alerts (alert_time DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_reading_time
ON public.alerts (reading_time DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_reading_id
ON public.alerts (reading_id);

CREATE INDEX IF NOT EXISTS idx_alerts_type
ON public.alerts (alert_type);


-- ====================================
-- 3) PREVENT DUPLICATE GAS ALERT TYPES
-- ====================================
CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_reading_type
ON public.alerts (reading_id, alert_type)
WHERE reading_id IS NOT NULL;


-- ====================================
-- 4) GAS ALERT TRIGGER FUNCTION
--    Example thresholds:
--    CO High  : co  > 100
--    NOx Spike: nox > 350
-- ====================================
CREATE OR REPLACE FUNCTION public.generate_sensor_alerts()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.co > 300 THEN
        INSERT INTO public.alerts (
            reading_id,
            reading_time,
            alert_time,
            alert_type,
            alert_value,
            status,
            message
        )
        VALUES (
            NEW.id,
            NEW.reading_time,
            NOW(),
            'CO High',
            NEW.co::TEXT || ' ppm',
            'New',
            'CO level exceeded threshold'
        )
        ON CONFLICT DO NOTHING;
    END IF;

    IF NEW.nox > 3703 THEN
        INSERT INTO public.alerts (
            reading_id,
            reading_time,
            alert_time,
            alert_type,
            alert_value,
            status,
            message
        )
        VALUES (
            NEW.id,
            NEW.reading_time,
            NOW(),
            'NOx Spike',
            NEW.nox::TEXT || ' ppm',
            'New',
            'NOx level exceeded threshold'
        )
        ON CONFLICT DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$;


-- ====================================
-- 5) AUTO-RESOLVE UPLOAD DELAY ALERT
-- ====================================
CREATE OR REPLACE FUNCTION public.resolve_upload_delay_on_new_reading()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.alerts
    SET
        status = 'Resolved',
        message = 'Upload resumed and new sensor data was received'
    WHERE alert_type = 'Upload Delay'
      AND status IN ('New', 'Acknowledged');

    RETURN NEW;
END;
$$;


-- ====================================
-- 6) TRIGGERS ON SENSOR READINGS
-- ====================================
DROP TRIGGER IF EXISTS trg_generate_sensor_alerts ON public.sensor_readings;
CREATE TRIGGER trg_generate_sensor_alerts
AFTER INSERT ON public.sensor_readings
FOR EACH ROW
EXECUTE FUNCTION public.generate_sensor_alerts();

DROP TRIGGER IF EXISTS trg_resolve_upload_delay ON public.sensor_readings;
CREATE TRIGGER trg_resolve_upload_delay
AFTER INSERT ON public.sensor_readings
FOR EACH ROW
EXECUTE FUNCTION public.resolve_upload_delay_on_new_reading();


-- ====================================
-- 7) FUNCTION TO CHECK UPLOAD DELAY
--    Arduino sends every 1 second
--    Delay threshold set to 3 seconds
-- ====================================
CREATE OR REPLACE FUNCTION public.check_upload_delay()
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    latest_reading_id UUID;
    latest_reading_time TIMESTAMPTZ;
    delay_threshold INTERVAL := INTERVAL '3 seconds';
BEGIN
    SELECT id, reading_time
    INTO latest_reading_id, latest_reading_time
    FROM public.sensor_readings
    ORDER BY reading_time DESC
    LIMIT 1;

    IF latest_reading_time IS NULL THEN
        RETURN;
    END IF;

    IF latest_reading_time < NOW() - delay_threshold THEN
        INSERT INTO public.alerts (
            reading_id,
            reading_time,
            alert_time,
            alert_type,
            alert_value,
            status,
            message
        )
        SELECT
            latest_reading_id,
            latest_reading_time,
            NOW(),
            'Upload Delay',
            EXTRACT(EPOCH FROM (NOW() - latest_reading_time))::INT || ' seconds',
            'New',
            'No sensor data received within the allowed 3-second window'
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.alerts a
            WHERE a.alert_type = 'Upload Delay'
              AND a.status IN ('New', 'Acknowledged')
        );
    END IF;
END;
$$;


-- ====================================
-- 8) SAMPLE TEST DATA
-- ====================================
INSERT INTO public.sensor_readings (reading_time, temperature, nox, co)
VALUES
    (NOW() - INTERVAL '2 seconds', 26.10, 310.00, 95.00),
    (NOW() - INTERVAL '1 second', 26.30, 360.00, 101.00),
    (NOW(), 26.40, 329.00, 106.00)
ON CONFLICT (reading_time) DO NOTHING;


INSERT INTO public.sensor_readings (reading_time, temperature, nox, co)
VALUES
    (NOW() - INTERVAL '5 seconds', 26.10, 310.00, 95.00),
    (NOW() - INTERVAL '8 second', 26.30, 360.00, 101.00)
ON CONFLICT (reading_time) DO NOTHING;

-- ====================================
-- 9) RUN THIS ON A SCHEDULE
-- ====================================
-- Call this every 1 second or 2 seconds from your backend / pgAgent:
-- SELECT public.check_upload_delay();


-- ====================================
-- 10) USEFUL QUERIES
-- ====================================

-- Latest sensor readings
-- SELECT *
-- FROM public.sensor_readings
-- ORDER BY reading_time DESC;

-- All alerts
-- SELECT *
-- FROM public.alerts
-- ORDER BY alert_time DESC;

-- New alerts only
-- SELECT *
-- FROM public.alerts
-- WHERE status = 'New'
-- ORDER BY alert_time DESC;

-- Alerts joined with readings
-- SELECT
--     a.id AS alert_id,
--     a.alert_type,
--     a.alert_value,
--     a.status,
--     a.reading_time,
--     a.alert_time,
--     s.temperature,
--     s.nox,
--     s.co
-- FROM public.alerts a
-- LEFT JOIN public.sensor_readings s
--     ON a.reading_id = s.id
-- ORDER BY a.alert_time DESC;

