SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'hospital%' ORDER BY 1;
