// Setup Better Auth database tables
import pg from 'pg';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error('DATABASE_URL environment variable is required');
  process.exit(1);
}

const schema = fs.readFileSync(join(__dirname, 'better-auth-schema.sql'), 'utf-8');

const pool = new pg.Pool({
  connectionString: DATABASE_URL,
});

async function setup() {
  try {
    console.log('Connecting to database...');
    const client = await pool.connect();

    console.log('Running schema migration...');
    await client.query(schema);

    console.log('✓ Better Auth tables created successfully!');

    // Verify tables
    const result = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_name IN ('user', 'session', 'account', 'verification')
    `);

    console.log('\nCreated tables:');
    result.rows.forEach(row => console.log(`  - ${row.table_name}`));

    client.release();
    await pool.end();
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

setup();
