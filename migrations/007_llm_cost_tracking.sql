-- Migration: Create LLM Cost Tracking Tables
-- Description: Implements comprehensive cost tracking for Agent Cortex Claude API usage
-- Author: BoarderframeOS Team
-- Date: 2025-06-17

-- Main cost tracking table for every LLM request
CREATE TABLE IF NOT EXISTS llm_cost_tracking (
    tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    input_cost DECIMAL(10, 6) NOT NULL,
    output_cost DECIMAL(10, 6) NOT NULL,
    total_cost DECIMAL(10, 6) NOT NULL,
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_latency_ms INTEGER,
    strategy_used VARCHAR(50),
    task_type VARCHAR(100),
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10),
    quality_score DECIMAL(3, 2) CHECK (quality_score BETWEEN 0 AND 1),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for efficient querying
CREATE INDEX idx_llm_cost_agent_timestamp ON llm_cost_tracking(agent_name, request_timestamp DESC);
CREATE INDEX idx_llm_cost_model ON llm_cost_tracking(model_used);
CREATE INDEX idx_llm_cost_timestamp ON llm_cost_tracking(request_timestamp DESC);

-- Daily aggregated summary table
CREATE TABLE IF NOT EXISTS llm_cost_summary (
    summary_date DATE NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    successful_requests INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0,
    total_input_tokens INTEGER NOT NULL DEFAULT 0,
    total_output_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    avg_latency_ms INTEGER,
    min_latency_ms INTEGER,
    max_latency_ms INTEGER,
    models_used JSONB DEFAULT '{}'::jsonb,
    strategies_used JSONB DEFAULT '{}'::jsonb,
    hourly_distribution JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (summary_date, agent_name)
);

-- Index for efficient date range queries
CREATE INDEX idx_llm_summary_date ON llm_cost_summary(summary_date DESC);

-- Budget tracking and control table
CREATE TABLE IF NOT EXISTS llm_budget_tracking (
    agent_name VARCHAR(100) PRIMARY KEY,
    agent_tier VARCHAR(50) NOT NULL DEFAULT 'worker',
    daily_budget DECIMAL(10, 2) NOT NULL DEFAULT 10.00,
    monthly_budget DECIMAL(10, 2) NOT NULL DEFAULT 300.00,
    current_daily_spend DECIMAL(10, 6) NOT NULL DEFAULT 0,
    current_monthly_spend DECIMAL(10, 6) NOT NULL DEFAULT 0,
    daily_request_limit INTEGER DEFAULT 1000,
    current_daily_requests INTEGER NOT NULL DEFAULT 0,
    budget_warnings INTEGER DEFAULT 0,
    last_warning_at TIMESTAMP WITH TIME ZONE,
    throttle_enabled BOOLEAN DEFAULT FALSE,
    throttle_start_at TIMESTAMP WITH TIME ZONE,
    throttle_strategy VARCHAR(50) DEFAULT 'downgrade_model',
    override_config JSONB DEFAULT '{}'::jsonb,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Model performance tracking for optimization
CREATE TABLE IF NOT EXISTS llm_model_performance (
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    evaluation_date DATE NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    avg_quality_score DECIMAL(3, 2),
    avg_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    p99_latency_ms INTEGER,
    error_rate DECIMAL(5, 4) DEFAULT 0,
    avg_input_tokens INTEGER,
    avg_output_tokens INTEGER,
    total_cost DECIMAL(10, 6) DEFAULT 0,
    cost_per_quality_point DECIMAL(10, 6),
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (model_name, provider, evaluation_date)
);

-- Create function to update daily summary
CREATE OR REPLACE FUNCTION update_llm_cost_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert summary record
    INSERT INTO llm_cost_summary (
        summary_date,
        agent_name,
        total_requests,
        successful_requests,
        failed_requests,
        total_input_tokens,
        total_output_tokens,
        total_cost,
        avg_latency_ms,
        min_latency_ms,
        max_latency_ms
    )
    VALUES (
        DATE(NEW.request_timestamp),
        NEW.agent_name,
        1,
        CASE WHEN NEW.success THEN 1 ELSE 0 END,
        CASE WHEN NOT NEW.success THEN 1 ELSE 0 END,
        NEW.input_tokens,
        NEW.output_tokens,
        NEW.total_cost,
        NEW.response_latency_ms,
        NEW.response_latency_ms,
        NEW.response_latency_ms
    )
    ON CONFLICT (summary_date, agent_name) DO UPDATE
    SET
        total_requests = llm_cost_summary.total_requests + 1,
        successful_requests = llm_cost_summary.successful_requests + CASE WHEN NEW.success THEN 1 ELSE 0 END,
        failed_requests = llm_cost_summary.failed_requests + CASE WHEN NOT NEW.success THEN 1 ELSE 0 END,
        total_input_tokens = llm_cost_summary.total_input_tokens + NEW.input_tokens,
        total_output_tokens = llm_cost_summary.total_output_tokens + NEW.output_tokens,
        total_cost = llm_cost_summary.total_cost + NEW.total_cost,
        avg_latency_ms = (llm_cost_summary.avg_latency_ms * llm_cost_summary.total_requests + NEW.response_latency_ms) / (llm_cost_summary.total_requests + 1),
        min_latency_ms = LEAST(llm_cost_summary.min_latency_ms, NEW.response_latency_ms),
        max_latency_ms = GREATEST(llm_cost_summary.max_latency_ms, NEW.response_latency_ms),
        updated_at = CURRENT_TIMESTAMP;

    -- Update budget tracking
    UPDATE llm_budget_tracking
    SET
        current_daily_spend = current_daily_spend + NEW.total_cost,
        current_daily_requests = current_daily_requests + 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE agent_name = NEW.agent_name;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic summary updates
CREATE TRIGGER update_summary_on_tracking
AFTER INSERT ON llm_cost_tracking
FOR EACH ROW
EXECUTE FUNCTION update_llm_cost_summary();

-- Function to reset daily budgets (call via cron job)
CREATE OR REPLACE FUNCTION reset_daily_budgets()
RETURNS void AS $$
BEGIN
    UPDATE llm_budget_tracking
    SET
        current_daily_spend = 0,
        current_daily_requests = 0,
        budget_warnings = 0,
        throttle_enabled = FALSE,
        throttle_start_at = NULL,
        last_updated = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function to check and enforce budget limits
CREATE OR REPLACE FUNCTION check_budget_limit(p_agent_name VARCHAR)
RETURNS TABLE(
    allowed BOOLEAN,
    reason TEXT,
    recommended_action TEXT
) AS $$
DECLARE
    v_budget RECORD;
BEGIN
    SELECT * INTO v_budget
    FROM llm_budget_tracking
    WHERE agent_name = p_agent_name;

    -- Check daily spend limit
    IF v_budget.current_daily_spend >= v_budget.daily_budget THEN
        RETURN QUERY
        SELECT
            FALSE,
            'Daily budget exceeded',
            'Switch to budget model or wait until tomorrow';

    -- Check if approaching limit (80%)
    ELSIF v_budget.current_daily_spend >= v_budget.daily_budget * 0.8 THEN
        RETURN QUERY
        SELECT
            TRUE,
            'Approaching daily budget limit',
            'Consider using cost-optimized strategy';

    -- Check request limit
    ELSIF v_budget.current_daily_requests >= v_budget.daily_request_limit THEN
        RETURN QUERY
        SELECT
            FALSE,
            'Daily request limit exceeded',
            'Batch requests or wait until tomorrow';

    ELSE
        RETURN QUERY
        SELECT
            TRUE,
            'Within budget limits',
            'Continue normal operation';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create view for easy cost analysis
CREATE OR REPLACE VIEW llm_cost_analysis AS
SELECT
    DATE_TRUNC('day', request_timestamp) as day,
    agent_name,
    model_used,
    COUNT(*) as request_count,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(total_cost) as total_cost,
    AVG(response_latency_ms) as avg_latency_ms,
    AVG(quality_score) as avg_quality,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM llm_cost_tracking
GROUP BY DATE_TRUNC('day', request_timestamp), agent_name, model_used
ORDER BY day DESC, total_cost DESC;

-- Insert default budget limits for known agent tiers
INSERT INTO llm_budget_tracking (agent_name, agent_tier, daily_budget, monthly_budget, daily_request_limit)
VALUES
    ('solomon', 'executive', 50.00, 1500.00, 500),
    ('david', 'executive', 50.00, 1500.00, 500),
    ('department_head', 'department', 20.00, 600.00, 1000),
    ('specialist_agent', 'specialist', 10.00, 300.00, 2000),
    ('worker_bot', 'worker', 5.00, 150.00, 5000)
ON CONFLICT (agent_name) DO NOTHING;

-- Add comment descriptions
COMMENT ON TABLE llm_cost_tracking IS 'Detailed tracking of every LLM API call with cost breakdown';
COMMENT ON TABLE llm_cost_summary IS 'Daily aggregated summaries for reporting and analysis';
COMMENT ON TABLE llm_budget_tracking IS 'Budget limits and throttling controls per agent';
COMMENT ON TABLE llm_model_performance IS 'Model performance metrics for optimization decisions';
COMMENT ON VIEW llm_cost_analysis IS 'Convenient view for cost analysis queries';
