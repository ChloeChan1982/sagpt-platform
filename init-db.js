const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const DB_PATH = path.join(__dirname, './data/sagpt.db');

console.log('Creating database at:', DB_PATH);

// 创建数据库连接
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('Database connection error:', err);
    process.exit(1);
  }
  console.log('Database connection established');

  // 初始化数据库表
  initTables(db);
});

async function initTables(db) {
  const tables = `
    -- 用户需求表
    CREATE TABLE IF NOT EXISTS user_requests (
      request_id TEXT PRIMARY KEY,
      target_country TEXT NOT NULL,
      industry TEXT NOT NULL,
      business_goal TEXT NOT NULL CHECK(business_goal IN ('setup', 'investment', 'compliance', 'dispute')),
      budget_range TEXT NOT NULL,
      urgency TEXT NOT NULL CHECK(urgency IN ('low', 'medium', 'high')),
      company_name TEXT NOT NULL,
      contact_person TEXT NOT NULL,
      email TEXT NOT NULL,
      phone TEXT NOT NULL,
      tags TEXT,
      status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'processed', 'failed')),
      matched_providers TEXT,
      explanation TEXT,
      submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      processed_at DATETIME
    );

    -- 服务提供商表
    CREATE TABLE IF NOT EXISTS service_providers (
      provider_id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      country TEXT NOT NULL,
      service_type TEXT NOT NULL CHECK(service_type IN ('legal', 'tax', 'finance', 'marketing')),
      pricing_tier TEXT NOT NULL CHECK(pricing_tier IN ('basic', 'standard', 'premium')),
      rating REAL NOT NULL CHECK(rating BETWEEN 1 AND 5),
      description TEXT,
      contact_email TEXT,
      website TEXT,
      tags TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME
    );

    -- 聊天会话表
    CREATE TABLE IF NOT EXISTS chat_sessions (
      session_id TEXT PRIMARY KEY,
      request_id TEXT,
      started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      ended_at DATETIME,
      FOREIGN KEY (request_id) REFERENCES user_requests (request_id)
    );

    -- 聊天消息表
    CREATE TABLE IF NOT EXISTS chat_messages (
      message_id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
      content TEXT NOT NULL,
      language TEXT NOT NULL CHECK(language IN ('en', 'zh')),
      context_id TEXT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
    );

    -- 合规报告表
    CREATE TABLE IF NOT EXISTS compliance_reports (
      report_id TEXT PRIMARY KEY,
      request_id TEXT,
      country TEXT NOT NULL,
      industry TEXT NOT NULL,
      language TEXT NOT NULL CHECK(language IN ('en', 'zh')),
      content TEXT NOT NULL,
      generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (request_id) REFERENCES user_requests (request_id)
    );

    -- 管理员用户表
    CREATE TABLE IF NOT EXISTS admins (
      admin_id TEXT PRIMARY KEY,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      name TEXT NOT NULL,
      email TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      last_login_at DATETIME
    );
  `;

  const statements = tables.split(';').filter(s => s.trim());

  let completed = 0;
  const total = statements.length;

  for (let i = 0; i < statements.length; i++) {
    const stmt = statements[i].trim() + ';';
    if (stmt) {
      await new Promise((resolve) => {
        db.run(stmt, (err) => {
          if (err) {
            console.error(`Error executing statement ${i+1}:`, err.message);
          } else {
            console.log(`Statement ${i+1} executed successfully`);
          }
          completed++;
          if (completed === total) {
            insertSampleData(db);
          }
          resolve();
        });
      });
    }
  }
}

async function insertSampleData(db) {
  console.log('Checking for existing data...');

  // 检查是否已经有样本数据
  const providerCount = await new Promise((resolve) => {
    db.get('SELECT COUNT(*) as count FROM service_providers', (err, row) => {
      if (err) {
        console.error('Error checking provider count:', err);
        resolve(0);
      } else {
        resolve(row.count);
      }
    });
  });

  if (providerCount === 0) {
    console.log('Inserting sample service providers...');

    const sampleProviders = [
      {
        provider_id: 'prov_1',
        name: 'Global Legal Services Inc.',
        country: 'United States',
        service_type: 'legal',
        pricing_tier: 'premium',
        rating: 4.8,
        description: 'Specialized in e-commerce legal setup and compliance',
        contact_email: 'info@globallegal.com',
        website: 'https://www.globallegal.com',
        tags: JSON.stringify(['e-commerce', 'legal', 'setup'])
      },
      {
        provider_id: 'prov_2',
        name: 'International Tax Advisors',
        country: 'United Kingdom',
        service_type: 'tax',
        pricing_tier: 'standard',
        rating: 4.5,
        description: 'Expert tax planning and compliance for cross-border operations',
        contact_email: 'contact@taxadvisors.com',
        website: 'https://www.taxadvisors.com',
        tags: JSON.stringify(['tax', 'compliance', 'international'])
      },
      {
        provider_id: 'prov_3',
        name: 'Overseas Marketing Solutions',
        country: 'Germany',
        service_type: 'marketing',
        pricing_tier: 'basic',
        rating: 4.2,
        description: 'Localization and digital marketing for international expansion',
        contact_email: 'hello@overseasmarketing.com',
        website: 'https://www.overseasmarketing.com',
        tags: JSON.stringify(['marketing', 'localization', 'digital'])
      }
    ];

    const stmt = `
      INSERT OR IGNORE INTO service_providers
      (provider_id, name, country, service_type, pricing_tier, rating, description, contact_email, website, tags, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const now = new Date().toISOString();

    for (let i = 0; i < sampleProviders.length; i++) {
      const provider = sampleProviders[i];
      await new Promise((resolve) => {
        db.run(stmt, [
          provider.provider_id,
          provider.name,
          provider.country,
          provider.service_type,
          provider.pricing_tier,
          provider.rating,
          provider.description,
          provider.contact_email,
          provider.website,
          provider.tags,
          now,
          now
        ], function(err) {
          if (err) {
            console.error(`Error inserting provider ${i+1}:`, err.message);
          } else {
            console.log(`Provider ${i+1} inserted successfully (${this.changes} row affected)`);
          }
          resolve();
        });
      });
    }
  } else {
    console.log(`Found ${providerCount} existing service providers`);
  }

  // 完成
  console.log('Database initialization complete');
  db.close((err) => {
    if (err) {
      console.error('Error closing database:', err);
    }
    console.log('Database connection closed');
  });
}