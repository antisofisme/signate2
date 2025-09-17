// K6 Load Testing Script for Anthias SaaS Platform
// Performance testing for staging and production environments

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp-up
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Scale to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(99)<1500'], // 99% of requests must complete below 1.5s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate below 10%
  },
};

// Test configuration from environment
const BASE_URL = __ENV.BASE_URL || 'https://staging.signate.com';
const API_URL = `${BASE_URL}/api/v1`;

// Test data
const testUsers = [
  { email: 'test1@example.com', password: 'testpass123' },
  { email: 'test2@example.com', password: 'testpass123' },
  { email: 'test3@example.com', password: 'testpass123' },
];

// Authentication tokens (store globally)
let authTokens = {};

export function setup() {
  console.log('Setting up load test...');

  // Health check before starting
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Health check failed: ${healthCheck.status}`);
  }

  console.log('Load test setup complete');
  return { baseUrl: BASE_URL, apiUrl: API_URL };
}

export default function(data) {
  const userIndex = __VU % testUsers.length;
  const user = testUsers[userIndex];

  // Test scenarios with weighted distribution
  const scenario = Math.random();

  if (scenario < 0.3) {
    testHomePage(data.baseUrl);
  } else if (scenario < 0.6) {
    testAPI(data.apiUrl, user);
  } else if (scenario < 0.8) {
    testAuthentication(data.apiUrl, user);
  } else {
    testFileUpload(data.apiUrl, user);
  }

  sleep(1 + Math.random() * 2); // Random sleep between 1-3 seconds
}

function testHomePage(baseUrl) {
  const response = http.get(baseUrl);

  const success = check(response, {
    'Homepage loads successfully': (r) => r.status === 200,
    'Homepage response time < 500ms': (r) => r.timings.duration < 500,
    'Homepage contains expected content': (r) => r.body.includes('Anthias'),
  });

  if (!success) {
    errorRate.add(1);
  }
}

function testAPI(apiUrl, user) {
  // Get CSRF token first
  const csrfResponse = http.get(`${apiUrl}/csrf/`);
  let csrfToken = '';

  if (csrfResponse.status === 200) {
    const csrfMatch = csrfResponse.body.match(/csrfToken["']:\s*["']([^"']+)["']/);
    if (csrfMatch) {
      csrfToken = csrfMatch[1];
    }
  }

  // Test various API endpoints
  const endpoints = [
    '/health',
    '/auth/status',
    '/tenants/',
    '/displays/',
  ];

  const headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken,
  };

  // Add auth token if available
  if (authTokens[user.email]) {
    headers['Authorization'] = `Bearer ${authTokens[user.email]}`;
  }

  endpoints.forEach(endpoint => {
    const response = http.get(`${apiUrl}${endpoint}`, { headers });

    const success = check(response, {
      [`API ${endpoint} responds correctly`]: (r) => r.status >= 200 && r.status < 400,
      [`API ${endpoint} response time < 1000ms`]: (r) => r.timings.duration < 1000,
    });

    if (!success) {
      errorRate.add(1);
    }
  });
}

function testAuthentication(apiUrl, user) {
  const loginData = {
    email: user.email,
    password: user.password,
  };

  const response = http.post(`${apiUrl}/auth/login/`, JSON.stringify(loginData), {
    headers: { 'Content-Type': 'application/json' },
  });

  const success = check(response, {
    'Login request processed': (r) => r.status >= 200 && r.status < 500,
    'Login response time < 2000ms': (r) => r.timings.duration < 2000,
  });

  // Store auth token if login successful
  if (response.status === 200) {
    try {
      const responseData = JSON.parse(response.body);
      if (responseData.access_token) {
        authTokens[user.email] = responseData.access_token;
      }
    } catch (e) {
      console.warn('Failed to parse login response');
    }
  }

  if (!success) {
    errorRate.add(1);
  }
}

function testFileUpload(apiUrl, user) {
  if (!authTokens[user.email]) {
    // Skip if not authenticated
    return;
  }

  // Create a small test file
  const testFile = http.file('test-image.jpg', 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==', 'image/jpeg');

  const response = http.post(`${apiUrl}/media/upload/`, {
    file: testFile,
    name: 'Test Upload',
    description: 'Load test file upload',
  }, {
    headers: {
      'Authorization': `Bearer ${authTokens[user.email]}`,
    },
  });

  const success = check(response, {
    'File upload processed': (r) => r.status >= 200 && r.status < 500,
    'Upload response time < 5000ms': (r) => r.timings.duration < 5000,
  });

  if (!success) {
    errorRate.add(1);
  }
}

export function teardown(data) {
  console.log('Cleaning up load test...');

  // Final health check
  const healthCheck = http.get(`${data.baseUrl}/health`);
  console.log(`Final health check status: ${healthCheck.status}`);

  console.log('Load test teardown complete');
}