#!/usr/bin/env node
/**
 * Frontend validation tests
 * Tests that schools.json can be loaded and parsed correctly
 * Run with: node tests/test_frontend.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_DIR = path.join(__dirname, '..', 'frontend');
const SCHOOLS_FILE = path.join(FRONTEND_DIR, 'data', 'schools.json');

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

function test(name, fn) {
    try {
        fn();
        console.log(`✓ ${name}`);
        testsPassed++;
    } catch (error) {
        console.log(`✗ ${name} FAILED:`);
        console.log(`  ${error.message}`);
        testsFailed++;
    }
}

// Load schools data
let schools;
try {
    const data = fs.readFileSync(SCHOOLS_FILE, 'utf8');
    schools = JSON.parse(data);
    console.log(`Loaded ${schools.length} schools from ${SCHOOLS_FILE}\n`);
} catch (error) {
    console.error(`Failed to load schools.json: ${error.message}`);
    process.exit(1);
}

console.log('=' . repeat(80));
console.log('RUNNING FRONTEND VALIDATION TESTS');
console.log('=' . repeat(80));
console.log();

// Tests
test('schools.json is valid array', () => {
    assert(Array.isArray(schools), 'schools should be an array');
    assert(schools.length > 0, 'schools array should not be empty');
});

test('All schools have required fields for map display', () => {
    const requiredFields = ['name', 'type', 'coordinates', 'address'];

    for (const school of schools) {
        for (const field of requiredFields) {
            assert(field in school, `School ${school.name || 'Unknown'} missing ${field}`);
        }

        // Check coordinates structure
        assert('latitude' in school.coordinates, `${school.name} missing latitude`);
        assert('longitude' in school.coordinates, `${school.name} missing longitude`);
        assert(typeof school.coordinates.latitude === 'number', `${school.name} latitude not a number`);
        assert(typeof school.coordinates.longitude === 'number', `${school.name} longitude not a number`);
    }
});

test('School types are valid', () => {
    const validTypes = ['Primaire', 'Collège', 'Lycée'];

    for (const school of schools) {
        assert(
            validTypes.includes(school.type),
            `Invalid school type: ${school.type}`
        );
    }
});

test('Popup content can be generated for all schools', () => {
    // Simulate popup content generation
    for (const school of schools) {
        let errors = [];

        // Required for basic popup
        if (!school.name) errors.push('Missing name');
        if (!school.type) errors.push('Missing type');
        if (!school.address || !school.address.city) errors.push('Missing address.city');

        if (errors.length > 0) {
            throw new Error(`School ${school.uai}: ${errors.join(', ')}`);
        }
    }
});

test('IPS data structure is valid where present', () => {
    const schoolsWithIPS = schools.filter(s => s.ips && s.ips.value);

    assert(schoolsWithIPS.length > 0, 'Should have at least some schools with IPS data');

    let nsCount = 0;
    for (const school of schoolsWithIPS) {
        assert(typeof school.ips.value !== 'undefined', `${school.name} IPS value missing`);
        assert(school.ips.year, `${school.name} IPS missing year`);

        // Handle 'NS' (Non Significatif) values
        const valueStr = String(school.ips.value).toUpperCase();
        if (valueStr === 'NS' || valueStr === 'NON SIGNIFICATIF') {
            nsCount++;
            continue;
        }

        // IPS value should be parseable as number
        const ipsValue = parseFloat(school.ips.value);
        assert(!isNaN(ipsValue), `${school.name} IPS value not a number: ${school.ips.value}`);
        assert(ipsValue >= 30 && ipsValue <= 200, `${school.name} IPS value out of range: ${ipsValue}`);
    }

    console.log(`  Checked ${schoolsWithIPS.length} schools with IPS data (${nsCount} with NS values)`);
});

test('Enrollment data structure is valid where present', () => {
    const schoolsWithEnrollment = schools.filter(s => s.student_count);

    assert(schoolsWithEnrollment.length > 0, 'Should have at least some schools with enrollment');

    for (const school of schoolsWithEnrollment) {
        assert(typeof school.student_count === 'number', `${school.name} student_count not a number`);
        assert(school.student_count > 0, `${school.name} student_count not positive`);
        assert(school.enrollment_year, `${school.name} enrollment missing year`);

        // Check class size for primary schools if they have classes
        if (school.type === 'Primaire' && school.number_of_classes) {
            assert(school.class_size, `${school.name} has classes but no class_size`);

            const expectedClassSize = school.student_count / school.number_of_classes;
            const actualClassSize = school.class_size;
            const diff = Math.abs(expectedClassSize - actualClassSize);

            assert(
                diff < 0.1,
                `${school.name} class_size calculation wrong: expected ${expectedClassSize.toFixed(1)}, got ${actualClassSize}`
            );
        }
    }

    console.log(`  Checked ${schoolsWithEnrollment.length} schools with enrollment data`);
});

test('Exam results structure is valid where present', () => {
    const schoolsWithExams = schools.filter(s => s.exam_results);

    assert(schoolsWithExams.length > 0, 'Should have at least some schools with exam results');

    for (const school of schoolsWithExams) {
        assert(school.exam_results.type, `${school.name} exam_results missing type`);
        assert(school.exam_results.year, `${school.name} exam_results missing year`);

        // Success rate should be reasonable if present
        if (school.exam_results.success_rate) {
            const rate = school.exam_results.success_rate;
            assert(rate >= 0 && rate <= 100, `${school.name} success_rate out of range: ${rate}`);
        }
    }

    console.log(`  Checked ${schoolsWithExams.length} schools with exam results`);
});

test('No duplicate UAI codes', () => {
    const uaiSet = new Set();
    const duplicates = [];

    for (const school of schools) {
        if (uaiSet.has(school.uai)) {
            duplicates.push(school.uai);
        }
        uaiSet.add(school.uai);
    }

    assert(duplicates.length === 0, `Found duplicate UAI codes: ${duplicates.join(', ')}`);
});

test('Marker colors are defined for all school types', () => {
    // These should match the colors in app.js
    const markerColors = {
        'Primaire': '#3b82f6',
        'Collège': '#eab308',
        'Lycée': '#dc2626'
    };

    const schoolTypes = new Set(schools.map(s => s.type));

    for (const type of schoolTypes) {
        assert(type in markerColors, `No marker color defined for type: ${type}`);
    }
});

test('File size is reasonable', () => {
    const stats = fs.statSync(SCHOOLS_FILE);
    const sizeMB = stats.size / (1024 * 1024);

    assert(sizeMB > 1, `File too small: ${sizeMB.toFixed(2)}MB`);
    assert(sizeMB < 10, `File too large: ${sizeMB.toFixed(2)}MB (may slow down loading)`);

    console.log(`  File size: ${sizeMB.toFixed(2)}MB`);
});

test('Language data structure is valid where present', () => {
    const schoolsWithLanguages = schools.filter(s => s.languages);

    assert(schoolsWithLanguages.length > 0, 'Should have at least some schools with language data');

    for (const school of schoolsWithLanguages) {
        assert('lv1' in school.languages, `${school.name} missing languages.lv1`);
        assert('lv2' in school.languages, `${school.name} missing languages.lv2`);
        assert(Array.isArray(school.languages.lv1), `${school.name} lv1 not an array`);
        assert(Array.isArray(school.languages.lv2), `${school.name} lv2 not an array`);

        // Language data should only be for collèges and lycées
        assert(
            school.type === 'Collège' || school.type === 'Lycée',
            `${school.name} has languages but is type ${school.type} (should be Collège or Lycée)`
        );
    }

    console.log(`  Checked ${schoolsWithLanguages.length} schools with language data`);
});

// Summary
console.log();
console.log('=' . repeat(80));
console.log(`RESULTS: ${testsPassed} passed, ${testsFailed} failed`);
console.log('=' . repeat(80));

process.exit(testsFailed === 0 ? 0 : 1);
