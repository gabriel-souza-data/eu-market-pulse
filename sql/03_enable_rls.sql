-- Enable RLS
ALTER TABLE countries ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_kpis ENABLE ROW LEVEL SECURITY;

-- Allow public read-only access (needed for the Streamlit dashboard)
CREATE POLICY "Public read access" ON countries FOR SELECT USING (true);
CREATE POLICY "Public read access" ON market_indicators FOR SELECT USING (true);
CREATE POLICY "Public read access" ON country_kpis FOR SELECT USING (true);